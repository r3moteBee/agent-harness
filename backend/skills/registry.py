"""Skill registry — discovers, loads, and indexes skills from disk.

Skills live in two locations:
  - Bundled:  <repo>/skills/          (shipped with Pantheon)
  - User:     <data>/skills/          (user-installed)

Each skill is a directory containing at minimum a `skill.json` manifest.
An optional `instructions.md` provides the detailed procedure injected
into the system prompt when the skill is active.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from config import get_settings
from skills.models import LoadedSkill, SkillManifest, ProjectSkillSettings

logger = logging.getLogger(__name__)
settings = get_settings()

# Bundled skills live alongside the backend source
_BUNDLED_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"

# User-installed skills live inside the data directory
_USER_SKILLS_DIR = settings.data_dir / "skills"


class SkillRegistry:
    """In-memory registry of all available skills."""

    def __init__(self) -> None:
        self._skills: dict[str, LoadedSkill] = {}
        self._loaded = False

    def load(self) -> None:
        """(Re)load all skills from both directories."""
        self._skills.clear()
        loaded = 0

        # Load bundled skills first
        if _BUNDLED_SKILLS_DIR.is_dir():
            for skill_dir in sorted(_BUNDLED_SKILLS_DIR.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "skill.json").exists():
                    skill = self._load_skill(skill_dir, is_bundled=True)
                    if skill:
                        self._skills[skill.name] = skill
                        loaded += 1

        # Load user-installed skills (override bundled if same name)
        _USER_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        if _USER_SKILLS_DIR.is_dir():
            for skill_dir in sorted(_USER_SKILLS_DIR.iterdir()):
                if skill_dir.is_dir() and (skill_dir / "skill.json").exists():
                    skill = self._load_skill(skill_dir, is_bundled=False)
                    if skill:
                        if skill.name in self._skills:
                            logger.info(
                                "User skill '%s' overrides bundled version",
                                skill.name,
                            )
                        self._skills[skill.name] = skill
                        loaded += 1

        self._loaded = True
        logger.info("Skill registry loaded: %d skills", loaded)

    def _load_skill(self, skill_dir: Path, is_bundled: bool) -> LoadedSkill | None:
        """Load a single skill from a directory."""
        manifest_path = skill_dir / "skill.json"
        instructions_path = skill_dir / "instructions.md"

        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest = SkillManifest(**raw)
        except Exception as e:
            logger.warning("Failed to load skill from %s: %s", skill_dir, e)
            return None

        instructions = ""
        if instructions_path.exists():
            try:
                instructions = instructions_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to read instructions for %s: %s", skill_dir.name, e)

        # Load per-project enable/disable state
        enabled_projects = self._load_enabled_projects(manifest.name)

        return LoadedSkill(
            manifest=manifest,
            instructions=instructions,
            skill_dir=str(skill_dir),
            is_bundled=is_bundled,
            enabled_projects=enabled_projects,
        )

    def _load_enabled_projects(self, skill_name: str) -> list[str]:
        """Load which projects have this skill enabled.

        For Phase 1, all skills are enabled for all projects by default.
        Per-project state will be stored in a lightweight JSON sidecar
        once the project settings API is extended.
        """
        state_file = _USER_SKILLS_DIR / ".skill_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                return state.get(skill_name, {}).get("enabled_projects", [])
            except Exception:
                pass
        return []

    def _save_skill_state(self) -> None:
        """Persist per-skill state (enabled projects) to disk."""
        state: dict[str, Any] = {}
        for name, skill in self._skills.items():
            state[name] = {
                "enabled_projects": skill.enabled_projects,
            }
        state_file = _USER_SKILLS_DIR / ".skill_state.json"
        _USER_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    # ── Public API ──────────────────────────────────────────────────────

    def ensure_loaded(self) -> None:
        """Load skills if not already loaded."""
        if not self._loaded:
            self.load()

    def get(self, name: str) -> LoadedSkill | None:
        """Get a skill by name."""
        self.ensure_loaded()
        return self._skills.get(name)

    def list_all(self) -> list[LoadedSkill]:
        """List all registered skills."""
        self.ensure_loaded()
        return list(self._skills.values())

    def list_for_project(self, project_id: str) -> list[LoadedSkill]:
        """List skills available for a project.

        Phase 1 logic: A skill is available if it has no enabled_projects
        list (globally available) or the project is in the list.
        """
        self.ensure_loaded()
        results = []
        for skill in self._skills.values():
            if not skill.enabled_projects or project_id in skill.enabled_projects:
                results.append(skill)
        return results

    def enable_for_project(self, skill_name: str, project_id: str) -> bool:
        """Enable a skill for a specific project."""
        self.ensure_loaded()
        skill = self._skills.get(skill_name)
        if not skill:
            return False
        if project_id not in skill.enabled_projects:
            skill.enabled_projects.append(project_id)
        self._save_skill_state()
        return True

    def disable_for_project(self, skill_name: str, project_id: str) -> bool:
        """Disable a skill for a specific project."""
        self.ensure_loaded()
        skill = self._skills.get(skill_name)
        if not skill:
            return False
        if project_id in skill.enabled_projects:
            skill.enabled_projects.remove(project_id)
        self._save_skill_state()
        return True

    def names(self) -> list[str]:
        """Get all skill names."""
        self.ensure_loaded()
        return list(self._skills.keys())


# ── Singleton ────────────────────────────────────────────────────────────────

_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry singleton."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _registry.load()
    return _registry


def reload_skill_registry() -> SkillRegistry:
    """Force-reload the skill registry."""
    global _registry
    _registry = SkillRegistry()
    _registry.load()
    return _registry
