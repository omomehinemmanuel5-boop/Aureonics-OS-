from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DealStage(str, Enum):
    LEAD_IDENTIFICATION = "lead_identification"
    STAKEHOLDER_MAPPING = "stakeholder_mapping"
    TECHNICAL_QUALIFICATION = "technical_qualification"
    BUSINESS_CASE_ALIGNMENT = "business_case_alignment"
    SECURITY_COMPLIANCE_REVIEW = "security_compliance_review"
    PROCUREMENT_PREPARATION = "procurement_preparation"
    NEGOTIATION_SUPPORT = "negotiation_support"
    CLOSE = "close"
    POST_CLOSE_HANDOFF = "post_close_handoff"


@dataclass
class Stakeholder:
    name: str
    role: str
    email: str
    engagement: float = 0.0
    objections: list[str] = field(default_factory=list)


@dataclass
class DealContext:
    deal_id: str
    account_name: str
    stage: DealStage = DealStage.LEAD_IDENTIFICATION
    stakeholders: dict[str, Stakeholder] = field(default_factory=dict)
    value_estimate: float = 0.0
    close_probability: float = 0.1
    risks: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)

    def add_history(self, event: str, payload: dict[str, Any]) -> None:
        self.history.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "payload": payload,
            }
        )
