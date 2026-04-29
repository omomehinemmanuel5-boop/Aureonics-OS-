from __future__ import annotations

from .conversation_state import IntentClass

TEMPLATES = {
    IntentClass.HOT: "Great fit. Want a 2-min live demo, trial activation, or direct enterprise call?",
    IntentClass.WARM: "Happy to clarify quickly. What’s the main blocker: integration, security, or ROI?",
    IntentClass.COLD: "Quick intro: Lex Aureon is a self-healing AI sales agent that books and closes faster. Open to a short demo?",
    IntentClass.DEAD: "Understood — I’ll pause outreach. If priorities shift, I’m here.",
}


class MessageGenerator:
    def generate(self, intent: IntentClass, custom: str | None = None) -> str:
        return custom or TEMPLATES[intent]
