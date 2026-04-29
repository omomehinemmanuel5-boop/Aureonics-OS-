from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AnalyticsEngine:
    metrics: Dict[str, float] = field(default_factory=lambda: {
        "messages_sent": 0,
        "replies": 0,
        "positive_replies": 0,
        "demos_booked": 0,
        "paid_conversions": 0,
    })

    def track(self, key: str, inc: float = 1) -> None:
        self.metrics[key] = self.metrics.get(key, 0) + inc

    def snapshot(self) -> Dict[str, float]:
        m = self.metrics
        m["reply_rate"] = (m["replies"] / m["messages_sent"]) if m["messages_sent"] else 0
        m["positive_reply_rate"] = (m["positive_replies"] / m["replies"]) if m["replies"] else 0
        m["demo_booked_rate"] = (m["demos_booked"] / m["positive_replies"]) if m["positive_replies"] else 0
        m["conversion_to_paid"] = (m["paid_conversions"] / m["demos_booked"]) if m["demos_booked"] else 0
        return dict(m)
