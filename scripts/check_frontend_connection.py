#!/usr/bin/env python3
"""Check whether backend is connected to external Next.js frontend."""
from __future__ import annotations

import json
import sys
from urllib.request import urlopen, Request


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_frontend_connection.py <backend_base_url>")
        return 2

    base = sys.argv[1].rstrip("/")
    req = Request(f"{base}/frontend/status", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network/runtime variability
        print(f"ERROR: failed to query {base}/frontend/status: {exc}")
        return 1

    mode = payload.get("mode")
    connected = mode == "external_nextjs"
    print(json.dumps(payload, indent=2))
    if connected:
        print("\nCONNECTED: external Next.js frontend is active.")
        return 0

    print("\nNOT CONNECTED: backend is serving embedded static frontend.")
    print("Set LEX_FRONTEND_BASE_URL in deployment environment to connect external frontend.")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
