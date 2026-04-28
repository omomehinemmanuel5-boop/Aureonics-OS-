from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request

from lex_aureon.backend.common.middleware import enforce_org_scope
from lex_aureon.backend.common.models import PolicyRecord, PolicyRule
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, parse_mock_jwt, require_role
from lex_aureon.backend.events.bus import build_event, event_bus
from packages.contracts.schemas import EventType

app = FastAPI(title="Lex Aureon Policy Engine", version="2.0.0")


@app.get("/policy")
def list_policies(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    return repository.list_policies(principal.organization_id)


@app.post("/policy", response_model=PolicyRecord)
def create_policy(payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    require_role(principal, {"admin", "owner", "policy_admin"})
    record = PolicyRecord(organization_id=principal.organization_id, **payload.dict())
    saved = repository.upsert_policy(record)
    event_bus.publish(build_event(EventType.policy_triggered, principal.organization_id, getattr(request.state, "request_id", "unknown"), getattr(request.state, "trace_id", "unknown"), {"policy_id": saved.id}, principal.user_id))
    return saved


@app.put("/policy/{policy_id}", response_model=PolicyRecord)
def update_policy(policy_id: str, payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    require_role(principal, {"admin", "owner", "policy_admin"})
    existing = repository.policies.get(policy_id)
    if existing is None or existing.organization_id != principal.organization_id:
        raise HTTPException(status_code=404, detail="policy not found")
    existing.name = payload.name
    existing.description = payload.description
    existing.rule_type = payload.rule_type
    existing.action = payload.action
    existing.severity = payload.severity
    existing.enabled = payload.enabled
    existing.conditions = payload.conditions
    existing.updated_at = datetime.now(timezone.utc)
    saved = repository.upsert_policy(existing)
    event_bus.publish(build_event(EventType.policy_triggered, principal.organization_id, getattr(request.state, "request_id", "unknown"), getattr(request.state, "trace_id", "unknown"), {"policy_id": saved.id, "operation": "update"}, principal.user_id))
    return saved


@app.delete("/policy/{policy_id}")
def delete_policy(policy_id: str, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    require_role(principal, {"admin", "owner", "policy_admin"})
    if not repository.delete_policy(policy_id):
        raise HTTPException(status_code=404, detail="policy not found")
    return {"deleted": True}
