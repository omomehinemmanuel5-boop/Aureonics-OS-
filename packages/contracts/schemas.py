from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    ai_ingested = "AI_INGESTED"
    ai_governed = "AI_GOVERNED"
    policy_triggered = "POLICY_TRIGGERED"
    audit_logged = "AUDIT_LOGGED"
    governance_degraded = "GOVERNANCE_DEGRADED"


class IngestRequestContract(BaseModel):
    organization_id: str = Field(min_length=3)
    user_id: str = Field(min_length=3)
    model_name: str
    raw_output: str = Field(min_length=1, max_length=20000)
    prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceRequestContract(BaseModel):
    log_id: str
    organization_id: str
    policy_version: str | None = None


class GovernanceResponseContract(BaseModel):
    log_id: str
    raw_output: str
    governed_output: str
    final_output: str
    risk_score: float
    risk_explanation: str
    risk_reduction_score: float
    meaning_preserved_score: float
    applied_policies: list[str] = Field(default_factory=list)


class PolicyContract(BaseModel):
    id: str | None = None
    organization_id: str
    name: str
    description: str
    rule_type: str
    action: str
    severity: str
    enabled: bool = True
    conditions: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    event_type: EventType
    organization_id: str
    actor_id: str | None = None
    request_id: str
    trace_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime


# Backward-compatibility aliases expected by downstream tests/services.
IngestRequest = IngestRequestContract
GovernanceRequest = GovernanceRequestContract
