"""Skills API — list, enable/disable, reload, and inspect skills."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

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
