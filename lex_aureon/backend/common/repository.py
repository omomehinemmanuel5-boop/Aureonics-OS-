from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import AuditRecord, GovernanceResponse, IngestRequest, PolicyRecord


class MemoryRepository:
    def __init__(self) -> None:
        self.logs: dict[str, AuditRecord] = {}
        self.log_order: list[str] = []
        self.policies: dict[str, PolicyRecord] = {}
        self.metrics: list[dict[str, Any]] = []

    def create_log(self, payload: IngestRequest) -> AuditRecord:
        previous_hash = self.logs[self.log_order[-1]].immutable_hash if self.log_order else "GENESIS"
        record = AuditRecord(
            id=str(uuid4()),
            organization_id=payload.organization_id,
            user_id=payload.user_id,
            raw_output=payload.raw_output,
            trace={"model": payload.model_name, "metadata": payload.metadata, "prompt": payload.prompt},
            previous_hash=previous_hash,
        )
        record.immutable_hash = hashlib.sha256(
            f"{record.id}:{record.raw_output}:{record.created_at.isoformat()}:{previous_hash}".encode()
        ).hexdigest()
        self.logs[record.id] = record
        self.log_order.append(record.id)
        return record

    def append_governance_trace(self, result: GovernanceResponse) -> AuditRecord:
        row = self.logs[result.log_id]
        row.governed_output = result.governed_output
        row.final_output = result.final_output
        row.trace.setdefault("governance_history", []).append(result.dict())
        return row

    def get_log(self, log_id: str) -> AuditRecord | None:
        return self.logs.get(log_id)

    def list_logs(self, organization_id: str) -> list[AuditRecord]:
        return [self.logs[log_id] for log_id in self.log_order if self.logs[log_id].organization_id == organization_id]

    def upsert_policy(self, policy: PolicyRecord) -> PolicyRecord:
        policy.updated_at = datetime.now(timezone.utc)
        self.policies[policy.id] = policy
        return policy

    def list_policies(self, organization_id: str) -> list[PolicyRecord]:
        return [row for row in self.policies.values() if row.organization_id == organization_id]

    def delete_policy(self, policy_id: str) -> bool:
        return self.policies.pop(policy_id, None) is not None

    def add_metric(self, metric: dict[str, Any]) -> None:
        self.metrics.append(metric)

    def export_logs_csv(self, organization_id: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "created_at", "raw_output", "governed_output", "final_output", "previous_hash", "immutable_hash"])
        for row in self.list_logs(organization_id):
            writer.writerow([
                row.id,
                row.created_at.isoformat(),
                row.raw_output,
                row.governed_output or "",
                row.final_output or "",
                row.previous_hash or "",
                row.immutable_hash or "",
            ])
        return output.getvalue()


repository = MemoryRepository()
