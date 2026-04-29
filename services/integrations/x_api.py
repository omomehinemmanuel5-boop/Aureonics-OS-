from __future__ import annotations
from typing import List

from services.growth.models import Lead


class XApiClient:
    """Simulated X API integration with local fixtures."""

    def fetch_ai_leads(self) -> List[Lead]:
        return [
            Lead("x-001", "Ari Stone", "Founder", "VectorPilot", 23, "x", "https://x.com/aristone", {"ai_usage": 0.92, "urgency": 0.81}, {"recent_post": "shipping AI copilots to fintech teams"}),
            Lead("x-002", "Mina Cho", "CTO", "LexFlow", 140, "x", "https://x.com/minacho", {"ai_usage": 0.73, "urgency": 0.66}, {"recent_post": "SOC2 prep for legal AI"}),
        ]
