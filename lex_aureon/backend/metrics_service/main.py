from fastapi import Depends, FastAPI, Request

from lex_aureon.backend.common.middleware import enforce_org_scope
from lex_aureon.backend.common.repository import repository
from lex_aureon.backend.common.security import Principal, parse_mock_jwt

app = FastAPI(title="Lex Aureon Metrics Service", version="2.0.0")


@app.get("/metrics")
def get_metrics(request: Request, principal: Principal = Depends(parse_mock_jwt)):
    enforce_org_scope(request, principal)
    logs = repository.list_logs(principal.organization_id)
    scoped_metrics = [m for m in repository.metrics if repository.get_log(m.get("log_id", "")) and repository.get_log(m["log_id"]).organization_id == principal.organization_id]
    total = len(scoped_metrics)
    avg_risk_reduction = round(sum(m.get("risk_reduction", 0.0) for m in scoped_metrics) / total, 4) if total else 0.0
    avg_meaning = round(sum(m.get("meaning_preserved", 0.0) for m in scoped_metrics) / total, 4) if total else 0.0
    return {"organization_id": principal.organization_id, "total_logs": len(logs), "evaluated_logs": total, "risk_reduction_score": avg_risk_reduction, "meaning_preserved_score": avg_meaning, "governance_effectiveness": round((avg_risk_reduction * 0.7) + (avg_meaning * 0.3), 4)}
