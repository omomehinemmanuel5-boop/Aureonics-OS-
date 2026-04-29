from __future__ import annotations

from dataclasses import asdict
from typing import Dict

from .conversation_state import ConversationMemory


class PersistentMemory:
    """Simple in-memory store; swap with Redis/Postgres in production."""

    def __init__(self) -> None:
        self._store: Dict[str, ConversationMemory] = {}

    def get(self, lead_id: str) -> ConversationMemory:
        if lead_id not in self._store:
            self._store[lead_id] = ConversationMemory()
        return self._store[lead_id]

    def update(self, lead_id: str, memory: ConversationMemory) -> None:
        self._store[lead_id] = memory

    def export(self) -> Dict[str, dict]:
        return {k: asdict(v) for k, v in self._store.items()}
