from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass
class MemoryItem:
    id: str
    organization_id: str
    raw_output: str
    correction: str
    embedding: list[float]


class InMemoryVectorStore:
    """Simple vector memory abstraction with pluggable persistence.

    For production, replace with pgvector/Supabase RPC adapter.
    """

    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def add(self, item: MemoryItem) -> None:
        self._items.append(item)

    def similar(self, organization_id: str, query_embedding: list[float], k: int = 5) -> list[dict[str, Any]]:
        scoped = [item for item in self._items if item.organization_id == organization_id]
        scored = [
            {
                "id": item.id,
                "raw_output": item.raw_output,
                "correction": item.correction,
                "score": self._cosine_similarity(query_embedding, item.embedding),
            }
            for item in scoped
        ]
        return sorted(scored, key=lambda row: row["score"], reverse=True)[:k]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sqrt(sum(x * x for x in a))
        norm_b = sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
