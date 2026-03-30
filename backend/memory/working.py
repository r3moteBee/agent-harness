"""Tier 1: Working memory — in-context conversation buffer with token management."""
from __future__ import annotations
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Rough token estimator: ~4 chars per token
def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class WorkingMessage:
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def token_estimate(self) -> int:
        return _estimate_tokens(self.content)


class WorkingMemory:
    """Tier 1: Fast in-context working memory with automatic overflow management.
    
    Holds recent conversation turns in a rolling buffer. When the token budget
    is exceeded, old messages are summarized and evicted to episodic memory.
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        max_messages: int = 50,
        episodic_callback: Any = None,  # async callable to save overflow
    ):
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self._messages: deque[WorkingMessage] = deque()
        self._token_count: int = 0
        self._episodic_callback = episodic_callback

    def add_message(self, role: str, content: str, metadata: dict | None = None) -> None:
        """Add a message to working memory, evicting old messages if needed."""
        msg = WorkingMessage(role=role, content=content, metadata=metadata or {})
        self._messages.append(msg)
        self._token_count += msg.token_estimate

        # Evict from the front if we exceed limits
        while (
            self._token_count > self.max_tokens or len(self._messages) > self.max_messages
        ) and len(self._messages) > 2:  # Always keep at least 2 messages
            evicted = self._messages.popleft()
            self._token_count -= evicted.token_estimate
            logger.debug(f"Evicted from working memory: {evicted.role} ({evicted.token_estimate} tokens)")

        logger.debug(
            f"Working memory: {len(self._messages)} messages, ~{self._token_count} tokens"
        )

    def get_messages(self, as_dicts: bool = True) -> list[Any]:
        """Return all messages in working memory."""
        if as_dicts:
            return [
                {"role": m.role, "content": m.content}
                for m in self._messages
            ]
        return list(self._messages)

    def get_token_count(self) -> int:
        """Return estimated token count for current working memory."""
        return self._token_count

    def clear(self) -> list[WorkingMessage]:
        """Clear all messages and return them (for consolidation)."""
        messages = list(self._messages)
        self._messages.clear()
        self._token_count = 0
        return messages

    def summarize_to_str(self) -> str:
        """Generate a text summary of the current working memory."""
        if not self._messages:
            return ""
        lines = []
        for m in self._messages:
            lines.append(f"{m.role.upper()}: {m.content[:500]}")
        return "\n\n".join(lines)

    def peek_recent(self, n: int = 5) -> list[WorkingMessage]:
        """Return the n most recent messages."""
        msgs = list(self._messages)
        return msgs[-n:]

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:
        return f"WorkingMemory(messages={len(self._messages)}, tokens~{self._token_count})"
