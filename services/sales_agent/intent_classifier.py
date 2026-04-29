from __future__ import annotations

from .conversation_state import IntentClass, LeadProfile


class IntentClassifier:
    def classify(self, message: str, lead: LeadProfile) -> tuple[IntentClass, float]:
        text = message.lower()
        score = (
            lead.urgency_score * 0.25
            + lead.technical_depth * 0.2
            + lead.budget_hint * 0.2
            + lead.compliance_interest * 0.15
            + lead.response_speed * 0.2
        )
        if any(k in text for k in ["buy now", "contract", "start today", "payment"]):
            score += 0.25
        if any(k in text for k in ["not interested", "stop", "unsubscribe"]):
            return IntentClass.DEAD, 0.95
        if score >= 0.75:
            return IntentClass.HOT, min(score, 0.99)
        if score >= 0.45:
            return IntentClass.WARM, score
        return IntentClass.COLD, score
