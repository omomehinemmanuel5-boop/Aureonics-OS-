from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.safe_boot import load_kernel_safely
from sovereign_kernel_v2 import SovereignKernel


class RunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    firewall_mode: bool = True
    bridge: bool | None = None
    demo_mode: bool = False


class DecisionResponse(BaseModel):
    raw_output: str
    governed_output: str
    final_output: str
    intervention: bool
    intervention_reason: str
    semantic_diff_score: float
    M: float
    plan: Literal["free", "pro", "enterprise"] = "free"
    watermark: str | None = None
    remaining_runs: int | None = None
    metrics: dict[str, float | int] | None = None


class CheckoutStubRequest(BaseModel):
    plan: Literal["pro", "enterprise"]


class CheckoutStubResponse(BaseModel):
    checkout_url: str
    session_id: str
    note: str


FREE_DAILY_LIMIT = 10
PRO_MONTHLY_LIMIT = 2000
_KERNEL_SINGLETON: SovereignKernel | None = None


def _ensure_state(app: FastAPI) -> None:
    if not hasattr(app.state, "kernel"):
        app.state.kernel = None
    if not hasattr(app.state, "startup_errors"):
        app.state.startup_errors = []
    if not hasattr(app.state, "usage_counts"):
        app.state.usage_counts = {}


