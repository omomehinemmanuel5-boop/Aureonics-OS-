from __future__ import annotations

from fastapi import HTTPException, Request

from .security import Principal


def enforce_org_scope(request: Request, principal: Principal, target_org_id: str | None = None) -> None:
    header_org = request.headers.get("x-org-id")
    org = target_org_id or header_org
    if not org:
        raise HTTPException(status_code=400, detail="Missing org context")
    if org != principal.organization_id:
        raise HTTPException(status_code=403, detail="org isolation violation")
