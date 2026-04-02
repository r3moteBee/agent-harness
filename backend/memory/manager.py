"""Memory manager — orchestrates all 5 memory tiers."""
from __future__ import annotations
import logging
from typing import Any

from memory.working import WorkingMemory
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.graph import GraphMemory
from memory.archival import ArchivalMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """Central interface for all memory operations across all 5 tiers.
    
    Usage:
        manager = MemoryManager(project_id="my-project")
        await manager.remember("Alice is our main client", tier="semantic")
        results = await manager.recall("who is our client?")
    """

    def __init__(
        self,
        project_id: str = "default",
        session_id: str | None = None,
        embedding_fn: Any = None,
        max_working_tokens: int = 8000,
    ):
        self.project_id = project_id
        self.session_id = session_id
        self.embedding_fn = embedding_fn

        # Initialize all tiers
        self.working = WorkingMemory(max_tokens=max_working_tokens)
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory(project_id=project_id, embedding_fn=embedding_fn)
        self.graph = GraphMemory(project_id=project_id)
        self.archival = ArchivalMemory(project_id=project_id)

    def set_active_project(self, project_id: str) -> None:
        """Switch all memory tiers to a different project namespace."""
        self.project_id = project_id
        self.semantic = SemanticMemory(project_id=project_id, embedding_fn=self.embedding_fn)
        self.graph = GraphMemory(project_id=project_id)
        self.archival = ArchivalMemory(project_id=project_id)
        logger.info(f"Memory manager switched to project: {project_id}")

    async def remember(
        self,
        content: str,
        tier: str = "semantic",
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> str:
        """Store content in the specified memory tier."""
        sid = session_id or self.session_id or "default"
        meta = metadata or {}

        if tier == "working":
            self.working.add_message("system", content)
            return "stored:working"

        elif tier == "episodic":
            note_id = await self.episodic.add_note(
                content=content,
                project_id=self.project_id,
                session_id=sid,
                tags=meta.get("tags", []),
            )
            return f"stored:episodic:{note_id}"

        elif tier == "semantic":
            doc_id = await self.semantic.store(content=content, metadata=meta)
            return f"stored:semantic:{doc_id}"

        elif tier == "archival":
            filename = await self.archival.append_note(content)
            return f"stored:archival:{filename}"

        else:
            logger.warning(f"Unknown memory tier: {tier}, defaulting to semantic")
            doc_id = await self.semantic.store(content=content, metadata=meta)
            return f"stored:semantic:{doc_id}"

    async def recall(
        self,
        query: str,
        tiers: list[str] | None = None,
        project_id: str | None = None,
        limit_per_tier: int = 3,
    ) -> list[dict[str, Any]]:
        """Search across multiple memory tiers and return merged results.
        
        Returns list of dicts with keys: content, source, score, metadata
        """
        active_project = project_id or self.project_id
        if tiers is None:
            tiers = ["semantic", "episodic", "graph"]

        all_results: list[dict[str, Any]] = []

        if "semantic" in tiers:
            try:
                sem_results = await self.semantic.search(query, n=limit_per_tier)
                for r in sem_results:
                    r["source"] = "semantic"
                    r["tier"] = "semantic"
                all_results.extend(sem_results)
            except Exception as e:
                logger.error(f"Semantic recall error: {e}")

        if "episodic" in tiers:
            try:
                ep_results = await self.episodic.search_messages(
                    query=query,
                    project_id=active_project,
                    limit=limit_per_tier * 2,
                )
                # Convert to standard format
                for r in ep_results[:limit_per_tier]:
                    all_results.append({
                        "id": r["id"],
                        "content": f"[{r['role']}] {r['content']}",
                        "source": "episodic",
                        "tier": "episodic",
                        "score": 0.5,  # No relevance score for text search
                        "metadata": {"session_id": r.get("session_id"), "timestamp": r.get("timestamp")},
                    })
            except Exception as e:
                logger.error(f"Episodic recall error: {e}")

        if "graph" in tiers:
            try:
                graph_results = await self.graph.search_nodes(query, limit=limit_per_tier * 2)
                # Also fetch all edges once to build relationship lines
                all_edges = await self.graph.list_edges(limit=500)
                edge_index: dict[str, list[str]] = {}
                for e in all_edges:
                    a, b, rel = e["node_a_label"], e["node_b_label"], e["relationship"]
                    edge_index.setdefault(a, []).append(f"  → {rel}: {b}")
                    edge_index.setdefault(b, []).append(f"  ← {rel}: {a}")

                for r in graph_results[:limit_per_tier]:
                    label = r["label"]
                    rels = edge_index.get(label, [])
                    rel_text = ("\n" + "\n".join(rels)) if rels else ""
                    all_results.append({
                        "id": r["id"],
                        "content": f"[graph:{r['node_type']}] {label}{rel_text}",
                        "source": "graph",
                        "tier": "graph",
                        "score": 0.65,
                        "metadata": r.get("metadata", {}),
                    })
            except Exception as e:
                logger.error(f"Graph recall error: {e}")

        # Sort by score descending
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results

    async def audit_memory(
        self,
        tier: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """Return all memories for a tier (for inspection/editing in the UI)."""
        active_project = project_id or self.project_id

        if tier == "working":
            return {
                "tier": "working",
                "items": [
                    {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                    for m in self.working.get_messages(as_dicts=False)
                ],
                "token_count": self.working.get_token_count(),
            }

        elif tier == "episodic":
            messages = await self.episodic.get_all_messages(project_id=active_project, limit=200)
            notes = await self.episodic.get_notes(project_id=active_project, limit=50)
            return {
                "tier": "episodic",
                "messages": messages,
                "notes": notes,
                "total_messages": len(messages),
            }

        elif tier == "semantic":
            items = await self.semantic.list_memories(limit=100)
            count = await self.semantic.count()
            return {
                "tier": "semantic",
                "items": items,
                "total": count,
            }

        elif tier == "graph":
            nodes = await self.graph.list_nodes(limit=200)
            edges = await self.graph.list_edges(limit=500)
            return {
                "tier": "graph",
                "nodes": nodes,
                "edges": edges,
            }

        elif tier == "archival":
            files = await self.archival.list_files()
            notes = await self.archival.list_notes()
            summary = await self.archival.get_project_summary()
            return {
                "tier": "archival",
                "files": files,
                "notes": notes,
                "project_summary": summary,
            }

        return {"tier": tier, "error": "Unknown tier"}

    async def consolidate_session(self) -> str:
        """Consolidate current session's working memory to semantic/archival.
        
        Call at the end of a session to promote important information.
        Returns a summary of what was stored.
        """
        messages = self.working.get_messages(as_dicts=True)
        if not messages:
            return "No messages to consolidate."

        # Build a summary text from recent messages
        summary_lines = []
        for msg in messages[-20:]:  # Last 20 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:300]  # Truncate
            if role in ("user", "assistant"):
                summary_lines.append(f"{role}: {content}")

        if not summary_lines:
            return "No user/assistant messages to consolidate."

        summary_text = "\n".join(summary_lines)
        session_summary = f"Session summary (session_id={self.session_id}):\n{summary_text}"

        # Store to semantic memory
        doc_id = await self.semantic.store(
            content=session_summary,
            metadata={
                "type": "session_summary",
                "session_id": self.session_id or "unknown",
                "project_id": self.project_id,
            },
        )

        # Clear working memory
        self.working.clear()

        logger.info(f"Session consolidated to semantic memory: {doc_id}")
        return f"Session consolidated. Summary stored as semantic memory: {doc_id}"


def create_memory_manager(
    project_id: str = "default",
    session_id: str | None = None,
    provider: Any = None,
) -> MemoryManager:
    """Factory function to create a MemoryManager with optional embedding support.

    Uses the dedicated embedding provider when available so embeddings can be
    routed to a different endpoint/model than the primary chat LLM.
    """
    embedding_fn = None
    try:
        from models.provider import get_embedding_provider
        emb_provider = get_embedding_provider()
        embedding_fn = emb_provider.embed
    except Exception:
        # Fall back to the primary provider passed in
        if provider:
            embedding_fn = provider.embed
    return MemoryManager(
        project_id=project_id,
        session_id=session_id,
        embedding_fn=embedding_fn,
    )
