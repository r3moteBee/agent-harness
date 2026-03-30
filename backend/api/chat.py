"""Chat API — POST /api/chat, GET /api/chat/history, WebSocket /ws/chat."""
from __future__ import annotations
import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel

from agent.core import AgentCore
from config import get_settings
from memory.manager import create_memory_manager
from models.provider import get_provider

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    project_id: str = "default"
    stream: bool = True


class ChatResponse(BaseModel):
    session_id: str
    response: str
    project_id: str


class HistoryRequest(BaseModel):
    session_id: str
    project_id: str = "default"
    limit: int = 50


# Active WebSocket connections
_active_connections: dict[str, WebSocket] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message to the agent and get a response (non-streaming)."""
    session_id = req.session_id or str(uuid.uuid4())
    provider = get_provider()
    memory = create_memory_manager(
        project_id=req.project_id,
        session_id=session_id,
        provider=provider,
    )

    agent = AgentCore(
        provider=provider,
        memory_manager=memory,
        project_id=req.project_id,
        session_id=session_id,
    )

    full_response = ""
    async for event in agent.chat(req.message, stream=False):
        if event["type"] == "done":
            full_response = event.get("full_response", "")
        elif event["type"] == "error":
            raise HTTPException(status_code=500, detail=event["message"])

    return ChatResponse(
        session_id=session_id,
        response=full_response,
        project_id=req.project_id,
    )


@router.get("/chat/history")
async def get_history(
    session_id: str = Query(...),
    project_id: str = Query(default="default"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """Get conversation history for a session."""
    from memory.episodic import EpisodicMemory
    episodic = EpisodicMemory()
    messages = await episodic.get_history(session_id=session_id, limit=limit)
    return {"session_id": session_id, "messages": messages, "count": len(messages)}


@router.get("/chat/sessions")
async def list_sessions(
    project_id: str = Query(default="default"),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """List recent chat sessions for a project."""
    from memory.episodic import EpisodicMemory
    episodic = EpisodicMemory()
    sessions = await episodic.get_sessions(project_id=project_id, limit=limit)
    return {"sessions": sessions, "project_id": project_id}


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming chat with the agent."""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    _active_connections[connection_id] = websocket
    logger.info(f"WebSocket connected: {connection_id}")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            message = data.get("message", "")
            session_id = data.get("session_id") or str(uuid.uuid4())
            project_id = data.get("project_id", "default")

            if not message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            # Send session_id back to client
            await websocket.send_json({"type": "session_start", "session_id": session_id})

            provider = get_provider()
            memory = create_memory_manager(
                project_id=project_id,
                session_id=session_id,
                provider=provider,
            )
            agent = AgentCore(
                provider=provider,
                memory_manager=memory,
                project_id=project_id,
                session_id=session_id,
            )

            async for event in agent.chat(message, stream=True):
                try:
                    await websocket.send_json(event)
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        _active_connections.pop(connection_id, None)
