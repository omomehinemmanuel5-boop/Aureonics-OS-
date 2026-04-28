from fastapi import Depends, FastAPI, Request, Response

from lex_aureon.backend.common.middleware import enforce_org_scope
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, parse_mock_jwt
from lex_aureon.backend.events.bus import build_event, event_bus
from packages.contracts.schemas import EventType

app = FastAPI(title="Lex Aureon Audit Log Service", version="2.0.0")


@app.get("/audit")
def list_audit(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    rows = repository.list_logs(principal.organization_id)
    event_bus.publish(build_event(EventType.audit_logged, principal.organization_id, getattr(request.state, "request_id", "unknown"), getattr(request.state, "trace_id", "unknown"), {"count": len(rows)}, principal.user_id))
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
    lines = ["LEX AUREON COMPLIANCE AUDIT EXPORT", ""] + [f"[{row.created_at.isoformat()}] {row.id} :: {row.previous_hash} -> {row.immutable_hash}" for row in rows]
    return Response(content="\n".join(lines).encode("utf-8"), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=lex-aureon-audit.pdf"})
