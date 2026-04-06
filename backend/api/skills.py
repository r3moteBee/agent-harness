"""Skills API — list, enable/disable, reload, scan, and inspect skills."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import get_settings
from skills.registry import get_skill_registry, reload_skill_registry

logger = logging.getLogger(__name__)
router = APIRouter()


class SkillToggleRequest(BaseModel):
    project_id: str
    enabled: bool


# ── List all skills ──────────────────────────────────────────────────────────

@router.get("/skills")
async def list_skills(
    project_id: str = Query(default=None, description="Filter skills available for this project"),
) -> dict[str, Any]:
    """List all registered skills, optionally filtered by project."""
    registry = get_skill_registry()

    if project_id:
        skills = registry.list_for_project(project_id)
    else:
        skills = registry.list_all()

    return {
        "skills": [s.to_summary() for s in skills],
        "count": len(skills),
    }


# ── Get a single skill ──────────────────────────────────────────────────────

@router.get("/skills/{skill_name}")
async def get_skill(skill_name: str) -> dict[str, Any]:
    """Get full details for a skill including instructions."""
    registry = get_skill_registry()
    skill = registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    summary = skill.to_summary()
    summary["instructions"] = skill.instructions
    summary["skill_dir"] = skill.skill_dir
    summary["parameters"] = [p.model_dump() for p in skill.manifest.parameters]
    summary["capabilities_required"] = skill.manifest.capabilities_required
    summary["pantheon"] = skill.manifest.pantheon.model_dump()
    return summary


# ── Enable / disable a skill for a project ───────────────────────────────────

@router.put("/skills/{skill_name}/toggle")
async def toggle_skill(skill_name: str, req: SkillToggleRequest) -> dict[str, Any]:
    """Enable or disable a skill for a specific project."""
    registry = get_skill_registry()
    skill = registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    if req.enabled:
        registry.enable_for_project(skill_name, req.project_id)
    else:
        registry.disable_for_project(skill_name, req.project_id)

    return {
        "skill": skill_name,
        "project_id": req.project_id,
        "enabled": req.enabled,
    }


# ── Delete a skill ──────────────────────────────────────────────────────────

@router.delete("/skills/{skill_name}")
async def delete_skill(skill_name: str) -> dict[str, Any]:
    """Delete a skill from the registry and (for user-installed) from disk.

    Bundled skills are removed from the registry but preserved on disk.
    Reloading the registry will restore them.
    """
    registry = get_skill_registry()
    skill = registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    result = registry.delete(skill_name)
    if not result.get("deleted"):
        raise HTTPException(status_code=500, detail=result.get("error", "Delete failed"))

    logger.info("Deleted skill '%s': %s", skill_name, result)
    return {"skill": skill_name, **result}


# ── Reload the skill registry ───────────────────────────────────────────────

@router.post("/skills/reload")
async def reload_skills() -> dict[str, Any]:
    """Force-reload all skills from disk."""
    registry = reload_skill_registry()
    return {
        "status": "reloaded",
        "count": len(registry.list_all()),
        "skills": registry.names(),
    }


# ── Get skill discovery setting for a project ───────────────────────────────

@router.get("/skills/discovery/{project_id}")
async def get_skill_discovery(project_id: str) -> dict[str, str]:
    """Get the skill discovery mode for a project."""
    from secrets.vault import get_vault
    vault = get_vault()
    mode = vault.get_secret(f"skill_discovery_{project_id}") or "off"
    return {"project_id": project_id, "skill_discovery": mode}


@router.put("/skills/discovery/{project_id}")
async def set_skill_discovery(project_id: str, mode: str = Query(...)) -> dict[str, str]:
    """Set the skill discovery mode for a project (off / suggest / auto)."""
    if mode not in ("off", "suggest", "auto"):
        raise HTTPException(status_code=400, detail="Mode must be 'off', 'suggest', or 'auto'")
    from secrets.vault import get_vault
    vault = get_vault()
    vault.set_secret(f"skill_discovery_{project_id}", mode)
    logger.info("Skill discovery for project '%s' set to '%s'", project_id, mode)
    return {"project_id": project_id, "skill_discovery": mode}


# ── Security scanning ──────────────────────────────────────────────────────

@router.post("/skills/{skill_name}/scan")
async def scan_skill_endpoint(
    skill_name: str,
    ai_review: bool = Query(default=True, description="Run AI review (Layer 3) — slower but deeper"),
) -> dict[str, Any]:
    """Run the security scanner on a skill and store the result."""
    from skills.scanner import scan_skill

    registry = get_skill_registry()
    skill = registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    skill_dir = Path(skill.skill_dir)
    result = await scan_skill(
        skill_dir=skill_dir,
        manifest=skill.manifest,
        instructions=skill.instructions,
        run_ai_review=ai_review,
    )

    # Persist the scan result on the manifest
    skill.manifest.security_scan = result

    # If the scan failed, move to quarantine
    if not result.passed:
        quarantine_result = _quarantine_skill(skill_name, reason="scan_failed")
        return {
            "skill": skill_name,
            "scan": result.model_dump(),
            "quarantined": quarantine_result.get("quarantined", False),
        }

    return {
        "skill": skill_name,
        "scan": result.model_dump(),
        "quarantined": False,
    }


@router.get("/skills/{skill_name}/scan")
async def get_scan_result(skill_name: str) -> dict[str, Any]:
    """Get the most recent scan result for a skill."""
    registry = get_skill_registry()
    skill = registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    if not skill.manifest.security_scan:
        return {"skill": skill_name, "scan": None, "message": "No scan has been run yet"}

    return {
        "skill": skill_name,
        "scan": skill.manifest.security_scan.model_dump(),
    }


# ── Quarantine ─────────────────────────────────────────────────────────────

def _quarantine_skill(skill_name: str, reason: str = "") -> dict[str, Any]:
    """Move a user-installed skill to the quarantine directory.

    Bundled skills cannot be quarantined (they live in the repo); instead
    they are disabled for all projects.
    """
    settings = get_settings()
    registry = get_skill_registry()
    skill = registry.get(skill_name)
    if not skill:
        return {"quarantined": False, "error": "not_found"}

    if skill.is_bundled:
        # Can't move bundled skills — just log a warning
        logger.warning(
            "Bundled skill '%s' failed scan (reason: %s) — cannot quarantine, flagging only",
            skill_name, reason,
        )
        return {
            "quarantined": False,
            "bundled": True,
            "message": "Bundled skill flagged but not quarantined (files are in the repo)",
        }

    # Move user-installed skill to quarantine
    skill_dir = Path(skill.skill_dir)
    quarantine_dir = settings.data_dir / "skills" / ".quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    dest = quarantine_dir / skill_name

    try:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(skill_dir), str(dest))

        # Remove from registry
        registry.delete(skill_name)

        logger.info("Quarantined skill '%s' → %s (reason: %s)", skill_name, dest, reason)
        return {"quarantined": True, "path": str(dest), "reason": reason}
    except Exception as e:
        logger.error("Failed to quarantine '%s': %s", skill_name, e)
        return {"quarantined": False, "error": str(e)}


@router.post("/skills/{skill_name}/quarantine")
async def quarantine_skill_endpoint(skill_name: str) -> dict[str, Any]:
    """Manually quarantine a skill."""
    result = _quarantine_skill(skill_name, reason="manual")
    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    return {"skill": skill_name, **result}


@router.get("/skills/quarantine/list")
async def list_quarantined() -> dict[str, Any]:
    """List skills in the quarantine directory."""
    settings = get_settings()
    quarantine_dir = settings.data_dir / "skills" / ".quarantine"
    if not quarantine_dir.is_dir():
        return {"quarantined": [], "count": 0}

    quarantined = []
    for d in sorted(quarantine_dir.iterdir()):
        if d.is_dir():
            manifest_path = d / "skill.json"
            info: dict[str, Any] = {"name": d.name, "path": str(d)}
            if manifest_path.exists():
                try:
                    import json
                    raw = json.loads(manifest_path.read_text())
                    info["description"] = raw.get("description", "")
                    info["version"] = raw.get("version", "")
                except Exception:
                    pass
            quarantined.append(info)

    return {"quarantined": quarantined, "count": len(quarantined)}


@router.post("/skills/{skill_name}/unquarantine")
async def unquarantine_skill(skill_name: str) -> dict[str, Any]:
    """Restore a skill from quarantine back to user-installed skills."""
    settings = get_settings()
    quarantine_dir = settings.data_dir / "skills" / ".quarantine"
    quarantined_path = quarantine_dir / skill_name

    if not quarantined_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not in quarantine")

    user_skills_dir = settings.data_dir / "skills"
    dest = user_skills_dir / skill_name
    if dest.exists():
        raise HTTPException(
            status_code=409,
            detail=f"A skill named '{skill_name}' already exists — remove it first",
        )

    try:
        shutil.move(str(quarantined_path), str(dest))
        # Reload registry to pick up the restored skill
        reload_skill_registry()
        logger.info("Restored skill '%s' from quarantine", skill_name)
        return {"skill": skill_name, "restored": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore: {e}")
