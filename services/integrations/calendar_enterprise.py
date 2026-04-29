class CalendarEnterprise:
    def book_demo(self, attendees: list[str], slot_iso: str) -> dict:
        return {"attendees": attendees, "slot": slot_iso, "status": "held"}
