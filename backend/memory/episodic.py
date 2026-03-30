"""Tier 2: Episodic memory — SQLite-backed conversation history and task logs."""
from __future__ import annotations
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EpisodicMemory:
    """Tier 2: Persistent conversation history, task logs, and memory notes.
    
    Backed by SQLite for simplicity, reliability, and zero dependencies.
    All queries are synchronous SQLite operations wrapped in async interfaces.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or "data/episodic.db"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL DEFAULT 'default',
                    session_id TEXT NOT NULL,
                    title TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    project_id TEXT NOT NULL DEFAULT 'default',
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS task_logs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL DEFAULT 'default',
                    task_id TEXT NOT NULL,
                    task_name TEXT,
                    event TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memory_notes (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL DEFAULT 'default',
                    session_id TEXT,
                    content TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_messages_project ON messages(project_id);
                CREATE INDEX IF NOT EXISTS idx_task_logs_task ON task_logs(task_id);
                CREATE INDEX IF NOT EXISTS idx_notes_project ON memory_notes(project_id);
            """)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def save_message(
        self,
        session_id: str,
        project_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> str:
        """Save a conversation message to episodic memory."""
        msg_id = str(uuid.uuid4())
        now = _now_iso()
        with self._connect() as conn:
            # Upsert conversation record
            conn.execute("""
                INSERT INTO conversations (id, project_id, session_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
            """, (session_id, project_id, session_id, now, now))

            conn.execute("""
                UPDATE conversations SET updated_at = ? WHERE id = ?
            """, (now, session_id))

            conn.execute("""
                INSERT INTO messages (id, project_id, session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                msg_id, project_id, session_id, role, content, now,
                json.dumps(metadata or {})
            ))
            conn.commit()
        return msg_id

    async def get_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get conversation history for a session."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT id, role, content, timestamp, metadata
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
            """, (session_id, limit, offset)).fetchall()
        return [
            {
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["timestamp"],
                "metadata": json.loads(r["metadata"] or "{}"),
            }
            for r in rows
        ]

    async def get_sessions(
        self,
        project_id: str = "default",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent conversation sessions for a project."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT c.id, c.session_id, c.title, c.created_at, c.updated_at,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON m.session_id = c.session_id
                WHERE c.project_id = ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ?
            """, (project_id, limit)).fetchall()
        return [dict(r) for r in rows]

    async def search_messages(
        self,
        query: str,
        project_id: str = "default",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Full-text search across messages (SQLite LIKE)."""
        pattern = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT id, session_id, role, content, timestamp
                FROM messages
                WHERE project_id = ? AND content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (project_id, pattern, limit)).fetchall()
        return [dict(r) for r in rows]

    async def search_by_date(
        self,
        project_id: str,
        start_date: str,
        end_date: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search messages within a date range."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT id, session_id, role, content, timestamp, metadata
                FROM messages
                WHERE project_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (project_id, start_date, end_date, limit)).fetchall()
        return [
            {**dict(r), "metadata": json.loads(r["metadata"] or "{}")}
            for r in rows
        ]

    async def log_task_event(
        self,
        task_id: str,
        event: str,
        project_id: str = "default",
        task_name: str | None = None,
        details: str | None = None,
    ) -> str:
        """Log a task lifecycle event."""
        log_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO task_logs (id, project_id, task_id, task_name, event, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (log_id, project_id, task_id, task_name, event, details, _now_iso()))
            conn.commit()
        return log_id

    async def get_task_logs(
        self,
        task_id: str | None = None,
        project_id: str = "default",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve task logs."""
        with self._connect() as conn:
            if task_id:
                rows = conn.execute("""
                    SELECT * FROM task_logs
                    WHERE task_id = ? AND project_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (task_id, project_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM task_logs
                    WHERE project_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (project_id, limit)).fetchall()
        return [dict(r) for r in rows]

    async def add_note(
        self,
        content: str,
        project_id: str = "default",
        session_id: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Add a memory note."""
        note_id = str(uuid.uuid4())
        now = _now_iso()
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO memory_notes (id, project_id, session_id, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (note_id, project_id, session_id, content, json.dumps(tags or []), now, now))
            conn.commit()
        return note_id

    async def get_notes(
        self,
        project_id: str = "default",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get memory notes for a project."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT id, content, tags, session_id, created_at, updated_at
                FROM memory_notes
                WHERE project_id = ?
                ORDER BY updated_at DESC LIMIT ?
            """, (project_id, limit)).fetchall()
        return [
            {**dict(r), "tags": json.loads(r["tags"] or "[]")}
            for r in rows
        ]

    async def update_note(self, note_id: str, content: str) -> bool:
        """Update a memory note."""
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE memory_notes SET content = ?, updated_at = ? WHERE id = ?",
                (content, _now_iso(), note_id)
            )
            conn.commit()
        return cursor.rowcount > 0

    async def delete_note(self, note_id: str) -> bool:
        """Delete a memory note."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM memory_notes WHERE id = ?", (note_id,))
            conn.commit()
        return cursor.rowcount > 0

    async def delete_message(self, message_id: str) -> bool:
        """Delete a specific message."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            conn.commit()
        return cursor.rowcount > 0

    async def get_all_messages(
        self,
        project_id: str = "default",
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Get all messages for a project (for audit mode)."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT id, session_id, role, content, timestamp, metadata
                FROM messages
                WHERE project_id = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (project_id, limit)).fetchall()
        return [
            {**dict(r), "metadata": json.loads(r["metadata"] or "{}")}
            for r in rows
        ]
