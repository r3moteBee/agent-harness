"""Load and manage agent personality files (soul.md, agent.md)."""
from __future__ import annotations
import logging
from pathlib import Path

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def load_soul() -> str:
    """Load the global soul.md personality file."""
    soul_path = settings.personality_dir / "soul.md"
    if soul_path.exists():
        return soul_path.read_text(encoding="utf-8")
    logger.warning("soul.md not found, using minimal default")
    return "You are a helpful, curious, and honest AI assistant."


def load_agent_config() -> str:
    """Load the global agent.md configuration file."""
    agent_path = settings.personality_dir / "agent.md"
    if agent_path.exists():
        return agent_path.read_text(encoding="utf-8")
    logger.warning("agent.md not found, using minimal default")
    return "Use your tools and memory to assist the user effectively."


def load_project_personality(project_id: str) -> dict[str, str]:
    """Load per-project personality overrides if they exist."""
    project_dir = settings.projects_dir / project_id / "personality"
    result: dict[str, str] = {}
    for fname in ["soul.md", "agent.md"]:
        fpath = project_dir / fname
        if fpath.exists():
            result[fname] = fpath.read_text(encoding="utf-8")
    return result


def get_full_personality(project_id: str | None = None) -> dict[str, str]:
    """Return merged personality for a given project (project overrides global)."""
    soul = load_soul()
    agent = load_agent_config()
    if project_id:
        overrides = load_project_personality(project_id)
        soul = overrides.get("soul.md", soul)
        agent = overrides.get("agent.md", agent)
    return {"soul": soul, "agent": agent}


def save_soul(content: str, project_id: str | None = None) -> None:
    """Save soul.md globally or for a specific project."""
    if project_id:
        path = settings.projects_dir / project_id / "personality" / "soul.md"
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path = settings.personality_dir / "soul.md"
    path.write_text(content, encoding="utf-8")


def save_agent_config(content: str, project_id: str | None = None) -> None:
    """Save agent.md globally or for a specific project."""
    if project_id:
        path = settings.projects_dir / project_id / "personality" / "agent.md"
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        path = settings.personality_dir / "agent.md"
    path.write_text(content, encoding="utf-8")
