#!/usr/bin/env python3
"""Check whether backend is connected to external Next.js frontend."""
from __future__ import annotations

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def _fetch_json(url: str) -> dict:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _probe_redirect(url: str) -> tuple[int | None, str | None]:
    req = Request(url, headers={"Accept": "text/html"})
    try:
        with urlopen(req, timeout=10) as resp:
            return getattr(resp, "status", 200), resp.geturl()
    except HTTPError as exc:
        return exc.code, exc.headers.get("Location")
    except URLError:
        return None, None


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_frontend_connection.py <backend_base_url>")
        return 2

    base = sys.argv[1].rstrip("/")
    try:
        payload = _fetch_json(f"{base}/frontend/status")
    except Exception as exc:  # pragma: no cover - network/runtime variability
        print(f"ERROR: failed to query {base}/frontend/status: {exc}")
        return 1

    mode = payload.get("mode")
    connected = mode == "external_nextjs"
    print(json.dumps(payload, indent=2))
    home_status, home_target = _probe_redirect(f"{base}/")
    dash_status, dash_target = _probe_redirect(f"{base}/dashboard")
    print(f"\nRoute probe / -> status={home_status}, target={home_target}")
    print(f"Route probe /dashboard -> status={dash_status}, target={dash_target}")

    if connected:
        print("\nCONNECTED: external Next.js frontend is active.")
        return 0

    print("\nNOT CONNECTED: backend is serving embedded static frontend.")
    print("Set LEX_FRONTEND_BASE_URL in deployment environment to connect external frontend.")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
