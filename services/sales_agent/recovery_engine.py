from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecoveryResult:
    cause: str
    strategy_shift: str
    rewritten_message: str


class RecoveryEngine:
    def recover(self, failure_type: str) -> RecoveryResult:
        mapping = {
            "no_reply": ("timing_mismatch", "shorten_and_personalize", "Quick bump — worth a 2-min walkthrough this week?"),
            "negative_sentiment": ("tone_mismatch", "empathetic_tone", "Thanks for the candor. I’ll keep this brief and useful."),
            "objection_escalation": ("value_gap", "roi_proof", "Fair point. Want a side-by-side ROI snapshot for your team?"),
            "dropoff_after_demo_request": ("friction", "one_click_booking", "One-click slot here — no prep needed."),
            "booking_failure": ("calendar_conflict", "offer_async_demo", "No problem — I can send a 2-min custom async demo today."),
        }
        cause, shift, msg = mapping.get(failure_type, ("unknown", "retry", "Can we restart with your top priority?"))
        return RecoveryResult(cause, shift, msg)
