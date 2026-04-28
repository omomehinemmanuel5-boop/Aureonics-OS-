from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from lex_aureon.backend.common.models import GovernanceResponse, IngestRequest, PolicyRecord


class AuditRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    organization_id: str
    user_id: str
    raw_output: str
    governed_output: str | None = None
    final_output: str | None = None
    trace: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    immutable_hash: str
    prev_hash: str | None = None


class MemoryRepository:
    def __init__(self) -> None:
        self.logs: dict[str, list[AuditRecord]] = {}
        self.policies: dict[str, PolicyRecord] = {}
        self.metrics: list[dict[str, Any]] = []
        self.org_last_hash: dict[str, str] = {}

    def _chain_hash(self, org_id: str, record_id: str, raw_output: str, ts: datetime) -> tuple[str, str | None]:
        prev_hash = self.org_last_hash.get(org_id)
        material = f"{prev_hash or 'genesis'}:{record_id}:{raw_output}:{ts.isoformat()}"
        digest = hashlib.sha256(material.encode()).hexdigest()
        self.org_last_hash[org_id] = digest
        return digest, prev_hash

    def create_log(self, payload: IngestRequest) -> AuditRecord:
        now = datetime.now(timezone.utc)
        log_id = str(uuid4())
        digest, prev_hash = self._chain_hash(payload.organization_id, log_id, payload.raw_output, now)
        record = AuditRecord(
            id=log_id,
            organization_id=payload.organization_id,
            user_id=payload.user_id,
            raw_output=payload.raw_output,
            trace={"model": payload.model_name, "metadata": payload.metadata, "prompt": payload.prompt},
            immutable_hash=digest,
            prev_hash=prev_hash,
            created_at=now,
        )
        self.logs[log_id] = [record]
        return record

    def append_governance(self, result: GovernanceResponse, org_id: str) -> AuditRecord:
        if result.log_id not in self.logs:
            raise KeyError("log not found")
        latest = self.logs[result.log_id][-1]
        now = datetime.now(timezone.utc)
        digest, prev_hash = self._chain_hash(org_id, result.log_id, result.final_output, now)
        appended = AuditRecord(
            id=result.log_id,
            organization_id=latest.organization_id,
            user_id=latest.user_id,
            raw_output=latest.raw_output,
            governed_output=result.governed_output,
            final_output=result.final_output,
            trace={**latest.trace, "governance": result.dict()},
            immutable_hash=digest,
            prev_hash=prev_hash,
            created_at=now,
        )
        self.logs[result.log_id].append(appended)
        return appended

    def get_log(self, log_id: str, org_id: str) -> AuditRecord | None:
        versions = self.logs.get(log_id)
        if not versions:
            return None
        latest = versions[-1]
        return latest if latest.organization_id == org_id else None

    def list_logs(self, organization_id: str) -> list[AuditRecord]:
        return [versions[-1] for versions in self.logs.values() if versions[-1].organization_id == organization_id]

    def upsert_policy(self, policy: PolicyRecord) -> PolicyRecord:
        policy.updated_at = datetime.now(timezone.utc)
        self.policies[policy.id] = policy
        return policy

    def list_policies(self, organization_id: str) -> list[PolicyRecord]:
        return [row for row in self.policies.values() if row.organization_id == organization_id]

    def get_policy(self, policy_id: str, organization_id: str) -> PolicyRecord | None:
        policy = self.policies.get(policy_id)
        if not policy or policy.organization_id != organization_id:
            return None
        return policy

    def delete_policy(self, policy_id: str, organization_id: str) -> bool:
        policy = self.get_policy(policy_id, organization_id)
        if not policy:
            return False
        self.policies.pop(policy_id)
        return True

    def add_metric(self, metric: dict[str, Any]) -> None:
        self.metrics.append(metric)

    def export_logs_csv(self, organization_id: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "created_at", "raw_output", "governed_output", "final_output", "immutable_hash", "prev_hash"])
        for row in self.list_logs(organization_id):
            writer.writerow([row.id, row.created_at.isoformat(), row.raw_output, row.governed_output or "", row.final_output or "", row.immutable_hash, row.prev_hash or ""])
        return output.getvalue()


repository = MemoryRepository()
