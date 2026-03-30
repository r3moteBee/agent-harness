"""System prompt assembly for the agent."""
from __future__ import annotations
import logging
from datetime import datetime, timezone

from agent.personality import get_full_personality

logger = logging.getLogger(__name__)


def build_system_prompt(
    project_id: str | None = None,
    project_name: str | None = None,
    recalled_memories: list[dict] | None = None,
    extra_context: str | None = None,
) -> str:
    """Assemble the full system prompt from all sources."""
    personality = get_full_personality(project_id)
    soul = personality["soul"]
    agent_config = personality["agent"]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    project_section = ""
    if project_id and project_name:
        project_section = f"\n\n## Active Project\nYou are currently working in project: **{project_name}** (id: {project_id})\nAll memories, files, and context are scoped to this project."
    elif project_id:
        project_section = f"\n\n## Active Project\nProject ID: {project_id}"

    memory_section = ""
    if recalled_memories:
        memory_lines = []
        for m in recalled_memories:
            source = m.get("source", "memory")
            content = m.get("content", "")
            if content:
                memory_lines.append(f"[{source}] {content}")
        if memory_lines:
            memory_section = "\n\n## Recalled Context\nRelevant information from your memory:\n" + "\n\n".join(memory_lines)

    extra_section = f"\n\n## Additional Context\n{extra_context}" if extra_context else ""

    return f"""{soul}

---

{agent_config}{project_section}{memory_section}{extra_section}

---

Current time: {now}"""
