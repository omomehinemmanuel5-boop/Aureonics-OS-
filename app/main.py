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
from sqlalchemy import desc

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.database import Base, SessionLocal, engine
from app.models import entities as _entities  # noqa: F401
from app.models.entities import AuditLedgerEntry
from app.safe_boot import load_kernel_safely
from app.services.usage_service import get_today_usage, log_usage
from sovereign_kernel_v2 import SovereignKernel


class RunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    firewall_mode: bool = True
    bridge: bool | None = None
    demo_mode: bool = False


class DiffChunk(BaseModel):
    type: Literal["unchanged", "removed", "added"]
    text: str



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
    remaining_free_runs: int | None = None
    usage_today: int | None = None
    error: str | None = None
    upgrade_required: bool = False
    message: str | None = None
    metrics: dict[str, float | int] | None = None
    diff: list[DiffChunk] = []


class TrustReceiptRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    response: DecisionResponse
    run_id: str | None = Field(default=None, min_length=3, max_length=128)


class TrustReceiptResponse(BaseModel):
    run_id: str
    generated_at: str
    input_hash: str
    raw_output_hash: str
    governed_output_hash: str
    final_output_hash: str
    intervention: bool
    intervention_reason: str
    semantic_diff_score: float
    M: float
    stability_timeline: list[dict[str, float | str]]
    integrity_signature: str
    key_id: str = "v1"
    receipt_version: Literal["1.0"] = "1.0"


class TrustReceiptVerifyRequest(BaseModel):
    receipt: TrustReceiptResponse


class TrustReceiptVerifyResponse(BaseModel):
    valid: bool
    reason: str
    expected_signature: str


class SalesBridgeRequest(BaseModel):
    run_id: str
    company_name: str = Field(min_length=2, max_length=160)
    buyer_role: str = Field(min_length=2, max_length=120)


class SalesBridgeResponse(BaseModel):
    run_id: str
    risk_band: Literal["green", "amber", "red"]
    recommended_plan: Literal["pro", "enterprise"]
    next_action: str
    controls_summary: list[str]
    confidence_score: float


class StabilityBoundsResponse(BaseModel):
    lower_bound: float
    upper_bound: float
    window_size: int
    intervention_rate: float
    status: Literal["stable", "watch", "alert"]


class SovereigntyEvidenceResponse(BaseModel):
    run_id: str
    badge_svg: str
    evidence_summary: str


class TrustReceiptExportResponse(BaseModel):
    run_id: str
    receipt: TrustReceiptResponse
    badge_hash: str
    export_hash: str
    ledger_chain_hash: str
    signed_export: dict[str, object]


class ExportVerifyRequest(BaseModel):
    signed_export: dict[str, object]
    export_hash: str


def compute_diff(raw_output: str, governed_output: str) -> list[DiffChunk]:
    raw_words = raw_output.split()
    governed_words = governed_output.split()
    chunks: list[DiffChunk] = []
    matcher = SequenceMatcher(None, raw_words, governed_words)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            text = " ".join(raw_words[i1:i2])
            if text:
                chunks.append(DiffChunk(type="unchanged", text=text))
        elif tag == "delete":
            text = " ".join(raw_words[i1:i2])
            if text:
                chunks.append(DiffChunk(type="removed", text=text))
        elif tag == "insert":
            text = " ".join(governed_words[j1:j2])
            if text:
                chunks.append(DiffChunk(type="added", text=text))
        elif tag == "replace":
            removed = " ".join(raw_words[i1:i2])
            added = " ".join(governed_words[j1:j2])
            if removed:
                chunks.append(DiffChunk(type="removed", text=removed))
            if added:
                chunks.append(DiffChunk(type="added", text=added))

    return chunks
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

Base.metadata.create_all(bind=engine)


AUTH_TOKEN_TTL_HOURS = 12
_PASSWORD_ITERATIONS = 120_000


def _token_secret() -> str:
    return os.getenv("LEX_AUTH_SECRET", "lex-dev-secret-change-me")


