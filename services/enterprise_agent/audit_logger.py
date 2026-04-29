from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from services.compliance.logging_policy import REQUIRED_AUDIT_FIELDS


@dataclass
class AuditEvent:
    deal_id: str
    actor: str
    action: str
    reason: str
    compliance_status: str
    metadata: dict
    timestamp: str | None = None


class AuditLogger:
    def __init__(self) -> None:
        self._events: list[dict] = []

    def log(self, event: AuditEvent) -> dict:
        payload = asdict(event)
        payload["timestamp"] = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
        missing = REQUIRED_AUDIT_FIELDS - payload.keys()
        if missing:
            raise ValueError(f"missing audit fields: {missing}")
        self._events.append(payload)
        return payload

    def events(self) -> list[dict]:
        return list(self._events)
