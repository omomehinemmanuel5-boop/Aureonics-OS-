from fastapi import Depends, FastAPI, Request

from lex_aureon.backend.common.middleware import enforce_org_scope
from lex_aureon.backend.common.models import IngestRequest
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, RateLimiter, parse_mock_jwt
from lex_aureon.backend.events.bus import build_event, event_bus
from packages.contracts.schemas import EventType

app = FastAPI(title="Lex Aureon Ingestion Service", version="2.0.0")
limiter = RateLimiter(240)


@app.post("/ingest")
def ingest(payload: IngestRequest, request: Request, principal: Principal = Depends(parse_mock_jwt)):
    limiter.check(f"{principal.organization_id}:{principal.user_id}")
    enforce_org_scope(request, principal, payload.organization_id)
    if principal.user_id != payload.user_id:
        return {"error": "token scope mismatch"}

    record = repository.create_log(payload)
    event_bus.publish(
        build_event(
            EventType.ai_ingested,
            organization_id=record.organization_id,
            request_id=getattr(request.state, "request_id", "unknown"),
            trace_id=getattr(request.state, "trace_id", "unknown"),
            actor_id=principal.user_id,
            payload={"log_id": record.id},
        )
    )
    return {"log_id": record.id, "immutable_hash": record.immutable_hash, "previous_hash": record.previous_hash, "created_at": record.created_at}
