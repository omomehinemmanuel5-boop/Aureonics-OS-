from contextlib import asynccontextmanager
from datetime import datetime, timezone
import importlib
import os
import sqlite3
import uuid
from collections import deque
from difflib import SequenceMatcher
from typing import Any, Optional

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
    if not hasattr(app.state, "lex_traces"):
        app.state.lex_traces = deque(maxlen=250)
    if not hasattr(app.state, "policies"):
        app.state.policies = [
            {
                "id": "policy-core-lock-v1",
                "name": "Core Lock Final Assertion Gate",
                "description": "Final output can only be emitted after constitutional checks and intervention policy pass.",
                "version": "1.0.0",
                "active": True,
                "thresholds": {"M_min": 0.20, "semanticDiff_max": 0.12},
            },
            {
                "id": "policy-memory-theta-v1",
                "name": "Effective Theta Memory Weighting",
                "description": "Memory influence is bounded by theta_eff to preserve lawful stability under drift.",
                "version": "1.0.0",
                "active": True,
                "thresholds": {"theta_eff_min": 0.35, "theta_eff_max": 0.92},
            },
        ]


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


def _get_kernel():
    _ensure_runtime_state()
    if app.state.kernel is None:
        _load_runtime_dependencies()
    return app.state.kernel


def _semantic_diff_score(a: str, b: str) -> float:
    return round(1.0 - SequenceMatcher(None, a or "", b or "").ratio(), 6)


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
def lex_run(payload: RunRequest):
    return _run_pipeline(payload)


@app.post("/praxis/run", response_model=DecisionResponse)
def praxis_run(payload: RunRequest):
    return _run_pipeline(payload)


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
