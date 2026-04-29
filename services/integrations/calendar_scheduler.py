from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class CalendarScheduler:
    def next_slots(self, timezone: str = "UTC", count: int = 3) -> list[str]:
        now = datetime.now(tz=ZoneInfo(timezone)).replace(minute=0, second=0, microsecond=0)
        slots = []
        for i in range(1, count + 1):
            slot = now + timedelta(hours=i * 2)
            slots.append(slot.isoformat())
        return slots

    def booking_link(self, lead_id: str) -> str:
        return f"https://cal.lexaureon.ai/book/{lead_id}"
