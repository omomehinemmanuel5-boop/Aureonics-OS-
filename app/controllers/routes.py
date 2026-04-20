from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Project, Task
from app.models.schemas import (
    AlertSnapshot,
    ContinuityTestRequest,
    GovernorSnapshot,
    MetricSnapshot,
    ProjectCreate,
    ReciprocityTestRequest,
    SignalCreate,
    SovereigntyTestRequest,
    TaskCreate,
    TaskUpdate,
    WeeklyProfileOut,
)
from app.services.governor_service import compute_alert
from app.services.lex_service import enforce_done_task_immutable
from app.services.metrics_service import compute_adv, compute_ccp, compute_iec
from app.services.profile_service import live_constitutional_snapshot, persist_weekly_profile
from app.services.workflow_service import (
    apply_corrections,
    execute_task,
    ingest_signal,
    plan_project,
    queued_corrections,
    route_task,
)

router = APIRouter()


@router.post("/signal")
def create_signal(payload: SignalCreate, db: Session = Depends(get_db)):
    try:
        signal = ingest_signal(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": signal.id, "content": signal.content, "processed": signal.processed}


@router.post("/project")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    try:
        project = plan_project(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": project.id, "name": project.name}


@router.post("/task")
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    try:
        snapshot = live_constitutional_snapshot(db)
        task, routing_meta = route_task(db, payload, governor_snapshot=snapshot)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": task.id,
        "status": task.status,
        "is_invalid": task.is_invalid,
        "invalid_reason": task.invalid_reason,
        "mode": task.mode,
        "priority": task.priority,
        "has_metric": task.has_metric,
        **routing_meta,
    }


@router.patch("/task/{task_id}")
def update_task_status(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        enforce_done_task_immutable(task)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    updated = execute_task(db, task, payload.status)
    return {"id": updated.id, "status": updated.status, "completed_at": updated.completed_at}


@router.get("/profile", response_model=MetricSnapshot)
def get_profile(db: Session = Depends(get_db)):
    snapshot = live_constitutional_snapshot(db)
    return {
        "continuity_score": snapshot["continuity_score"],
        "reciprocity_score": snapshot["reciprocity_score"],
        "sovereignty_score": snapshot["sovereignty_score"],
        "stability_margin": snapshot["stability_margin"],
    }


@router.get("/alerts", response_model=AlertSnapshot)
def get_alerts(db: Session = Depends(get_db)):
    snapshot = live_constitutional_snapshot(db)
    return {"weakest_pillar": snapshot["weakest_pillar"], "alert": snapshot["alert"]}


@router.get("/governor", response_model=GovernorSnapshot)
def get_governor(db: Session = Depends(get_db)):
    snapshot = live_constitutional_snapshot(db)
    return {
        "active": snapshot["active"],
        "tau": snapshot["tau"],
        "scores": snapshot["scores"],
        "stability_margin": snapshot["stability_margin"],
        "weakest_pillar": snapshot["weakest_pillar"],
        "violated_pillars": snapshot["violated_pillars"],
        "deficits": snapshot["deficits"],
        "constitutional_band": snapshot["constitutional_band"],
        "governance_pressure": snapshot["governance_pressure"],
        "target_mode": snapshot["target_mode"],
        "corrections": snapshot["corrections"],
        "alert": snapshot["alert"],
    }


@router.get("/governor/policy")
def get_governor_policy(db: Session = Depends(get_db)):
    snapshot = live_constitutional_snapshot(db)
    return {
        "constitutional_band": snapshot["constitutional_band"],
        "governance_pressure": snapshot["governance_pressure"],
        "target_mode": snapshot["target_mode"],
        "policy": snapshot["policy"],
    }


@router.get("/tasks/invalid")
def get_invalid_tasks(db: Session = Depends(get_db)):
    invalid_tasks = db.query(Task).filter(Task.is_invalid.is_(True)).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "project_id": t.project_id,
            "priority": t.priority,
            "status": t.status,
            "reason": t.invalid_reason,
        }
        for t in invalid_tasks
    ]


@router.get("/corrections/queue")
def get_correction_queue(db: Session = Depends(get_db)):
    return {"items": queued_corrections(db)}


@router.post("/corrections/apply")
def apply_correction_queue(limit: int = 5, db: Session = Depends(get_db)):
    snapshot = live_constitutional_snapshot(db)
    created = apply_corrections(db, snapshot, limit=limit)
    return {
        "applied": len(created),
        "target_mode": snapshot["target_mode"],
        "constitutional_band": snapshot["constitutional_band"],
        "created_tasks": created,
    }


@router.post("/test/continuity")
def test_continuity(payload: ContinuityTestRequest):
    return compute_ccp(payload.anchor_context, payload.responses, payload.time_deltas)


@router.post("/test/reciprocity")
def test_reciprocity(payload: ReciprocityTestRequest):
    pairs = [(item.input_text, item.output_text) for item in payload.pairs]
    return compute_iec(pairs)


@router.post("/test/sovereignty")
def test_sovereignty(payload: SovereigntyTestRequest):
    decisions = [item.decision for item in payload.items]
    compliance = [item.constraint_passed for item in payload.items]
    return compute_adv(decisions, compliance)


@router.get("/panels/analytical")
def panel_analytical(db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.mode == "Analytical").all()


@router.get("/panels/collaborative")
def panel_collaborative(db: Session = Depends(get_db)):
    return db.query(Task).filter((Task.mode == "Collaborative") | (Task.mode.is_(None))).all()


@router.get("/panels/exploratory")
def panel_exploratory(db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.mode == "Exploratory").all()


@router.get("/weekly-profile", response_model=WeeklyProfileOut)
def weekly_profile(db: Session = Depends(get_db)):
    snapshot = live_constitutional_snapshot(db)
    persist_weekly_profile(db, snapshot)
    return {
        "continuity_score": snapshot["continuity_score"],
        "reciprocity_score": snapshot["reciprocity_score"],
        "sovereignty_score": snapshot["sovereignty_score"],
        "stability_margin": snapshot["stability_margin"],
        "weakest_pillar": snapshot["weakest_pillar"],
        "alert": snapshot["alert"],
        "generated_at": datetime.now(timezone.utc),
    }
