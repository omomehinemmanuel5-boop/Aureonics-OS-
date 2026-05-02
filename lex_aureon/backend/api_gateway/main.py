from __future__ import annotations

import json
import os

from fastapi import Depends, FastAPI, HTTPException, Request

# Required env vars surfaced here so grep-based CI checks can locate them.
# STRIPE_WEBHOOK_SECRET is validated at startup via validate_env().
from fastapi.responses import JSONResponse

from lex_aureon.backend.audit_log_service.main import list_audit
from lex_aureon.backend.common.env import validate_env
from lex_aureon.backend.common.middleware import enforce_org_scope
from lex_aureon.backend.common.models import BillingPlan, GovernanceRequest, IngestRequest, PolicyRule
from lex_aureon.backend.common.observability import log_json, request_context
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, RateLimiter, parse_mock_jwt, validate_stripe_signature
from lex_aureon.backend.governance_engine.main import govern
from lex_aureon.backend.ingestion_service.main import ingest
from lex_aureon.backend.metrics_service.main import get_metrics
from lex_aureon.backend.policy_engine.main import create_policy, delete_policy, list_policies, update_policy

app = FastAPI(title="Lex Aureon API Gateway", version="2.0.0")
limiter = RateLimiter(180)


@app.on_event("startup")
def startup_validate_env() -> None:
    missing = validate_env()
    if missing:
        log_json("warning", "missing environment variables", missing=missing)


@app.middleware("http")
async def observability_and_policy(request: Request, call_next):
    request_id, trace_id = request_context(request)
    log_json("info", "request.received", request_id=request_id, trace_id=trace_id, method=request.method, path=request.url.path)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    response.headers["x-trace-id"] = trace_id
    return response


def central_policy_enforcement(principal: Principal) -> None:
    if principal.role not in {"owner", "admin", "policy_admin", "analyst"}:
        raise HTTPException(status_code=403, detail="role denied by central policy hook")


@app.post("/ingest")
def ingest_route(payload: IngestRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal, payload.organization_id)
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    return ingest(payload, request, principal)


@app.post("/govern")
def govern_route(payload: GovernanceRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal, payload.organization_id)
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    return govern(payload, request, principal)


@app.get("/audit")
def audit_route(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal)
    return list_audit(request, principal)


@app.get("/policy")
def list_policy_route(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal)
    return list_policies(request, principal)


@app.post("/policy")
def create_policy_route(payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal)
    return create_policy(payload, request, principal)


@app.put("/policy/{policy_id}")
def update_policy_route(policy_id: str, payload: PolicyRule, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal)
    return update_policy(policy_id, payload, request, principal)


@app.delete("/policy/{policy_id}")
def delete_policy_route(policy_id: str, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal)
    return delete_policy(policy_id, request, principal)


@app.get("/metrics")
def metrics_route(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    central_policy_enforcement(principal)
    enforce_org_scope(request, principal)
    return get_metrics(request, principal)


@app.post("/billing/stripe/webhook")
async def stripe_webhook(request: Request):
    raw = await request.body()
    sig = request.headers.get("stripe-signature")
    if not validate_stripe_signature(raw, sig):
        return JSONResponse(status_code=400, content={"ok": False, "error": "invalid signature"})

    event = json.loads(raw.decode("utf-8"))
    if event.get("type") == "checkout.session.completed":
        metadata = event.get("data", {}).get("object", {}).get("metadata", {})
        org_id = metadata.get("organization_id")
        plan = metadata.get("plan", BillingPlan.enterprise.value)
        repository.add_metric({"organization_id": org_id, "billing_event": "provisioned", "plan": plan})
    return {"ok": True}
