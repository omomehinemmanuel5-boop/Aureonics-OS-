from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os
import secrets
from difflib import SequenceMatcher
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=10, max_length=128)
    company_name: str = Field(min_length=2, max_length=160)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=10, max_length=128)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: str
    user: dict[str, str]


class CheckoutStubRequest(BaseModel):
    plan: Literal["pro", "enterprise"]
    method: Literal["manual"] = "manual"
    buyer_email: str = Field(min_length=5, max_length=320)
    company_name: str = Field(min_length=2, max_length=160)
    seats: int = Field(default=1, ge=1, le=1000)
    notes: str | None = Field(default=None, max_length=1000)


class CheckoutStubResponse(BaseModel):
    checkout_mode: Literal["manual_invoice"]
    invoice_id: str
    amount_usd: int | None = None
    currency: Literal["USD"] = "USD"
    payment_terms_days: int
    due_date: str
    wire_reference: str
    next_action: str
    payment_instructions: list[str]
    note: str


FREE_DAILY_LIMIT = 10
PRO_MONTHLY_LIMIT = 2000
_KERNEL_SINGLETON: SovereignKernel | None = None


AUTH_TOKEN_TTL_HOURS = 12
_PASSWORD_ITERATIONS = 120_000


def _token_secret() -> str:
    return os.getenv("LEX_AUTH_SECRET", "lex-dev-secret-change-me")


def _urlsafe_b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _urlsafe_unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _hash_password(password: str, salt: str | None = None) -> str:
    salt_bytes = (salt or secrets.token_hex(16)).encode("utf-8")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, _PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${_PASSWORD_ITERATIONS}${salt_bytes.decode()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        _, rounds, salt, digest = encoded.split("$", 3)
    except ValueError:
        return False
    test_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds)).hex()
    return hmac.compare_digest(test_digest, digest)


def _issue_access_token(user_id: str, email: str) -> tuple[str, datetime]:
    expiry = _now() + timedelta(hours=AUTH_TOKEN_TTL_HOURS)
    payload = {"sub": user_id, "email": email, "exp": int(expiry.timestamp())}
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded_payload = _urlsafe_b64(payload_json)
    signature = hmac.new(_token_secret().encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_urlsafe_b64(signature)}", expiry


def _decode_token(token: str) -> dict[str, str | int] | None:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
        expected = hmac.new(_token_secret().encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _urlsafe_unb64(signature_b64)):
            return None
        payload = json.loads(_urlsafe_unb64(payload_b64).decode("utf-8"))
    except Exception:
        return None

    exp = int(payload.get("exp", 0))
    if exp <= int(_now().timestamp()):
        return None
    return payload


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _auth_user(request: Request) -> dict[str, str] | None:
    return getattr(request.state, "auth_user", None)


def _require_auth(request: Request) -> dict[str, str]:
    user = _auth_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def _ensure_state(app: FastAPI) -> None:
    if not hasattr(app.state, "kernel"):
        app.state.kernel = None
    if not hasattr(app.state, "startup_errors"):
        app.state.startup_errors = []
    if not hasattr(app.state, "usage_counts"):
        app.state.usage_counts = {}
    if not hasattr(app.state, "users"):
        app.state.users = {}


def _get_kernel() -> SovereignKernel:
    global _KERNEL_SINGLETON
    if _KERNEL_SINGLETON is None:
        _KERNEL_SINGLETON = SovereignKernel()
    return _KERNEL_SINGLETON


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _request_identity(request: Request) -> str:
    user = _auth_user(request)
    if user:
        return f"user:{user.get('id', 'unknown')}"
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


