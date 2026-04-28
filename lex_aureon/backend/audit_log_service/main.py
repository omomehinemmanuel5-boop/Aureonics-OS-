from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request, Response

from lex_aureon.backend.common.event_bus import event_bus
from lex_aureon.backend.common.models import EventEnvelope, EventType
from lex_aureon.backend.common.observability import install_observability_middleware
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, parse_mock_jwt
from lex_aureon.backend.common.tenant import enforce_org_scope

app = FastAPI(title="Lex Aureon Audit Log Service", version="1.1.0")
install_observability_middleware(app)


@app.get("/audit")
def list_audit(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    rows = repository.list_logs(principal.organization_id)
    event_bus.publish(
        EventEnvelope(
            event_type=EventType.audit_logged,
            org_id=principal.organization_id,
            request_id=request.state.request_id,
            trace_id=request.state.trace_id,
            occurred_at=datetime.now(timezone.utc),
            payload={"count": len(rows)},
        )
    )
    return rows


@app.get("/audit/export/csv")
def export_audit_csv(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    csv_blob = repository.export_logs_csv(principal.organization_id)
    return Response(content=csv_blob, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=lex-aureon-audit.csv"})


@app.get("/audit/export/pdf")
def export_audit_pdf(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    rows = repository.list_logs(principal.organization_id)
    lines = ["LEX AUREON COMPLIANCE AUDIT EXPORT", ""]
    for row in rows:
        lines.append(f"[{row.created_at.isoformat()}] {row.id} :: {row.prev_hash} -> {row.immutable_hash}")
    fake_pdf_payload = "\n".join(lines).encode("utf-8")
    return Response(content=fake_pdf_payload, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=lex-aureon-audit.pdf"})
