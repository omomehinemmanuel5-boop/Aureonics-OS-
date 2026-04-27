from contextlib import asynccontextmanager
from datetime import datetime, timezone
import importlib
import os
import sqlite3
from difflib import SequenceMatcher
from typing import Literal, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from lex_memory.engine import classify_state, run_memory_pipeline

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


def _load_runtime_dependencies() -> None:
    global kernel
    _ensure_runtime_state()
    app.state.startup_errors = []
    try:
        database_mod = importlib.import_module("app.database")
        database_mod.Base.metadata.create_all(bind=database_mod.engine)
    except Exception as exc:
        app.state.startup_errors.append(f"database init failed: {exc}")

    try:
        kernel_mod = importlib.import_module("sovereign_kernel_v2")
        kernel = kernel_mod.SovereignKernel()
        app.state.kernel = kernel
    except Exception as exc:
        app.state.startup_errors.append(f"kernel init failed: {exc}")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if supabase_url and supabase_key:
        try:
            supabase_mod = importlib.import_module("supabase")
            app.state.supabase = supabase_mod.create_client(supabase_url, supabase_key)
        except Exception as exc:
            app.state.startup_errors.append(f"supabase init failed: {exc}")


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


class RunRequest(BaseModel):
    prompt: str
    firewall_mode: bool = True
    bridge: Optional[bool] = None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_output: str
    governed_output: str
    final_output: str
    intervention: bool
    intervention_reason: str
    semantic_diff_score: float
    M: float


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


def _run_pipeline(payload: RunRequest) -> DecisionResponse:
    raw_output = _generate_raw_output(payload.prompt)
    governed_output, reason = _govern_text(raw_output)

    semantic_diff_score = _semantic_diff_score(raw_output, governed_output)
    crs = _normalized_crs(payload.prompt, raw_output, governed_output)
    tau = 0.20
    m_val = round(min(crs.values()), 6)

    intervention = semantic_diff_score > 0.12 or m_val < tau
    if not payload.firewall_mode:
        intervention = False
        reason = "Firewall mode OFF; pass-through enforced."

    final_output = governed_output if (payload.firewall_mode and intervention) else raw_output
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

    return DecisionResponse(
        raw_output=raw_output,
        governed_output=governed_output,
        final_output=final_output,
        intervention=intervention,
        intervention_reason=reason,
        semantic_diff_score=semantic_diff_score,
        M=m_val,
    )


def _normalize_trace_row(row: dict) -> CanonicalTrace:
    c = float(row.get("C", row.get("c", 0.0)) or 0.0)
    r = float(row.get("R", row.get("r", 0.0)) or 0.0)
    s = float(row.get("S", row.get("s", 0.0)) or 0.0)
    m_val = float(row.get("M", row.get("m", min(c, r, s))) or 0.0)
    intervened = bool(row.get("intervention", row.get("intervened", False)))
    semantic_diff = float(row.get("semantic_diff_score", row.get("semanticDiff", 0.0)) or 0.0)
    theta_eff = row.get("thetaEff", row.get("theta_eff"))
    created_at = row.get("created_at") or row.get("createdAt")
    if not created_at:
        created_at = datetime.now(timezone.utc).isoformat()
    return CanonicalTrace(
        id=str(row.get("id", uuid4())),
        createdAt=str(created_at),
        prompt=str(row.get("prompt", "")),
        raw=str(row.get("response_raw", row.get("raw", ""))),
        governed=str(row.get("response_governed", row.get("governed", ""))),
        final=str(row.get("response_final", row.get("final", ""))),
        reason=str(row.get("intervention_reason", row.get("reason", "No intervention recorded."))),
        metrics=TraceMetrics(
            M=m_val,
            C=c,
            R=r,
            S=s,
            ADV=round(c - r, 6),
            thetaEff=float(theta_eff) if theta_eff is not None else None,
            semanticDiff=semantic_diff,
            intervened=intervened,
            health=_health_label(intervened=intervened, m_val=m_val),
        ),
    )


@app.get("/", include_in_schema=False)
def landing():
    return FileResponse("app/static/index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse("app/static/index.html")


@app.post("/lex/run", response_model=DecisionResponse)
def lex_run(payload: RunRequest):
    return _run_pipeline(payload)


@app.post("/praxis/run", response_model=DecisionResponse)
def praxis_run(payload: RunRequest):
    return _run_pipeline(payload)


@app.post("/api/lex/trace", response_model=CanonicalTrace)
def create_lex_trace(payload: RunRequest):
    decision = _run_pipeline(payload)
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