def _plan_price_usd(plan: str) -> int | None:
    if plan == "pro":
        return 19
    return None


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
    app.state.users = {}

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
    async def auth_subscription_middleware(request: Request, call_next):
        _ensure_state(app)
        request.state.auth_user = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            payload = _decode_token(auth_header.split(" ", 1)[1].strip())
            if payload:
                request.state.auth_user = {
                    "id": str(payload.get("sub", "")),
                    "email": str(payload.get("email", "")),
                }

        request.state.subscription_plan = _get_plan(request)
        response = await call_next(request)
        response.headers["x-subscription-plan"] = request.state.subscription_plan
        if request.state.auth_user:
            response.headers["x-auth-user"] = request.state.auth_user.get("email", "")
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

    @app.post("/auth/register", response_model=AuthTokenResponse)
    def auth_register(payload: RegisterRequest):
        _ensure_state(app)
        email = _normalize_email(payload.email)
        if email in app.state.users:
            raise HTTPException(status_code=409, detail="Account already exists")

        user_id = f"usr_{secrets.token_hex(8)}"
        app.state.users[email] = {
            "id": user_id,
            "email": email,
            "company_name": payload.company_name.strip(),
            "password_hash": _hash_password(payload.password),
            "created_at": _now().isoformat(),
        }
        token, expires = _issue_access_token(user_id, email)
        return AuthTokenResponse(
            access_token=token,
            expires_at=expires.isoformat(),
            user={"id": user_id, "email": email, "company_name": payload.company_name.strip()},
        )

    @app.post("/auth/login", response_model=AuthTokenResponse)
    def auth_login(payload: LoginRequest):
        _ensure_state(app)
        email = _normalize_email(payload.email)
        user = app.state.users.get(email)
        if not user or not _verify_password(payload.password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token, expires = _issue_access_token(str(user["id"]), email)
        return AuthTokenResponse(
            access_token=token,
            expires_at=expires.isoformat(),
            user={"id": str(user["id"]), "email": email, "company_name": str(user["company_name"])},
        )

    @app.get("/auth/me")
    def auth_me(request: Request):
        user = _require_auth(request)
        record = app.state.users.get(user["email"], {})
        return {
            "id": user["id"],
            "email": user["email"],
            "company_name": record.get("company_name", ""),
            "plan": request.state.subscription_plan,
        }

    @app.get("/pricing")
    def pricing():
        return {
            "product": "Lex API — Governed AI Responses",
            "checkout_mode": "manual_invoice",
            "plans": [
                {
                    "name": "free",
                    "price_usd_month": 0,
                    "limits": "10 runs/day",
                    "watermark": "Lex Demo",
                    "features": ["Governed inference", "Dashboard access"],
                    "manual_checkout": False,
                },
                {
                    "name": "pro",
                    "price_usd_month": 19,
                    "limits": "2,000 runs/month",
                    "watermark": None,
                    "features": ["No watermark", "Priority inference"],
                    "manual_checkout": True,
                },
                {
                    "name": "enterprise",
                    "price_usd_month": 99,
                    "limits": "Custom / bulk",
                    "watermark": None,
                    "features": ["API access", "Bulk inference", "Governance tuning controls"],
                    "manual_checkout": True,
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
    def billing_checkout(payload: CheckoutStubRequest, request: Request):
        now_dt = _now()
        now_token = int(now_dt.timestamp())
        reference = f"LEX-{payload.plan.upper()}-{now_token}"
        price = _plan_price_usd(payload.plan)
        amount = None if price is None else payload.seats * price
        due_date = (now_dt + timedelta(days=14)).date().isoformat()
        if payload.plan == "pro":
            next_action = "Reply to the invoice email and pay via ACH/wire using the reference code."
        else:
            next_action = "Book enterprise scoping call; invoice is issued after scope confirmation."
        return CheckoutStubResponse(
            checkout_mode="manual_invoice",
            invoice_id=f"inv_manual_{payload.plan}_{now_token}",
            amount_usd=amount,
            payment_terms_days=14,
            due_date=due_date,
            wire_reference=reference,
            next_action=next_action,
            payment_instructions=[
                f"Send remittance to billing@aureonics.ai with invoice_id and wire reference {reference}.",
                "Payment rails: ACH transfer, domestic wire, or approved procurement portal.",
                "After payment confirmation, production plan entitlement is activated within one business day.",
            ],
            note="Manual payment mode is active. Stripe auto-checkout is intentionally disabled.",
        )

    return app


app = create_app()
