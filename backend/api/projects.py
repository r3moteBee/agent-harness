"""Projects API — create, list, switch, delete project namespaces."""
from __future__ import annotations
import json
import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

_PROJECTS_META_FILE = None


def _meta_file() -> Path:
    path = settings.db_dir / "projects.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_projects() -> dict[str, Any]:
    meta = _meta_file()
    if meta.exists():
        try:
            return json.loads(meta.read_text())
        except Exception:
            pass
    # Initialize with default project
    default = {
        "default": {
            "id": "default",
            "name": "Default Project",
            "description": "The default project workspace",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }
    }
    meta.write_text(json.dumps(default, indent=2))
    return default


def _save_projects(projects: dict[str, Any]) -> None:
    _meta_file().write_text(json.dumps(projects, indent=2))


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    id: str | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None


@router.get("/projects")
async def list_projects() -> dict[str, Any]:
    """List all projects."""
    projects = _load_projects()
    return {"projects": list(projects.values()), "count": len(projects)}


@router.post("/projects")
async def create_project(req: CreateProjectRequest) -> dict[str, Any]:
    """Create a new project."""
    projects = _load_projects()
    project_id = req.id or str(uuid.uuid4())[:8]

    # Sanitize ID
    import re
    project_id = re.sub(r'[^a-zA-Z0-9-_]', '-', project_id).lower()

    if project_id in projects:
        raise HTTPException(status_code=409, detail=f"Project '{project_id}' already exists")

    project = {
        "id": project_id,
        "name": req.name,
        "description": req.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active": True,
    }
    projects[project_id] = project

    # Create project directories
    project_dir = settings.projects_dir / project_id
    for subdir in ["workspace", "personality", "notes"]:
        (project_dir / subdir).mkdir(parents=True, exist_ok=True)

    _save_projects(projects)
    logger.info(f"Project created: {project_id}")
    return project


@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> dict[str, Any]:
    """Get project details."""
    projects = _load_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    project = projects[project_id]

    # Add memory stats
    try:
        from memory.semantic import SemanticMemory
        sem = SemanticMemory(project_id=project_id)
        project["semantic_memory_count"] = await sem.count()
    except Exception:
        project["semantic_memory_count"] = 0

    return project


@router.put("/projects/{project_id}")
async def update_project(project_id: str, req: UpdateProjectRequest) -> dict[str, Any]:
    """Update project metadata."""
    projects = _load_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    if req.name:
        projects[project_id]["name"] = req.name
    if req.description is not None:
        projects[project_id]["description"] = req.description
    projects[project_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_projects(projects)
    return projects[project_id]


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str) -> dict[str, str]:
    """Delete a project and all its data."""
    if project_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete the default project")
    projects = _load_projects()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete project files
    project_dir = settings.projects_dir / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)

    del projects[project_id]
    _save_projects(projects)
    logger.info(f"Project deleted: {project_id}")
    return {"status": "deleted", "project_id": project_id}
