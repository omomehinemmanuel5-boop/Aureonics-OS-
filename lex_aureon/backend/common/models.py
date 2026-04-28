from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from packages.contracts.schemas import GovernanceRequestContract, GovernanceResponseContract, IngestRequestContract


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IngestRequest(IngestRequestContract):
    pass


class GovernanceRequest(GovernanceRequestContract):
    pass


class GovernanceResponse(GovernanceResponseContract):
    risk_level: RiskLevel


class PolicyRule(BaseModel):
    name: str
    description: str
    rule_type: str
    action: str
    severity: RiskLevel = RiskLevel.medium
    enabled: bool = True
    conditions: dict[str, Any] = Field(default_factory=dict)


class PolicyRecord(PolicyRule):
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    user_id: str
    raw_output: str
    governed_output: str | None = None
    final_output: str | None = None
    trace: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    immutable_hash: str | None = None
    previous_hash: str | None = None


class BillingPlan(str, Enum):
    developer = "developer"
    team = "team"
    enterprise = "enterprise"
