from __future__ import annotations

from .conversation_state import IntentClass


class ClosingEngine:
    def next_action(self, intent: IntentClass) -> str:
        if intent == IntentClass.HOT:
            return "push_to_action"
        if intent == IntentClass.WARM:
            return "book_demo"
        if intent == IntentClass.COLD:
            return "nurture"
        return "stop"

    def close_message(self, action: str) -> str:
        return {
            "push_to_action": "I can plug this into your stack today — should I activate your trial now?",
            "book_demo": "Want me to lock a 15-minute demo slot this week?",
            "nurture": "I’ll send a short use-case note and check back next week.",
            "stop": "I’ll pause here.",
        }[action]
