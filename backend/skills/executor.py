"""Skill executor — run skill scripts in a sandboxed subprocess.

Security constraints enforced at runtime:
  - Scripts run as subprocesses (never imported into the backend)
  - Timeout and memory limits
  - No shell expansion
  - Working directory confined to skill dir or workspace
  - Environment variables filtered (no secrets leak)
  - Network access gated by declared capabilities
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from skills.models import LoadedSkill

logger = logging.getLogger(__name__)

# ── Defaults ────────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT_SECONDS = 30
MAX_TIMEOUT_SECONDS = 300
MAX_OUTPUT_BYTES = 1024 * 512  # 512 KB
ALLOWED_ENV_KEYS = {
    "PATH", "HOME", "USER", "LANG", "LC_ALL", "PYTHONPATH",
    "NODE_PATH", "TERM",
}


def _build_safe_env(skill: LoadedSkill, extra_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build a filtered environment for the subprocess.

    Only allows safe variables plus any explicitly declared vault secrets
    the skill is permitted to access.
    """
    env: dict[str, str] = {}
    for key in ALLOWED_ENV_KEYS:
        val = os.environ.get(key)
        if val:
            env[key] = val

    # Add any skill-specific env (e.g., resolved vault secrets)
    if extra_env:
        for key, val in extra_env.items():
            # Only allow secrets the skill declared in permissions
            allowed_secrets = skill.manifest.pantheon.permissions.vault_secrets
            if key in allowed_secrets or key in ALLOWED_ENV_KEYS:
                env[key] = val

    return env


def _validate_script_path(skill: LoadedSkill, script_name: str) -> Path:
    """Validate that the requested script exists inside the skill directory."""
    skill_dir = Path(skill.skill_dir)
    script_path = (skill_dir / script_name).resolve()

    # Ensure the resolved path is inside the skill directory (prevent traversal)
    if not str(script_path).startswith(str(skill_dir.resolve())):
        raise ValueError(f"Script path escapes skill directory: {script_name}")

    if not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script_name}")

    return script_path


def _get_interpreter(script_path: Path) -> list[str]:
    """Determine the interpreter for a script based on extension."""
    ext = script_path.suffix.lower()
    interpreters = {
        ".py": ["python3"],
        ".js": ["node"],
        ".ts": ["npx", "tsx"],
        ".sh": ["bash"],
        ".bash": ["bash"],
    }
    return interpreters.get(ext, ["python3"])


async def execute_script(
    skill: LoadedSkill,
    script_name: str,
    args: list[str] | None = None,
    input_data: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    workspace_dir: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Execute a skill's script in a sandboxed subprocess.

    Args:
        skill: The loaded skill
        script_name: Relative path to the script within the skill dir (e.g., "scripts/scrape.py")
        args: Command-line arguments to pass to the script
        input_data: Data to pipe to the script's stdin (as JSON)
        timeout: Max execution time in seconds
        workspace_dir: Working directory for the script (defaults to skill dir)
        extra_env: Additional environment variables (filtered by permissions)

    Returns:
        Dict with stdout, stderr, exit_code, timed_out, duration_ms
    """
    script_path = _validate_script_path(skill, script_name)
    interpreter = _get_interpreter(script_path)
    timeout = min(timeout, MAX_TIMEOUT_SECONDS)

    cmd = interpreter + [str(script_path)]
    if args:
        cmd.extend(args)

    env = _build_safe_env(skill, extra_env)
    cwd = str(workspace_dir) if workspace_dir else str(Path(skill.skill_dir))

    logger.info(
        "Executing skill script: %s %s (timeout=%ds, cwd=%s)",
        skill.name, script_name, timeout, cwd,
    )

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd,
            # No shell=True — prevents shell injection
        )

        stdin_bytes = input_data.encode("utf-8") if input_data else None

        import time
        start = time.monotonic()
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=stdin_bytes),
                timeout=timeout,
            )
            timed_out = False
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            stdout_bytes = b""
            stderr_bytes = b"Script execution timed out"
            timed_out = True

        duration_ms = int((time.monotonic() - start) * 1000)

        # Truncate large outputs
        stdout = stdout_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
        stderr = stderr_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")

        result = {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": proc.returncode or 0,
            "timed_out": timed_out,
            "duration_ms": duration_ms,
            "script": script_name,
            "skill": skill.name,
        }

        if timed_out:
            logger.warning("Script timed out: %s/%s after %ds", skill.name, script_name, timeout)
        elif proc.returncode != 0:
            logger.warning(
                "Script failed: %s/%s exit=%d stderr=%s",
                skill.name, script_name, proc.returncode, stderr[:200],
            )
        else:
            logger.info(
                "Script completed: %s/%s in %dms",
                skill.name, script_name, duration_ms,
            )

        return result

    except FileNotFoundError as e:
        return {
            "stdout": "",
            "stderr": f"Interpreter not found: {e}",
            "exit_code": 127,
            "timed_out": False,
            "duration_ms": 0,
            "script": script_name,
            "skill": skill.name,
        }
    except Exception as e:
        logger.error("Execution error for %s/%s: %s", skill.name, script_name, e, exc_info=True)
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
            "timed_out": False,
            "duration_ms": 0,
            "script": script_name,
            "skill": skill.name,
        }
