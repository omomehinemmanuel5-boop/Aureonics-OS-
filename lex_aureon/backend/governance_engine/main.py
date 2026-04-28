from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request

from lex_aureon.backend.common.middleware import enforce_org_scope
from lex_aureon.backend.common.models import GovernanceRequest, GovernanceResponse, RiskLevel
from lex_aureon.backend.common.observability import log_json
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, RateLimiter, parse_mock_jwt
from lex_aureon.backend.common.vector_memory import InMemoryVectorStore, MemoryItem
from lex_aureon.backend.events.bus import build_event, event_bus
from lex_aureon.backend.governance_engine.core import governance_transform, meaning_preserved, risk_score
from packages.contracts.schemas import EventType

app = FastAPI(title="Lex Aureon Governance Engine", version="2.0.0")
limiter = RateLimiter(240)
memory = InMemoryVectorStore()


@app.post("/govern", response_model=GovernanceResponse)
def govern(payload: GovernanceRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    enforce_org_scope(request, principal, payload.organization_id)

    row = repository.get_log(payload.log_id)
    if row is None:
        raise HTTPException(status_code=404, detail="log not found")
    if row.organization_id != principal.organization_id:
        raise HTTPException(status_code=403, detail="cross-tenant access denied")

    raw = row.raw_output
    policy = {"action": "redact"}

    try:
        score = risk_score(raw)
        governed = governance_transform(raw, policy)
    except Exception as exc:  # circuit breaker path
        log_json("error", "governance engine failed, entering safe fallback", error=str(exc), log_id=row.id)
        governed = raw
        score = 0.0
        event_bus.publish(
            build_event(
                EventType.governance_degraded,
                organization_id=row.organization_id,
                request_id=getattr(request.state, "request_id", "unknown"),
                trace_id=getattr(request.state, "trace_id", "unknown"),
                actor_id=principal.user_id,
                payload={"mode": "PASS_THROUGH_SAFE", "log_id": row.id},
            )
        )

    meaning = meaning_preserved(raw, governed)
    reduction = round(max(0.0, score - (score * meaning * 0.4)), 4)
    explanation = "No risky patterns matched" if raw == governed else "Deterministic governance transform applied"
    level = RiskLevel.low if score <= 0.25 else RiskLevel.medium if score <= 0.55 else RiskLevel.high if score <= 0.8 else RiskLevel.critical

    result = GovernanceResponse(
        log_id=row.id,
        raw_output=raw,
        governed_output=governed,
        final_output=governed,
        risk_score=score,
        risk_level=level,
        risk_explanation=explanation,
        meaning_preserved_score=meaning,
        risk_reduction_score=reduction,
        applied_policies=["deterministic-redaction-policy"],
    )

    repository.append_governance_trace(result)
    memory.add(MemoryItem(id=row.id, organization_id=row.organization_id, raw_output=raw, correction=governed, embedding=[score] * 16))
    repository.add_metric({"log_id": row.id, "risk_reduction": reduction, "meaning_preserved": meaning})

    event_bus.publish(
        build_event(
            EventType.ai_governed,
            organization_id=row.organization_id,
            request_id=getattr(request.state, "request_id", "unknown"),
            trace_id=getattr(request.state, "trace_id", "unknown"),
            actor_id=principal.user_id,
            payload={"log_id": row.id, "risk_score": score},
        )
    )
    return result
