from __future__ import annotations

import json
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request


def configure_json_logging() -> logging.Logger:
    logger = logging.getLogger("lex_aureon")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        logger.addHandler(handler)
    return logger


def log_json(logger: logging.Logger, level: str, message: str, **fields: object) -> None:
    payload = {"level": level, "message": message, **fields}
    logger.info(json.dumps(payload, default=str))


def install_observability_middleware(app: FastAPI) -> None:
    logger = configure_json_logging()

    @app.middleware("http")
    async def _middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        trace_id = request.headers.get("x-trace-id") or request_id
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        started = time.time()
        response = await call_next(request)
        latency_ms = round((time.time() - started) * 1000, 2)
        response.headers["x-request-id"] = request_id
        response.headers["x-trace-id"] = trace_id
        log_json(
            logger,
            "INFO",
            "request_completed",
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            request_id=request_id,
            trace_id=trace_id,
            latency_ms=latency_ms,
        )
        return response
