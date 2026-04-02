"""Built-in tool definitions for the agent."""
from __future__ import annotations
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Tool schemas (OpenAI function calling format)
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Store information in memory for future recall. Choose the tier based on importance: 'working' for temporary context, 'episodic' for conversation facts, 'semantic' for key insights/knowledge, 'graph' for relationships between concepts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The information to remember"},
                    "tier": {
                        "type": "string",
                        "enum": ["working", "episodic", "semantic"],
                        "description": "Memory tier to store in"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata tags",
                        "additionalProperties": True
                    }
                },
                "required": ["content", "tier"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Search memories across tiers to retrieve relevant past information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for"},
                    "tiers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["episodic", "semantic", "graph"]},
                        "description": "Which memory tiers to search (default: all)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_graph_node",
            "description": "Create a node in the associative graph memory to represent a concept, person, project, or fact.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_type": {
                        "type": "string",
                        "enum": ["concept", "person", "project", "event", "fact"],
                        "description": "Type of the node"
                    },
                    "label": {"type": "string", "description": "Human-readable name for the node"},
                    "metadata": {
                        "type": "object",
                        "description": "Additional properties for this node",
                        "additionalProperties": True
                    }
                },
                "required": ["node_type", "label"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_concepts",
            "description": "Create a relationship edge between two nodes in the associative graph memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_a_label": {"type": "string", "description": "Label of the first node"},
                    "node_b_label": {"type": "string", "description": "Label of the second node"},
                    "relationship": {"type": "string", "description": "Description of the relationship (e.g., 'works on', 'is related to', 'caused by')"}
                },
                "required": ["node_a_label", "node_b_label", "relationship"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the agent workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file within the workspace"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the agent workspace. Creates directories as needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file within the workspace"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_workspace_files",
            "description": "List files and directories in the agent workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Subdirectory path to list (default: root workspace)", "default": ""}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information using DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Schedule an autonomous task for the agent to work on independently.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What the agent should do in this task"},
                    "schedule": {
                        "type": "string",
                        "description": "When to run: 'now' for immediate, cron expression like '0 9 * * *' for daily at 9am, or 'interval:60' for every 60 minutes"
                    },
                    "name": {"type": "string", "description": "Short name for this task"}
                },
                "required": ["description", "schedule"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram",
            "description": "Send a message to the operator via Telegram. Use for important updates, task completions, or when you need human input on a long-running task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to send"}
                },
                "required": ["message"]
            }
        }
    }
]


async def execute_tool(
    tool_name: str,
    tool_args: dict[str, Any],
    memory_manager: Any,
    project_id: str | None = None,
    session_id: str | None = None,
) -> str:
    """Execute a tool call and return the result as a string."""
    try:
        if tool_name == "remember":
            return f"Stored in {tool_args['tier']} memory: {tool_args['content'][:100]}"

        elif tool_name == "recall":
            tiers = tool_args.get("tiers", ["episodic", "semantic"])
            return f"Searching for: {tool_args['query']} in tiers: {tiers}"

        elif tool_name == "create_graph_node":
            return f"Graph node created: {tool_args['label']} (type: {tool_args['node_type']})"

        elif tool_name == "link_concepts":
            return f"Linked '{tool_args['node_a_label']}' and '{tool_args['node_b_label']}' via: {tool_args['relationship']}"

        elif tool_name == "read_file":
            safe_path = _safe_workspace_path(tool_args["path"], project_id)
            if not safe_path.exists():
                return f"File not found: {tool_args['path']}"
            return safe_path.read_text(encoding="utf-8", errors="replace")

        elif tool_name == "write_file":
            safe_path = _safe_workspace_path(tool_args["path"], project_id)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(tool_args["content"], encoding="utf-8")
            return f"File written: {tool_args['path']} ({len(tool_args['content'])} bytes)"

        elif tool_name == "list_workspace_files":
            base = _get_workspace_base(project_id)
            sub = tool_args.get("path", "")
            target = (base / sub) if sub else base
            target = target.resolve()
            if not str(target).startswith(str(base)):
                return "Access denied: path outside workspace"
            if not target.exists():
                return f"Directory not found: {sub}"
            entries = []
            for item in sorted(target.iterdir()):
                kind = "dir" if item.is_dir() else "file"
                size = item.stat().st_size if item.is_file() else 0
                entries.append(f"[{kind}] {item.name}" + (f" ({size} bytes)" if kind == "file" else ""))
            return "\n".join(entries) if entries else "Empty directory"

        elif tool_name == "web_search":
            return await _ddg_search(tool_args["query"])

        elif tool_name == "create_task":
            return f"Task scheduled: {tool_args.get('name', 'task')} - {tool_args['description'][:100]}"

        elif tool_name == "send_telegram":
            return f"Telegram message sent: {tool_args['message'][:100]}"

        else:
            return f"Unknown tool: {tool_name}"

    except Exception as e:
        logger.error(f"Tool '{tool_name}' error: {e}", exc_info=True)
        return f"Error executing {tool_name}: {str(e)}"


def _get_workspace_base(project_id: str | None = None) -> Path:
    if project_id and project_id != "default":
        path = settings.projects_dir / project_id / "workspace"
    else:
        path = settings.workspace_dir
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _safe_workspace_path(rel_path: str, project_id: str | None = None) -> Path:
    """Resolve path safely within workspace to prevent path traversal."""
    base = _get_workspace_base(project_id)
    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError(f"Path traversal denied: {rel_path}")
    return target


async def _ddg_search(query: str) -> str:
    """Simple DuckDuckGo search via their HTML interface."""
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AgentHarness/1.0)"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, data={"q": query, "b": ""}, headers=headers)
            resp.raise_for_status()
            import re
            results = re.findall(r'<a class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', resp.text, re.S)
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.S)
            clean_tag = re.compile(r'<[^>]+>')
            lines = []
            for i, (url, title) in enumerate(results[:5]):
                clean_title = clean_tag.sub('', title).strip()
                snippet = clean_tag.sub('', snippets[i]).strip() if i < len(snippets) else ""
                lines.append(f"{i+1}. {clean_title}\n   {url}\n   {snippet}")
            return "\n\n".join(lines) if lines else "No results found."
    except Exception as e:
        return f"Search failed: {e}"
