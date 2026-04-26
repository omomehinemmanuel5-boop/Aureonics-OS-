from __future__ import annotations

from typing import Protocol


class EmbeddingModel(Protocol):
    def encode(self, text: str) -> list[float]: ...


class DeterministicEmbedder:
    """Dependency-free fallback embedder for deterministic local behavior."""

    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    def encode(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for idx, ch in enumerate((text or "").lower()):
            slot = (idx * 31 + ord(ch)) % self.dimensions
            vec[slot] += (ord(ch) % 23) / 23.0
        norm = sum(v * v for v in vec) ** 0.5
        return [round(v / norm, 8) for v in vec] if norm > 0 else vec


def embed(text: str, model: EmbeddingModel | None = None) -> list[float]:
    target = model or DeterministicEmbedder()
    encoded = target.encode(text)
    return encoded.tolist() if hasattr(encoded, "tolist") else list(encoded)
