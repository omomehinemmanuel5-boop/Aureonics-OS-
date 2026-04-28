from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EventType(str, Enum):
    ai_ingested = "AI_INGESTED"
    ai_governed = "AI_GOVERNED"
    policy_triggered = "POLICY_TRIGGERED"
    audit_logged = "AUDIT_LOGGED"
    degradation = "GOVERNANCE_DEGRADED"


class ServiceContext(BaseModel):
    request_id: str
    trace_id: str
    org_id: str
    user_id: str
    role: str


class IngestRequest(BaseModel):
    organization_id: str
    user_id: str
    model_name: str
    prompt: str | None = None
    raw_output: str = Field(min_length=1, max_length=20000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceRequest(BaseModel):
    log_id: str
    organization_id: str
    policy_version: str | None = None


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class GovernanceResponse(BaseModel):
    log_id: str
    raw_output: str
    governed_output: str
    final_output: str
    risk_score: float
    risk_level: RiskLevel
    risk_explanation: str
    meaning_preserved_score: float
    risk_reduction_score: float
    applied_policies: list[str] = Field(default_factory=list)
    fallback_mode: Literal["NONE", "PASS_THROUGH_SAFE"] = "NONE"


class PolicyRule(BaseModel):
    name: str
    description: str
    rule_type: str
    action: str
    severity: RiskLevel = RiskLevel.medium
    enabled: bool = True
    conditions: dict[str, Any] = Field(default_factory=dict)


class PolicyRecord(PolicyRule):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime


class EventEnvelope(BaseModel):
    event_type: EventType
    org_id: str
    request_id: str
    trace_id: str
    occurred_at: datetime
    payload: dict[str, Any]