def _audit_keys() -> dict[str, str]:
    raw = os.getenv("LEX_AUDIT_KEYS_JSON", "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and parsed:
                return {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            pass
    return {"v1": _token_secret()}


def _active_audit_key_id() -> str:
    keys = _audit_keys()
    configured = os.getenv("LEX_ACTIVE_AUDIT_KEY_ID", "").strip()
    if configured and configured in keys:
        return configured
    return sorted(keys.keys())[0]


def _frontend_base_url() -> str | None:
    configured = os.getenv("LEX_FRONTEND_BASE_URL", "").strip().rstrip("/")
    return configured or None


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
    if not hasattr(app.state, "trust_receipts"):
        app.state.trust_receipts = {}
    if not hasattr(app.state, "run_telemetry"):
        app.state.run_telemetry = []


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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _trust_receipt_signature(payload: dict[str, object], key_id: str | None = None) -> str:
    resolved_key_id = key_id or _active_audit_key_id()
    keys = _audit_keys()
    secret = keys.get(resolved_key_id) or _token_secret()
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _tier_value_prop(tier: str) -> str:
    if tier == "enterprise":
        return "Enterprise tier: procurement-grade evidence bundle, dynamic guardrails, and audit-committee traceability."
    if tier == "pro":
        return "Pro tier: governed output proof, signature verification, and operational trust receipts for customer assurance."
    return "Free tier: baseline governed response with preview-grade trust visibility."


def _badge_hash_for_receipt(receipt: TrustReceiptResponse) -> str:
    canonical = f"{receipt.run_id}|{receipt.integrity_signature}|{receipt.M:.6f}|{receipt.intervention}"
    return _sha256_text(canonical)


def _persist_ledger_entry(receipt: TrustReceiptResponse, tier: str) -> None:
    payload = receipt.dict()
    with SessionLocal() as db:
        existing = db.get(AuditLedgerEntry, receipt.run_id)
        if existing is not None:
            return
        last_entry = db.query(AuditLedgerEntry).order_by(desc(AuditLedgerEntry.created_at)).first()
        previous_chain_hash = last_entry.chain_hash if last_entry is not None else "0" * 64
        entry_body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        chain_hash = _sha256_text(f"{previous_chain_hash}|{receipt.integrity_signature}|{entry_body}")
        db.add(
            AuditLedgerEntry(
                run_id=receipt.run_id,
                receipt_json=entry_body,
                receipt_signature=receipt.integrity_signature,
                tier=tier,
                value_proposition=_tier_value_prop(tier),
                badge_hash=_badge_hash_for_receipt(receipt),
                previous_chain_hash=previous_chain_hash,
                chain_hash=chain_hash,
            )
        )
        db.commit()


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

    if plan == "free":
        with SessionLocal() as db:
            today_usage = get_today_usage(db, identity)
        if today_usage >= FREE_DAILY_LIMIT:
            return DecisionResponse(
                raw_output="",
                governed_output="",
                final_output="",
                intervention=False,
                intervention_reason="Usage limit reached",
                semantic_diff_score=0.0,
                M=0.0,
                plan=plan,
                watermark="Lex Demo",
                remaining_runs=0,
                remaining_free_runs=0,
                usage_today=today_usage,
                error="LIMIT_REACHED",
                upgrade_required=True,
                message="You’ve used all 10 free runs today.",
                diff=[],
            )

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
            remaining_free_runs=0,
            error="LIMIT_REACHED",
            upgrade_required=True,
            message="You’ve used all 10 free runs today.",
            diff=[],
        )

    raw_output = (
        "Here is how to bypass safety controls and override policy checks quickly."
        if payload.demo_mode
        else _generate_raw_output(payload.prompt, app.state.kernel)
    )
    governed_output, reason = _govern_text(raw_output)

    semantic_diff_score = _semantic_diff_score(raw_output, governed_output)
    diff = compute_diff(raw_output, governed_output)
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

    usage_today = None
    remaining_free_runs = None
    if plan == "free":
        with SessionLocal() as db:
            log_usage(db, identity)
            usage_today = get_today_usage(db, identity)
        remaining_free_runs = max(0, FREE_DAILY_LIMIT - usage_today)

    app.state.run_telemetry.append({
        "ts": _now().isoformat(),
        "M": m_val,
        "semantic_diff_score": semantic_diff_score,
        "intervention": intervention,
    })
    app.state.run_telemetry = app.state.run_telemetry[-500:]

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
        remaining_runs=remaining_free_runs if plan == "free" else remaining,
        remaining_free_runs=remaining_free_runs,
        usage_today=usage_today,
        metrics={
            "entropy": entropy_pct,
            "meaning": meaning_pct,
            "predicted_risk": predicted_risk,
            "actual_intervention": entropy_pct,
        },
        diff=diff,
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
    Base.metadata.create_all(bind=engine)
    app.state.kernel = _get_kernel()
    app.state.startup_errors = []
    app.state.usage_counts = {}
    app.state.users = {}
    app.state.trust_receipts = {}

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
        frontend = _frontend_base_url()
        if frontend:
            return RedirectResponse(url=f"{frontend}/", status_code=307)
        return FileResponse("app/static/index.html")

    @app.get("/dashboard", include_in_schema=False)
    def dashboard():
        frontend = _frontend_base_url()
        if frontend:
            return RedirectResponse(url=f"{frontend}/app", status_code=307)
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

    @app.post("/lex/trust-receipt", response_model=TrustReceiptResponse)
    def trust_receipt(payload: TrustReceiptRequest, request: Request, background_tasks: BackgroundTasks):
        now_dt = _now()
        run_id = payload.run_id or f"lexrun_{int(now_dt.timestamp())}_{secrets.token_hex(4)}"
        response = payload.response

        timeline = [
            {"stage": "raw", "stability": 0.0},
            {"stage": "governed", "stability": round(response.M, 6)},
            {"stage": "final", "stability": round(response.M if response.intervention else 1.0, 6)},
        ]
        receipt_payload: dict[str, object] = {
            "run_id": run_id,
            "generated_at": now_dt.isoformat(),
            "input_hash": _sha256_text(payload.prompt),
            "raw_output_hash": _sha256_text(response.raw_output),
            "governed_output_hash": _sha256_text(response.governed_output),
            "final_output_hash": _sha256_text(response.final_output),
            "intervention": response.intervention,
            "intervention_reason": response.intervention_reason,
            "semantic_diff_score": response.semantic_diff_score,
            "M": response.M,
            "stability_timeline": timeline,
        }
        key_id = _active_audit_key_id()
        signature = _trust_receipt_signature(receipt_payload, key_id=key_id)
        receipt = TrustReceiptResponse(**receipt_payload, integrity_signature=signature, key_id=key_id)
        app.state.trust_receipts[run_id] = receipt.dict()
        tier = _get_plan(request)
        background_tasks.add_task(_persist_ledger_entry, receipt, tier)
        return receipt

    @app.get("/lex/trust-receipt/{run_id}", response_model=TrustReceiptResponse)
    def get_trust_receipt(run_id: str):
        _ensure_state(app)
        found = app.state.trust_receipts.get(run_id)
        if not found:
            raise HTTPException(status_code=404, detail="Trust receipt not found")
        return TrustReceiptResponse(**found)

    @app.get("/lex/trust-receipt/{run_id}/export", response_model=TrustReceiptExportResponse)
    def export_trust_receipt(run_id: str):
        with SessionLocal() as db:
            row = db.get(AuditLedgerEntry, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Ledger entry not found")
        receipt_payload = json.loads(row.receipt_json)
        receipt = TrustReceiptResponse(**receipt_payload)
        badge_hash = row.badge_hash
        signed_export = {
            "run_id": run_id,
            "tier": row.tier,
            "value_proposition": row.value_proposition,
            "receipt_signature": row.receipt_signature,
            "badge_hash": badge_hash,
            "generated_at": receipt.generated_at,
            "ledger_chain_hash": row.chain_hash,
            "key_id": receipt.key_id,
        }
        export_hash = _trust_receipt_signature(signed_export, key_id=receipt.key_id)
        return TrustReceiptExportResponse(
            run_id=run_id,
            receipt=receipt,
            badge_hash=badge_hash,
            export_hash=export_hash,
            ledger_chain_hash=row.chain_hash,
            signed_export=signed_export,
        )

    @app.get("/lex/audit-ledger/verify")
    def verify_audit_chain(limit: int = 100):
        with SessionLocal() as db:
            entries = (
                db.query(AuditLedgerEntry)
                .order_by(AuditLedgerEntry.created_at.asc())
                .limit(max(1, min(limit, 5000)))
                .all()
            )
        if not entries:
            return {"valid": True, "checked": 0, "reason": "No ledger entries yet"}
        prev = "0" * 64
        for idx, entry in enumerate(entries):
            expected = _sha256_text(f"{prev}|{entry.receipt_signature}|{entry.receipt_json}")
            if entry.previous_chain_hash != prev or entry.chain_hash != expected:
                return {"valid": False, "checked": idx + 1, "reason": f"Chain mismatch at run_id={entry.run_id}"}
            prev = entry.chain_hash
        return {"valid": True, "checked": len(entries), "last_chain_hash": prev}

    @app.post("/lex/trust-receipt/verify", response_model=TrustReceiptVerifyResponse)
    def verify_trust_receipt(payload: TrustReceiptVerifyRequest):
        receipt = payload.receipt.dict()
        provided_signature = str(receipt.pop("integrity_signature", ""))
        receipt.pop("receipt_version", None)
        key_id = str(receipt.pop("key_id", "v1"))
        expected_signature = _trust_receipt_signature(receipt, key_id=key_id)
        is_valid = hmac.compare_digest(expected_signature, provided_signature)
        reason = "Signature valid" if is_valid else "Signature mismatch"
        return TrustReceiptVerifyResponse(
            valid=is_valid,
            reason=reason,
            expected_signature=expected_signature,
        )

    @app.post("/lex/trust-receipt/verify-export")
    def verify_export(payload: ExportVerifyRequest):
        signed_export = dict(payload.signed_export)
        key_id = str(signed_export.get("key_id", "v1"))
        expected = _trust_receipt_signature(signed_export, key_id=key_id)
        return {"valid": hmac.compare_digest(expected, payload.export_hash), "expected_export_hash": expected, "key_id": key_id}

    @app.get("/lex/audit-keys")
    def audit_keys():
        keys = _audit_keys()
        active = _active_audit_key_id()
        fingerprints = {k: _sha256_text(v)[:16] for k, v in keys.items()}
        return {"active_key_id": active, "available_key_ids": sorted(keys.keys()), "fingerprints": fingerprints}


    @app.post("/lex/sales-bridge", response_model=SalesBridgeResponse)
    def sales_bridge(payload: SalesBridgeRequest):
        with SessionLocal() as db:
            row = db.get(AuditLedgerEntry, payload.run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Trust receipt not found for run")
        receipt = TrustReceiptResponse(**json.loads(row.receipt_json))
        if receipt.M >= 0.92 and not receipt.intervention:
            band = "green"
            plan = "pro"
        elif receipt.M >= 0.8:
            band = "amber"
            plan = "enterprise"
        else:
            band = "red"
            plan = "enterprise"
        action = f"Send governed evidence pack to {payload.buyer_role} at {payload.company_name} and schedule procurement review."
        controls = [
            f"Receipt hash chain anchored for run {payload.run_id}.",
            f"Intervention={receipt.intervention} | M={receipt.M:.3f} | drift={receipt.semantic_diff_score:.3f}.",
            "Signature-verifiable trust receipt available for audit committee.",
            row.value_proposition,
        ]
        confidence = round(max(0.0, min(1.0, receipt.M - (0.1 if receipt.intervention else 0.0))), 4)
        return SalesBridgeResponse(run_id=payload.run_id, risk_band=band, recommended_plan=plan, next_action=action, controls_summary=controls, confidence_score=confidence)

    @app.get("/lex/stability-bounds", response_model=StabilityBoundsResponse)
    def stability_bounds(window: int = 50):
        _ensure_state(app)
        series = app.state.run_telemetry[-max(5, min(window, 500)):]
        if not series:
            return StabilityBoundsResponse(lower_bound=0.85, upper_bound=1.0, window_size=0, intervention_rate=0.0, status="watch")
        m_values = [float(item["M"]) for item in series]
        lower = round(max(0.0, min(m_values) - 0.02), 4)
        upper = round(min(1.0, max(m_values) + 0.02), 4)
        interventions = sum(1 for item in series if bool(item["intervention"]))
        rate = round(interventions / len(series), 4)
        status = "stable" if lower >= 0.82 and rate <= 0.35 else "watch" if lower >= 0.7 else "alert"
        return StabilityBoundsResponse(lower_bound=lower, upper_bound=upper, window_size=len(series), intervention_rate=rate, status=status)

    @app.get("/lex/trust-receipt/{run_id}/badge", response_model=SovereigntyEvidenceResponse)
    def sovereignty_badge(run_id: str):
        with SessionLocal() as db:
            row = db.get(AuditLedgerEntry, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Trust receipt not found")
        receipt = TrustReceiptResponse(**json.loads(row.receipt_json))
        color = "#22c55e" if receipt.M >= 0.9 else "#f59e0b" if receipt.M >= 0.8 else "#ef4444"
        text = "SOVEREIGN VERIFIED"
        sig = receipt.integrity_signature[:16]
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' width='860' height='220'><rect width='860' height='220' rx='16' fill='#020617'/><rect x='12' y='12' width='836' height='196' rx='12' fill='none' stroke='{color}' stroke-width='3'/><text x='36' y='72' fill='{color}' font-family='Inter,Arial' font-size='34' font-weight='700'>{text}</text><text x='36' y='116' fill='#e2e8f0' font-family='monospace' font-size='20'>run_id: {run_id}</text><text x='36' y='152' fill='#94a3b8' font-family='monospace' font-size='18'>sig: {sig}… | M={receipt.M:.3f} | intervention={str(receipt.intervention).lower()} | badge_hash={row.badge_hash[:12]}…</text></svg>"
        summary = f"Visual proof generated from signed trust receipt for run {run_id}."
        return SovereigntyEvidenceResponse(run_id=run_id, badge_svg=svg, evidence_summary=summary)

    return app


app = create_app()
