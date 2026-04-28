from __future__ import annotations

import hashlib
import hmac
import os
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass
class Principal:
    user_id: str
    organization_id: str
    role: str


class RateLimiter:
    def __init__(self, requests_per_minute: int = 120) -> None:
        self.requests_per_minute = requests_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.time()
        window = now - 60
        hits = [stamp for stamp in self._hits[key] if stamp >= window]
        if len(hits) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        hits.append(now)
        self._hits[key] = hits


def parse_mock_jwt(authorization: str | None = Header(default=None)) -> Principal:
    """Lightweight auth stub for scaffold.

    Expected header format: Bearer user_id:org_id:role
    """

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    parts = token.split(":")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail="Invalid token format")
    return Principal(user_id=parts[0], organization_id=parts[1], role=parts[2])


def require_role(principal: Principal, allowed: set[str]) -> None:
    if principal.role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient role")


def validate_stripe_signature(payload: bytes, sig_header: str | None, secret: str | None = None) -> bool:
    secret = secret or os.getenv("STRIPE_WEBHOOK_SECRET", "dev-secret")
    if not sig_header:
        return False
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, sig_header)
