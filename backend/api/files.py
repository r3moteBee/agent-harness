"""File repository API — upload, download, list, delete workspace files."""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import APIRouter, Body, HTTPException, UploadFile, File, Query
from typing import List as TList
from fastapi.responses import FileResponse

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


def _get_workspace(project_id: str = "default") -> Path:
    if project_id and project_id != "default":
        path = settings.projects_dir / project_id / "workspace"
    else:
        path = settings.workspace_dir
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def _safe_path(rel_path: str, project_id: str = "default") -> Path:
    base = _get_workspace(project_id)
    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Path traversal denied")
    return target


@router.get("/files")
async def list_files(
    project_id: str = Query(default="default"),
    path: str = Query(default=""),
) -> dict[str, Any]:
    """List files and directories in the workspace."""
    try:
        base = _get_workspace(project_id)
        target = _safe_path(path, project_id) if path else base
        if not target.exists():
            return {"files": [], "directories": [], "path": path}

        files = []
        directories = []
        for item in sorted(target.iterdir()):
            rel = str(item.relative_to(base))
            stat = item.stat()
            if item.is_dir():
                directories.append({
                    "name": item.name,
                    "path": rel,
                    "type": "directory",
                })
            else:
                files.append({
                    "name": item.name,
                    "path": rel,
                    "type": "file",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "extension": item.suffix.lower(),
                })

        return {
            "files": files,
            "directories": directories,
            "path": path,
            "total_files": len(files),
            "total_dirs": len(directories),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Query(default="default"),
    path: str = Query(default=""),
) -> dict[str, Any]:
    """Upload a file to the workspace."""
    filename = file.filename or "upload"
    # Sanitize filename
    filename = Path(filename).name  # Strip any path components
    dest_dir = _safe_path(path, project_id) if path else _get_workspace(project_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    # Handle filename conflicts
    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    content = await file.read()
    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(content)

    base = _get_workspace(project_id)
    return {
        "status": "uploaded",
        "filename": dest_path.name,
        "path": str(dest_path.relative_to(base)),
        "size": len(content),
    }


@router.post("/files/upload-multiple")
async def upload_multiple_files(
    files: TList[UploadFile] = File(...),
    project_id: str = Query(default="default"),
    path: str = Query(default=""),
) -> dict[str, Any]:
    """Upload multiple files to the workspace at once."""
    dest_dir = _safe_path(path, project_id) if path else _get_workspace(project_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = _get_workspace(project_id)
    results = []

    for file in files:
        filename = file.filename or "upload"
        filename = Path(filename).name
        dest_path = dest_dir / filename

        # Handle filename conflicts
        if dest_path.exists():
            stem = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        content = await file.read()
        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(content)

        results.append({
            "filename": dest_path.name,
            "path": str(dest_path.relative_to(base)),
            "size": len(content),
        })

    return {
        "status": "uploaded",
        "count": len(results),
        "files": results,
    }


@router.get("/files/download")
async def download_file(
    path: str = Query(...),
    project_id: str = Query(default="default"),
) -> FileResponse:
    """Download a file from the workspace."""
    target = _safe_path(path, project_id)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=str(target),
        filename=target.name,
        media_type="application/octet-stream",
    )


@router.get("/files/read")
async def read_file_content(
    path: str = Query(...),
    project_id: str = Query(default="default"),
) -> dict[str, Any]:
    """Read file content as text."""
    target = _safe_path(path, project_id)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "path": path,
            "content": content,
            "size": target.stat().st_size,
            "encoding": "utf-8",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/files/write")
async def write_file_content(
    path: str = Query(...),
    project_id: str = Query(default="default"),
    body: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    """Write text content to an existing or new file in the workspace."""
    content = body.get("content")
    if content is None:
        raise HTTPException(status_code=400, detail="Missing 'content' field")
    target = _safe_path(path, project_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(target, "w", encoding="utf-8") as f:
        await f.write(content)
    return {
        "status": "saved",
        "path": path,
        "size": len(content.encode("utf-8")),
    }


@router.delete("/files")
async def delete_file(
    path: str = Query(...),
    project_id: str = Query(default="default"),
) -> dict[str, str]:
    """Delete a file from the workspace."""
    target = _safe_path(path, project_id)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if target.is_dir():
        import shutil
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"status": "deleted", "path": path}


@router.post("/files/mkdir")
async def create_directory(
    path: str = Query(...),
    project_id: str = Query(default="default"),
) -> dict[str, str]:
    """Create a directory in the workspace."""
    target = _safe_path(path, project_id)
    target.mkdir(parents=True, exist_ok=True)
    return {"status": "created", "path": path}
