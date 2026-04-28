from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import Request

logger = logging.getLogger("lex_aureon")
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def request_context(request: Request) -> tuple[str, str]:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    request.state.trace_id = trace_id
    return request_id, trace_id


def log_json(level: str, message: str, **fields: object) -> None:
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "message": message, **fields}
    getattr(logger, level, logger.info)(json.dumps(payload, default=str))
