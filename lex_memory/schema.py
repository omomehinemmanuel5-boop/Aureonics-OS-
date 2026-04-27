from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


StateLabel = Literal["SAFE", "INTERVENED", "REFUSED", "STABLE", "UNSTABLE"]


@dataclass(slots=True)
class LexMemoryEvent:
    prompt: str
    response_raw: str
    response_governed: str
    response_final: str
    intervention: bool
    intervention_reason: str
    semantic_diff_score: float
    M: float
    C: float
    R: float
    S: float
    state_label: StateLabel
    embedding: list[float]
    model: str | None = None
    version: str | None = None
    session_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_record(self) -> dict:
        """Serialized append-only payload for Supabase insert."""
        return {
            "prompt": self.prompt,
            "response_raw": self.response_raw,
            "response_governed": self.response_governed,
            "response_final": self.response_final,
            "intervention": bool(self.intervention),
            "intervention_reason": self.intervention_reason,
            "semantic_diff_score": float(self.semantic_diff_score),
            "M": float(self.M),
            "C": float(self.C),
            "R": float(self.R),
            "S": float(self.S),
            "state_label": self.state_label,
            "embedding": self.embedding,
            "model": self.model,
            "version": self.version,
            "session_id": self.session_id,
        }
