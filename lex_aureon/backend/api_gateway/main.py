from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from lex_aureon.backend.audit_log_service.main import list_audit
from lex_aureon.backend.common.config import validate_env
from lex_aureon.backend.common.models import BillingPlan, GovernanceRequest, IngestRequest, PolicyRule
from lex_aureon.backend.common.observability import install_observability_middleware
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, RateLimiter, parse_mock_jwt, validate_stripe_signature
from lex_aureon.backend.common.tenant import enforce_org_scope
from lex_aureon.backend.governance_engine.main import govern
from lex_aureon.backend.ingestion_service.main import ingest
from lex_aureon.backend.metrics_service.main import get_metrics
from lex_aureon.backend.policy_engine.main import create_policy, delete_policy, list_policies, update_policy

app = FastAPI(title="Lex Aureon API Gateway", version="1.1.0")
install_observability_middleware(app)
limiter = RateLimiter(180)


@app.on_event("startup")
def startup_validation() -> None:
    missing = validate_env()
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def policy_enforcement_hook(principal: Principal) -> None:
    if principal.role == "suspended":
        raise HTTPException(status_code=403, detail="Organization suspended")


@app.post("/ingest")
def ingest_route(payload: IngestRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    policy_enforcement_hook(principal)
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    return ingest(payload, request, principal)


@app.post("/govern")
def govern_route(payload: GovernanceRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    policy_enforcement_hook(principal)
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    return govern(payload, request, principal)


@app.get("/audit")
def audit_route(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    return list_audit(request, principal)


@app.get("/policy")
def list_policy_route(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    return list_policies(request, principal)


@app.post("/policy")
def create_policy_route(payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    return create_policy(payload, request, principal)


@app.put("/policy/{policy_id}")
def update_policy_route(policy_id: str, payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    return update_policy(policy_id, payload, request, principal)


@app.delete("/policy/{policy_id}")
def delete_policy_route(policy_id: str, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    return delete_policy(policy_id, request, principal)


@app.get("/metrics")
def metrics_route(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    return get_metrics(request, principal)


@app.post("/billing/stripe/webhook")
async def stripe_webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("stripe-signature")
    if not validate_stripe_signature(raw, sig):
        return JSONResponse(status_code=400, content={"ok": False, "error": "invalid signature"})

    event = json.loads(raw.decode("utf-8"))
    event_type = event.get("type")
    if event_type == "checkout.session.completed":
        metadata = event.get("data", {}).get("object", {}).get("metadata", {})
        org_id = metadata.get("organization_id")
        plan = metadata.get("plan", BillingPlan.enterprise.value)
        repository.add_metric({"organization_id": org_id, "billing_event": "provisioned", "plan": plan, "received_at": datetime.now(timezone.utc).isoformat()})
    return {"ok": True}
