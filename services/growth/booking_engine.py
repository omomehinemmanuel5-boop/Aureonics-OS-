from services.integrations.calendar_scheduler import CalendarScheduler


class BookingEngine:
    def __init__(self, scheduler: CalendarScheduler) -> None:
        self.scheduler = scheduler

    def booking_message(self, lead_id: str, timezone: str = "UTC") -> str:
        slots = self.scheduler.next_slots(timezone=timezone)
        link = self.scheduler.booking_link(lead_id)
        return f"Great — here are 3 slots: {', '.join(slots)}. Or book instantly: {link}"
