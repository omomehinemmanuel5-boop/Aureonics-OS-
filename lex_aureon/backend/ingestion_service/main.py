from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request

from lex_aureon.backend.common.event_bus import event_bus
from lex_aureon.backend.common.models import EventEnvelope, EventType, IngestRequest
from lex_aureon.backend.common.observability import install_observability_middleware
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, RateLimiter, parse_mock_jwt
from lex_aureon.backend.common.tenant import enforce_org_scope

app = FastAPI(title="Lex Aureon Ingestion Service", version="1.1.0")
install_observability_middleware(app)
limiter = RateLimiter(240)


@app.post("/ingest")
def ingest(payload: IngestRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    if principal.organization_id != payload.organization_id or principal.user_id != payload.user_id:
        raise HTTPException(status_code=403, detail="token scope mismatch")
    record = repository.create_log(payload)
    event_bus.publish(
        EventEnvelope(
            event_type=EventType.ai_ingested,
            org_id=principal.organization_id,
            request_id=request.state.request_id,
            trace_id=request.state.trace_id,
            occurred_at=datetime.now(timezone.utc),
            payload={"log_id": record.id},
        )
    )
    return {"log_id": record.id, "immutable_hash": record.immutable_hash, "prev_hash": record.prev_hash, "created_at": record.created_at}
