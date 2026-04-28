from __future__ import annotations

from fastapi import Header, HTTPException, Request

from lex_aureon.backend.common.security import Principal


def enforce_org_scope(request: Request, principal: Principal, x_org_id: str | None = Header(default=None)) -> None:
    route_org_id = x_org_id or request.headers.get("x-org-id")
    if not route_org_id:
        raise HTTPException(status_code=400, detail="Missing x-org-id header")
    if route_org_id != principal.organization_id:
        raise HTTPException(status_code=403, detail="Cross-org access denied")
