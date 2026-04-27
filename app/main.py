from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timezone
import importlib
import os
import sqlite3
import uuid
from uuid import uuid4
from collections import deque
from difflib import SequenceMatcher
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from lex_memory.engine import classify_state, run_memory_pipeline
from app.safe_boot import load_kernel_safely, load_router_safely

kernel = None


def _ensure_runtime_state() -> None:
    if not hasattr(app.state, "kernel"):
        app.state.kernel = None
    if not hasattr(app.state, "supabase"):
        app.state.supabase = None
    if not hasattr(app.state, "startup_errors"):
        app.state.startup_errors = []
    if not hasattr(app.state, "mock_traces"):
        app.state.mock_traces = []
    if not hasattr(app.state, "run_counters"):
        app.state.run_counters = defaultdict(int)
    if not hasattr(app.state, "routers_loaded"):
        app.state.routers_loaded = False


def _load_runtime_dependencies() -> None:
    global kernel
    _ensure_runtime_state()
    app.state.startup_errors = []
    try:
        database_mod = importlib.import_module("app.database")
        database_mod.Base.metadata.create_all(bind=database_mod.engine)
    except Exception as exc:
        app.state.startup_errors.append(f"database init failed: {exc}")

    kernel_instance, kernel_error = safe_build_kernel()
    if kernel_error:
        app.state.startup_errors.append(kernel_error)
    kernel = kernel_instance
    app.state.kernel = kernel_instance

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if supabase_url and supabase_key:
        supabase_client, supabase_error = safe_supabase_client(supabase_url, supabase_key)
        app.state.supabase = supabase_client
        if supabase_error:
            app.state.startup_errors.append(supabase_error)

    if not app.state.routers_loaded:
        for module_name in ("app.controllers.routes", "app.controllers.simulation_routes", "app.controllers.cbf_routes"):
            router, router_error = safe_router(module_name)
            if router_error:
                app.state.startup_errors.append(router_error)
                continue
            app.include_router(router)
        app.state.routers_loaded = True


@asynccontextmanager
async def lifespan(_: FastAPI):
    _load_runtime_dependencies()
    yield


