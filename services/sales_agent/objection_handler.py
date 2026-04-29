from __future__ import annotations

OBJECTION_PLAYS = {
    "we already use": "Totally fair — most teams we replace felt that too. Want a 2-min comparison against your current stack?",
    "too expensive": "Understood. We usually cut manual sales effort by 30-50%; happy to show ROI in 2 minutes.",
    "not priority": "Makes sense. If I show a low-lift rollout this week, would it become a priority?",
    "need approval": "Perfect — I can send a one-page business case and join your approval call.",
    "send info": "Absolutely — I’ll send concise info plus a fast demo slot so you can validate quickly.",
}


class ObjectionHandler:
    def resolve(self, message: str) -> str | None:
        text = message.lower()
        for key, response in OBJECTION_PLAYS.items():
            if key in text:
                return response
        return None
