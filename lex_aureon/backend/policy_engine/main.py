from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request

from lex_aureon.backend.common.event_bus import event_bus
from lex_aureon.backend.common.models import EventEnvelope, EventType, PolicyRecord, PolicyRule
from lex_aureon.backend.common.observability import install_observability_middleware
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, parse_mock_jwt, require_role
from lex_aureon.backend.common.tenant import enforce_org_scope

app = FastAPI(title="Lex Aureon Policy Engine", version="1.1.0")
install_observability_middleware(app)


@app.get("/policy")
def list_policies(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    return repository.list_policies(principal.organization_id)


@app.post("/policy", response_model=PolicyRecord)
def create_policy(payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    require_role(principal, {"admin", "owner", "policy_admin"})
    now = datetime.now(timezone.utc)
    record = PolicyRecord(id=str(uuid4()), organization_id=principal.organization_id, created_at=now, updated_at=now, **payload.dict())
    saved = repository.upsert_policy(record)
    event_bus.publish(
        EventEnvelope(
            event_type=EventType.policy_triggered,
            org_id=principal.organization_id,
            request_id=request.state.request_id,
            trace_id=request.state.trace_id,
            occurred_at=now,
            payload={"policy_id": saved.id, "action": "created"},
        )
    )
    return saved


@app.put("/policy/{policy_id}", response_model=PolicyRecord)
def update_policy(policy_id: str, payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    require_role(principal, {"admin", "owner", "policy_admin"})
    existing = repository.get_policy(policy_id, principal.organization_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="policy not found")
    for field, value in payload.dict().items():
        setattr(existing, field, value)
    existing.updated_at = datetime.now(timezone.utc)
    return repository.upsert_policy(existing)


@app.delete("/policy/{policy_id}")
def delete_policy(policy_id: str, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    require_role(principal, {"admin", "owner", "policy_admin"})
    if not repository.delete_policy(policy_id, principal.organization_id):
        raise HTTPException(status_code=404, detail="policy not found")
    return {"deleted": True}
