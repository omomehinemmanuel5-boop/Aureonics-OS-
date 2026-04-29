from __future__ import annotations
from datetime import datetime, timedelta

from services.growth.models import ConversationState, ScoredLead


class DMOrchestrator:
    def can_send(self, state: ConversationState | None) -> bool:
        if state is None or state.last_contacted_at is None:
            return True
        return datetime.utcnow() - state.last_contacted_at >= timedelta(hours=24)

    def compose(self, scored: ScoredLead, body: str) -> str:
        return f"[{scored.lead.channel.upper()}][{scored.intent}] {body}"