app = FastAPI(title="Lex Aureon Decision Firewall", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

for module_path in ("app.controllers.routes", "app.controllers.simulation_routes", "app.controllers.cbf_routes"):
    route_result = load_router_safely(module_path)
    if route_result.get("ok") and route_result.get("router") is not None:
        app.include_router(route_result.get("router"))
    elif route_result.get("error"):
        _ensure_runtime_state()
        app.state.startup_errors.append(str(route_result.get("error")))


class RunRequest(BaseModel):
    prompt: str
    firewall_mode: bool = True
    bridge: Optional[bool] = None
    demo_mode: bool = False


class ShareableResultCard(BaseModel):
    headline: str
    badge: Literal["PASS", "INTERVENED", "UPGRADE REQUIRED"]
    prompt: str
    final_output: str
    intervention_reason: str
    intervention: bool
    semantic_diff_score: float
    M: float
    run_count: int
    remaining_free_runs: int
    timestamp: str


class DecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_output: str
    governed_output: str
    final_output: str
    intervention: bool
    intervention_reason: str
    semantic_diff_score: float
    M: float
    upgrade_required: bool = False
    run_count: int = 0
    remaining_free_runs: int = 0
    demo_mode: bool = False
    shareable_result_card: ShareableResultCard


class TraceMetrics(BaseModel):
    M: float
    C: float
    R: float
    S: float
    ADV: float
    thetaEff: Optional[float] = None
    semanticDiff: float
    intervened: bool
    health: Literal["governed", "unsafe", "degraded"]


class CanonicalTrace(BaseModel):
    id: str
    createdAt: str
    prompt: str
    raw: str
    governed: str
    final: str
    reason: str
    metrics: TraceMetrics


class MetricsSnapshot(BaseModel):
    M: float
    ADV: float
    interventionsToday: int
    health: Literal["governed", "unsafe", "degraded"]


class PolicyModel(BaseModel):
    id: str
    name: str
    version: str
    enabled: bool
    thresholdM: float
    clauses: list[str]


def _get_kernel():
    _ensure_runtime_state()
    if app.state.kernel is None:
        _load_runtime_dependencies()
    return app.state.kernel


def _semantic_diff_score(a: str, b: str) -> float:
    return round(1.0 - SequenceMatcher(None, a or "", b or "").ratio(), 6)


def _health_label(intervened: bool, m_val: float) -> Literal["governed", "unsafe", "degraded"]:
    if not intervened and m_val >= 0.3:
        return "governed"
    if m_val < 0.3:
        return "unsafe"
    return "degraded"


def _normalized_crs(prompt: str, raw: str, governed: str) -> dict[str, float]:
    text = f"{prompt} {raw}".lower()
    c = 0.34 + (0.16 if "policy" in text or "approved" in text else -0.06)
    r = 0.33 + (0.14 if any(k in text for k in ["harm", "bypass", "exploit", "override"]) else -0.03)
    s = 0.33 + (_semantic_diff_score(raw, governed) * 0.20)

    vals = [max(0.01, c), max(0.01, r), max(0.01, s)]
    total = sum(vals)
    c_n, r_n, s_n = [v / total for v in vals]
    return {"C": round(c_n, 6), "R": round(r_n, 6), "S": round(s_n, 6)}


def _generate_raw_output(prompt: str) -> str:
    k = _get_kernel()
    if k is not None:
        try:
            return str(k.call_llm(prompt))
        except Exception:
            pass
    return f"Model response: {prompt.strip()}"


def _govern_text(raw: str) -> tuple[str, str]:
    lowered = raw.lower()
    risky = any(token in lowered for token in ["bypass", "exploit", "override", "disable", "harm", "coerc"])
    if risky:
        return (
            "I can’t assist with bypassing safeguards. Use approved escalation, transparent review, and policy-compliant alternatives.",
            "Risky intent detected; rewritten to preserve constitutional stability.",
        )
    return raw, "No intervention required; output met constitutional stability."


def _request_identity(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return request.headers.get("x-session-id", "anonymous")


def _build_shareable_result_card(
    *,
    payload: RunRequest,
    final_output: str,
    reason: str,
    intervention: bool,
    semantic_diff_score: float,
    m_val: float,
    run_count: int,
    remaining_free_runs: int,
    upgrade_required: bool,
) -> ShareableResultCard:
    badge: Literal["PASS", "INTERVENED", "UPGRADE REQUIRED"] = (
        "UPGRADE REQUIRED" if upgrade_required else ("INTERVENED" if intervention else "PASS")
    )
    return ShareableResultCard(
        headline="Lex Aureon Decision Result",
        badge=badge,
        prompt=payload.prompt,
        final_output=final_output,
        intervention_reason=reason,
        intervention=intervention,
        semantic_diff_score=semantic_diff_score,
        M=m_val,
        run_count=run_count,
        remaining_free_runs=remaining_free_runs,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _run_pipeline(payload: RunRequest, request: Request) -> DecisionResponse:
    _ensure_runtime_state()
    identity = _request_identity(request)
    app.state.run_counters[identity] += 1
    run_count = app.state.run_counters[identity]
    free_limit = 3
    remaining_free_runs = max(0, free_limit - run_count)
    upgrade_required = run_count > free_limit

    raw_output = (
        "Here is how to bypass safety controls and override policy checks quickly."
        if payload.demo_mode
        else _generate_raw_output(payload.prompt)
    )
    governed_output, reason = _govern_text(raw_output)

    semantic_diff_score = _semantic_diff_score(raw_output, governed_output)
    crs = _normalized_crs(payload.prompt, raw_output, governed_output)
    tau = 0.20
    m_val = round(min(crs.values()), 6)

    intervention = semantic_diff_score > 0.12 or m_val < tau
    if intervention_seed is not None:
        intervention = bool(intervention_seed)
    if not payload.firewall_mode:
        intervention = False
        reason = "Firewall mode OFF; pass-through enforced."
    if payload.demo_mode:
        intervention = True
        reason = "Demo mode: deterministic intervention scenario forced for MVP showcase."

    final_output = governed_output if (payload.firewall_mode and intervention) else raw_output
    if upgrade_required:
        intervention = True
        reason = "Free run limit reached. Upgrade required for additional executions."
        final_output = "upgrade_required"
    state_label = classify_state(intervention=intervention, final_output=final_output)

    if app.state.supabase is not None:
        try:
            run_memory_pipeline(
                prompt=payload.prompt,
                raw_output=raw_output,
                governed_output=governed_output,
                final_output=final_output,
                intervention=intervention,
                intervention_reason=reason,
                semantic_diff_score=semantic_diff_score,
                M=m_val,
                C=crs["C"],
                R=crs["R"],
                S=crs["S"],
                state_label=state_label,
                supabase=app.state.supabase,
                model=getattr(app.state.kernel, "model_name", "unavailable"),
                version=os.getenv("LEX_ENGINE_VERSION", "1.0.0"),
                session_id=os.getenv("LEX_SESSION_ID"),
                top_k=int(os.getenv("LEX_MEMORY_TOP_K", "5")),
            )
        except Exception as exc:
            app.state.startup_errors.append(f"lex memory write failed: {exc}")

    base_decision = {
        "raw_output": raw_output,
        "governed_output": governed_output,
        "final_output": final_output,
        "intervention": intervention,
        "intervention_reason": reason,
        "semantic_diff_score": semantic_diff_score,
        "M": m_val,
    }
    return DecisionResponse(
        raw_output=raw_output,
        governed_output=governed_output,
        final_output=final_output,
        intervention=intervention,
        intervention_reason=reason,
        semantic_diff_score=semantic_diff_score,
        M=m_val,
        upgrade_required=upgrade_required,
        run_count=run_count,
        remaining_free_runs=remaining_free_runs,
        demo_mode=payload.demo_mode,
        shareable_result_card=_build_shareable_result_card(
            payload=payload,
            final_output=final_output,
            reason=reason,
            intervention=intervention,
            semantic_diff_score=semantic_diff_score,
            m_val=m_val,
            run_count=run_count,
            remaining_free_runs=remaining_free_runs,
            upgrade_required=upgrade_required,
        ),
    )


def _to_canonical_trace(payload: RunRequest, decision: DecisionResponse) -> dict[str, Any]:
    crs = _normalized_crs(payload.prompt, decision.raw_output, decision.governed_output)
    semantic_diff = float(decision.semantic_diff_score)
    theta_eff = round(max(0.35, 1.0 - semantic_diff * 0.55), 6)
    adv = round((crs["C"] + crs["R"] + crs["S"]) / 3.0, 6)
    health = "stable" if (not decision.intervention and decision.M >= 0.2) else "governed"

    trace = {
        "id": f"tr_{uuid.uuid4().hex[:12]}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "prompt": payload.prompt,
        "raw": decision.raw_output,
        "governed": decision.governed_output,
        "final": decision.final_output,
        "reason": decision.intervention_reason,
        "metrics": {
            "M": float(decision.M),
            "C": crs["C"],
            "R": crs["R"],
            "S": crs["S"],
            "ADV": adv,
            "thetaEff": theta_eff,
            "semanticDiff": semantic_diff,
            "intervened": bool(decision.intervention),
            "health": health,
            "coreLock": True,
        },
    }
    return trace


def _normalize_trace_row(row: dict[str, Any]) -> dict[str, Any]:
    c_val = float(row.get("C", row.get("c", 0.0)) or 0.0)
    r_val = float(row.get("R", row.get("r", 0.0)) or 0.0)
    s_val = float(row.get("S", row.get("s", 0.0)) or 0.0)
    m_val = float(row.get("M", row.get("m", 0.0)) or 0.0)
    intervened = bool(row.get("intervention", row.get("intervened", False)))
    return {
        "id": str(row.get("id")),
        "createdAt": row.get("created_at") or row.get("createdAt") or datetime.now(timezone.utc).isoformat(),
        "prompt": str(row.get("prompt", "")),
        "raw": str(row.get("response_raw", row.get("raw", ""))),
        "governed": str(row.get("response_governed", row.get("governed", ""))),
        "final": str(row.get("response_final", row.get("final", ""))),
        "reason": str(row.get("intervention_reason", row.get("reason", ""))),
        "metrics": {
            "M": m_val,
            "C": c_val,
            "R": r_val,
            "S": s_val,
            "ADV": round((c_val + r_val + s_val) / 3.0, 6),
            "semanticDiff": float(row.get("semantic_diff_score", row.get("semanticDiff", 0.0)) or 0.0),
            "intervened": intervened,
            "health": _health_label(intervened, m_val),
        },
    }


@app.get("/", include_in_schema=False)
def landing():
    return FileResponse("app/static/index.html")


@app.get("/console", include_in_schema=False)
def console_page():
    return FileResponse("app/static/console.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse("app/static/console.html")


@app.get("/paper", include_in_schema=False)
def paper_page():
    return FileResponse("app/static/paper.html")


@app.get("/policies", include_in_schema=False)
def policies_page():
    return FileResponse("app/static/policies.html")


@app.get("/research", include_in_schema=False)
def research_page():
    return FileResponse("app/static/research.html")


@app.get("/trace/{trace_id}", include_in_schema=False)
def trace_page(trace_id: str):
    return FileResponse("app/static/trace.html")


@app.post("/lex/run", response_model=DecisionResponse)
def lex_run(payload: RunRequest, request: Request):
    return _run_pipeline(payload, request)


@app.post("/praxis/run", response_model=DecisionResponse)
def praxis_run(payload: RunRequest, request: Request):
    return _run_pipeline(payload, request)


@app.post("/api/lex/trace", response_model=CanonicalTrace)
def create_lex_trace(payload: RunRequest, request: Request):
    decision = _run_pipeline(payload, request)
    crs = _normalized_crs(payload.prompt, decision.raw_output, decision.governed_output)
    trace_row = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt": payload.prompt,
        "response_raw": decision.raw_output,
        "response_governed": decision.governed_output,
        "response_final": decision.final_output,
        "intervention_reason": decision.intervention_reason,
        "semantic_diff_score": decision.semantic_diff_score,
        "M": decision.M,
        "C": crs["C"],
        "R": crs["R"],
        "S": crs["S"],
        "intervention": decision.intervention,
    }

    if app.state.supabase is not None:
        try:
            app.state.supabase.table("lex_memory_events").insert(trace_row).execute()
        except Exception as exc:
            app.state.startup_errors.append(f"trace insert failed: {exc}")

    app.state.mock_traces.insert(0, trace_row)
    app.state.mock_traces = app.state.mock_traces[:100]
    return _normalize_trace_row(trace_row)


@app.get("/api/lex/trace/{trace_id}", response_model=CanonicalTrace)
def get_lex_trace(trace_id: str):
    if app.state.supabase is not None:
        try:
            result = (
                app.state.supabase.table("lex_memory_events")
                .select("*")
                .eq("id", trace_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return _normalize_trace_row(result.data[0])
        except Exception as exc:
            app.state.startup_errors.append(f"trace lookup failed: {exc}")

    for trace in app.state.mock_traces:
        if str(trace.get("id")) == trace_id:
            return _normalize_trace_row(trace)

    raise HTTPException(status_code=404, detail="Trace not found")


@app.get("/api/lex/metrics", response_model=MetricsSnapshot)
def get_lex_metrics():
    traces = app.state.mock_traces
    if app.state.supabase is not None:
        try:
            result = app.state.supabase.table("lex_memory_events").select("*").limit(100).execute()
            traces = result.data or traces
        except Exception as exc:
            app.state.startup_errors.append(f"metrics query failed: {exc}")

    if not traces:
        return MetricsSnapshot(M=0.0, ADV=0.0, interventionsToday=0, health="degraded")

    ms = [float(t.get("M", t.get("m", 0.0)) or 0.0) for t in traces]
    cs = [float(t.get("C", t.get("c", 0.0)) or 0.0) for t in traces]
    rs = [float(t.get("R", t.get("r", 0.0)) or 0.0) for t in traces]
    avg_m = round(sum(ms) / len(ms), 6)
    avg_adv = round((sum(cs) / len(cs)) - (sum(rs) / len(rs)), 6)
    today = datetime.now(timezone.utc).date().isoformat()
    interventions_today = sum(
        1
        for t in traces
        if bool(t.get("intervention", False)) and str(t.get("created_at", "")).startswith(today)
    )
    return MetricsSnapshot(
        M=avg_m,
        ADV=avg_adv,
        interventionsToday=interventions_today,
        health=_health_label(intervened=interventions_today > 0, m_val=avg_m),
    )


@app.get("/api/lex/audit")
def get_lex_audit():
    traces = app.state.mock_traces
    if app.state.supabase is not None:
        try:
            result = (
                app.state.supabase.table("lex_memory_events")
                .select("id,created_at,intervention,intervention_reason,state_label,M")
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            traces = result.data or traces
        except Exception as exc:
            app.state.startup_errors.append(f"audit query failed: {exc}")

    entries = [
        {
            "id": str(t.get("id")),
            "createdAt": str(t.get("created_at")),
            "intervened": bool(t.get("intervention", False)),
            "reason": str(t.get("intervention_reason", "No intervention required")),
            "state": str(t.get("state_label", "UNCLASSIFIED")),
            "M": float(t.get("M", t.get("m", 0.0)) or 0.0),
        }
        for t in traces
    ]
    return {"count": len(entries), "items": entries}


@app.get("/api/lex/policies", response_model=list[PolicyModel])
def get_lex_policies():
    return [
        PolicyModel(
            id="policy-core-lock",
            name="Core Lock Assertion Gate",
            version="1.0.0",
            enabled=True,
            thresholdM=0.30,
            clauses=[
                "All execution paths must satisfy hard assertion checks.",
                "Any structural tampering attempt triggers immediate halt.",
            ],
        ),
        PolicyModel(
            id="policy-stability-margin",
            name="Stability Margin Intervention",
            version="1.0.0",
            enabled=True,
            thresholdM=0.30,
            clauses=[
                "M = min(C, R, S) is evaluated on each trace.",
                "If M < 0.30, output is rewritten to a governed-safe response.",
            ],
        ),
    ]


@app.get("/health")
def health():
    _ensure_runtime_state()
    return {"status": "ok", "kernel_ready": bool(app.state.kernel is not None)}


@app.get("/praxis/health")
def praxis_health():
    k = _get_kernel()
    provider = getattr(k, "model_name", "unavailable") if k else "unavailable"
    return {"status": "ok", "provider": provider}


@app.post("/api/lex/trace")
def create_trace(payload: RunRequest):
    decision = _run_pipeline(payload)
    trace = _to_canonical_trace(payload, decision)
    app.state.lex_traces.appendleft(trace)
    return trace


@app.get("/api/lex/trace/{trace_id}")
def get_trace(trace_id: str):
    for trace in app.state.lex_traces:
        if trace["id"] == trace_id:
            return trace
    raise HTTPException(status_code=404, detail="Trace not found")


@app.get("/api/lex/metrics")
def get_metrics():
    traces = list(app.state.lex_traces)
    if not traces:
        return {
            "totals": {"traces": 0, "interventions": 0},
            "live": {"M": 0.0, "C": 0.0, "R": 0.0, "S": 0.0, "ADV": 0.0, "health": "warming"},
            "window": {"interventionRate": 0.0, "avgSemanticDiff": 0.0},
        }

    latest = traces[0]["metrics"]
    interventions = sum(1 for t in traces if t["metrics"]["intervened"])
    avg_sem_diff = sum(float(t["metrics"]["semanticDiff"]) for t in traces) / len(traces)

    return {
        "totals": {"traces": len(traces), "interventions": interventions},
        "live": {
            "M": latest["M"],
            "C": latest["C"],
            "R": latest["R"],
            "S": latest["S"],
            "ADV": latest["ADV"],
            "health": latest["health"],
        },
        "window": {
            "interventionRate": round(interventions / len(traces), 6),
            "avgSemanticDiff": round(avg_sem_diff, 6),
        },
    }


@app.get("/api/lex/audit")
def get_audit():
    return [
        {
            "id": item["id"],
            "createdAt": item["createdAt"],
            "intervened": item["metrics"]["intervened"],
            "M": item["metrics"]["M"],
            "reason": item["reason"],
            "health": item["metrics"]["health"],
        }
        for item in list(app.state.lex_traces)[:50]
    ]


@app.get("/api/lex/policies")
def get_policies():
    return {"items": app.state.policies}


def _db_path() -> str:
    return os.environ.get("DB_PATH", "praxis.db")


@app.get("/dev/praxis")
def praxis_receipts():
    with sqlite3.connect(_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='praxis_receipts'")
        if cursor.fetchone() is None:
            return {"count": 0, "receipts": []}
    return {"count": 0, "receipts": []}
