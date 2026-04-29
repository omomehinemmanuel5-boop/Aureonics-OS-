class EscalationEngine:
    def should_escalate(self, intent: str, deal_value: float) -> tuple[bool, str | None]:
        if intent in {"legal", "security_review", "pricing"}:
            return True, f"intent:{intent}"
        if deal_value >= 250000:
            return True, "high_value_deal"
        return False, None
