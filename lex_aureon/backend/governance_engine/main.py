from __future__ import annotations

from datetime import datetime, timezone
from difflib import SequenceMatcher

from fastapi import Depends, FastAPI, HTTPException, Request

from lex_aureon.backend.common.circuit_breaker import CircuitBreaker
from lex_aureon.backend.common.event_bus import event_bus
from lex_aureon.backend.common.models import EventEnvelope, EventType, GovernanceRequest, GovernanceResponse, RiskLevel
from lex_aureon.backend.common.observability import install_observability_middleware
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, RateLimiter, parse_mock_jwt
from lex_aureon.backend.common.tenant import enforce_org_scope
from lex_aureon.backend.common.vector_memory import InMemoryVectorStore, MemoryItem
from lex_aureon.backend.governance_engine.core import governance_transform, risk_score

app = FastAPI(title="Lex Aureon Governance Engine", version="1.1.0")
install_observability_middleware(app)
limiter = RateLimiter(240)
memory = InMemoryVectorStore()
breaker = CircuitBreaker()


def embed(text: str) -> list[float]:
    buckets = [0.0] * 16
    for idx, char in enumerate(text.lower()[:512]):
        buckets[idx % 16] += (ord(char) % 31) / 31
    return buckets


@app.post("/govern", response_model=GovernanceResponse)
def govern(payload: GovernanceRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    row = repository.get_log(payload.log_id, principal.organization_id)
    if row is None:
        raise HTTPException(status_code=404, detail="log not found")

    raw = row.raw_output

    def _run_governance() -> GovernanceResponse:
        score = risk_score(raw)
        governed, matches = governance_transform(raw)
        similarity = SequenceMatcher(None, raw, governed).ratio()
        meaning = round(similarity, 4)
        reduction = round(max(0.0, score - (score * meaning * 0.4)), 4)
        level = RiskLevel.low if score <= 0.25 else RiskLevel.medium if score <= 0.55 else RiskLevel.high if score <= 0.8 else RiskLevel.critical
        explanation = "No risky patterns matched" if not matches else f"Matched risky terms: {', '.join(sorted(matches))}"
        return GovernanceResponse(
            log_id=row.id,
            raw_output=raw,
            governed_output=governed,
            final_output=governed,
            risk_score=score,
            risk_level=level,
            risk_explanation=explanation,
            meaning_preserved_score=meaning,
            risk_reduction_score=reduction,
            applied_policies=["default-risk-keyword-policy"] if matches else [],
            fallback_mode="NONE",
        )

    def _fallback() -> GovernanceResponse:
        event_bus.publish(
            EventEnvelope(
                event_type=EventType.degradation,
                org_id=principal.organization_id,
                request_id=request.state.request_id,
                trace_id=request.state.trace_id,
                occurred_at=datetime.now(timezone.utc),
                payload={"mode": "PASS_THROUGH_SAFE", "log_id": row.id},
            )
        )
        return GovernanceResponse(
            log_id=row.id,
            raw_output=raw,
            governed_output=raw,
            final_output=raw,
            risk_score=0.0,
            risk_level=RiskLevel.low,
            risk_explanation="Governance degraded; pass-through safe mode enabled",
            meaning_preserved_score=1.0,
            risk_reduction_score=0.0,
            applied_policies=[],
            fallback_mode="PASS_THROUGH_SAFE",
        )

    result = breaker.execute(_run_governance, _fallback)
    repository.append_governance(result, principal.organization_id)

    memory.add(MemoryItem(id=row.id, organization_id=row.organization_id, raw_output=raw, correction=result.governed_output, embedding=embed(raw)))
    neighbors = memory.similar(row.organization_id, embed(raw), k=3)
    repository.add_metric({"log_id": row.id, "risk_reduction": result.risk_reduction_score, "meaning_preserved": result.meaning_preserved_score, "neighbors": neighbors})
    event_bus.publish(
        EventEnvelope(
            event_type=EventType.ai_governed,
            org_id=principal.organization_id,
            request_id=request.state.request_id,
            trace_id=request.state.trace_id,
            occurred_at=datetime.now(timezone.utc),
            payload={"log_id": row.id, "risk_score": result.risk_score},
        )
    )
    return result