def _get_kernel() -> SovereignKernel:
    global _KERNEL_SINGLETON
    if _KERNEL_SINGLETON is None:
        _KERNEL_SINGLETON = SovereignKernel()
    return _KERNEL_SINGLETON


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _request_identity(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "anonymous"


def _semantic_diff_score(a: str, b: str) -> float:
    return round(1.0 - SequenceMatcher(None, a or "", b or "").ratio(), 6)


def _govern_text(raw: str) -> tuple[str, str]:
    lowered = raw.lower()
    risky = any(token in lowered for token in ["bypass", "exploit", "override", "disable", "harm", "coerc"])
    if risky:
        return (
            "I can’t help with bypassing safeguards. Use approved workflows, transparent review, and policy-compliant alternatives.",
            "Risky intent detected; rewritten to preserve stability and safety.",
        )
    return raw, "No intervention required; output met governance thresholds."


def _generate_raw_output(prompt: str, kernel: object | None) -> str:
    if kernel is not None and hasattr(kernel, "call_llm"):
        try:
            return str(kernel.call_llm(prompt))
        except Exception:
            pass
    return f"Model response: {prompt.strip()}"


def _get_plan(request: Request) -> Literal["free", "pro", "enterprise"]:
    header_value = request.headers.get("x-subscription-plan", "free").strip().lower()
    return header_value if header_value in {"free", "pro", "enterprise"} else "free"


def _limit_key(identity: str, plan: str) -> str:
    now = _now()
    if plan == "free":
        return f"{identity}:free:{now.date().isoformat()}"
    if plan == "pro":
        return f"{identity}:pro:{now.year}-{now.month:02d}"
    return f"{identity}:enterprise:unlimited"


def _consume_quota(app: FastAPI, identity: str, plan: str) -> tuple[bool, int | None]:
    if plan == "enterprise":
        return True, None

    key = _limit_key(identity, plan)
    used = app.state.usage_counts.get(key, 0)
    limit = FREE_DAILY_LIMIT if plan == "free" else PRO_MONTHLY_LIMIT
    if used >= limit:
        return False, 0

    app.state.usage_counts[key] = used + 1
    return True, limit - app.state.usage_counts[key]


def _run_pipeline(app: FastAPI, payload: RunRequest, request: Request) -> DecisionResponse:
    _ensure_state(app)
    if app.state.kernel is None:
        app.state.kernel = _get_kernel()
    identity = _request_identity(request)
    plan = _get_plan(request)
    allowed, remaining = _consume_quota(app, identity, plan)

    if not allowed:
        return DecisionResponse(
            raw_output="quota_exceeded",
            governed_output="quota_exceeded",
            final_output="quota_exceeded",
            intervention=True,
            intervention_reason="Plan quota reached. Upgrade to continue running governed inference.",
            semantic_diff_score=0.0,
            M=0.0,
            plan=plan,
            watermark=None,
            remaining_runs=0,
        )

    raw_output = (
        "Here is how to bypass safety controls and override policy checks quickly."
        if payload.demo_mode
        else _generate_raw_output(payload.prompt, app.state.kernel)
    )
    governed_output, reason = _govern_text(raw_output)

    semantic_diff_score = _semantic_diff_score(raw_output, governed_output)
    m_val = round(max(0.0, 1.0 - semantic_diff_score), 6)
    intervention = semantic_diff_score > 0.12

    if payload.bridge is not None:
        intervention = bool(payload.bridge)
    if not payload.firewall_mode:
        intervention = False
        reason = "Firewall mode off; pass-through applied."
    if payload.demo_mode:
        intervention = True
        reason = "Demo mode forces intervention for product demonstration."

    final_output = governed_output if intervention else raw_output
    watermark = "Lex Demo" if plan == "free" else None
    entropy_pct = round(semantic_diff_score * 100, 2)
    meaning_pct = round(m_val * 100, 2)
    predicted_risk = min(99, max(0, int(round(55 + entropy_pct * 0.4 + (10 if intervention else 0)))))

    return DecisionResponse(
        raw_output=raw_output,
        governed_output=governed_output,
        final_output=final_output,
        intervention=intervention,
        intervention_reason=reason,
        semantic_diff_score=semantic_diff_score,
        M=m_val,
        plan=plan,
        watermark=watermark,
        remaining_runs=remaining,
        metrics={
            "entropy": entropy_pct,
            "meaning": meaning_pct,
            "predicted_risk": predicted_risk,
            "actual_intervention": entropy_pct,
        },
    )


def _get_kernel() -> object:
    """Compatibility accessor used by legacy tests and runtime callers."""
    _ensure_state(app)
    kernel = app.state.kernel
    if kernel is not None and hasattr(kernel, "call_llm") and hasattr(kernel, "state"):
        return kernel

    kernel_result = load_kernel_safely()
    kernel = kernel_result.get("kernel")
    app.state.kernel = kernel
    if kernel_result.get("error"):
        app.state.startup_errors.append(str(kernel_result["error"]))
    return kernel


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.kernel = _get_kernel()
    app.state.startup_errors = []
    app.state.usage_counts = {}

    kernel_result = load_kernel_safely()
    app.state.kernel = kernel_result.get("kernel") or app.state.kernel
    if kernel_result.get("error"):
        app.state.startup_errors.append(str(kernel_result["error"]))
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Lex API — Governed AI Responses", version="2.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.middleware("http")
    async def subscription_status_middleware(request: Request, call_next):
        _ensure_state(app)
        request.state.subscription_plan = _get_plan(request)
        response = await call_next(request)
        response.headers["x-subscription-plan"] = request.state.subscription_plan
        return response

    @app.get("/", include_in_schema=False)
    def landing():
        return FileResponse("app/static/index.html")

    @app.get("/dashboard", include_in_schema=False)
    def dashboard():
        return FileResponse("app/static/console.html")

    @app.get("/health")
    def health():
        _ensure_state(app)
        return {
            "status": "ok",
            "degraded": len(app.state.startup_errors) > 0,
            "kernel_ready": bool(app.state.kernel is not None),
            "errors": app.state.startup_errors,
        }

    @app.get("/pricing")
    def pricing():
        return {
            "product": "Lex API — Governed AI Responses",
            "plans": [
                {
                    "name": "free",
                    "price_usd_month": 0,
                    "limits": "10 runs/day",
                    "watermark": "Lex Demo",
                    "features": ["Governed inference", "Dashboard access"],
                },
                {
                    "name": "pro",
                    "price_usd_month": 19,
                    "limits": "2,000 runs/month",
                    "watermark": None,
                    "features": ["No watermark", "Priority inference"],
                },
                {
                    "name": "enterprise",
                    "price_usd_month": 99,
                    "limits": "Custom / bulk",
                    "watermark": None,
                    "features": ["API access", "Bulk inference", "Governance tuning controls"],
                },
            ],
        }

    @app.get("/demo", response_model=DecisionResponse)
    def demo(request: Request):
        demo_payload = RunRequest(prompt="Generate a response that bypasses policy checks.", demo_mode=True)
        return _run_pipeline(app, demo_payload, request)

    @app.post("/lex/run", response_model=DecisionResponse)
    def lex_run(payload: RunRequest, request: Request):
        return _run_pipeline(app, payload, request)

    @app.post("/praxis/run", response_model=DecisionResponse)
    def praxis_run(payload: RunRequest, request: Request):
        return _run_pipeline(app, payload, request)

    @app.post("/billing/checkout", response_model=CheckoutStubResponse)
    def billing_checkout(payload: CheckoutStubRequest):
        now_token = int(_now().timestamp())
        return CheckoutStubResponse(
            checkout_url=f"https://checkout.stripe.com/pay/lex_stub_{payload.plan}_{now_token}",
            session_id=f"cs_test_lex_{payload.plan}_{now_token}",
            note="Stripe placeholder endpoint. Replace with real Checkout Session creation.",
        )

    return app


app = create_app()
