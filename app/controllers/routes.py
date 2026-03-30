from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Project, Task
from app.models.schemas import (
    AlertSnapshot,
    ContinuityTestRequest,
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
from app.services.metrics_service import compute_adv, compute_ccp, compute_iec, compute_profile
from app.services.workflow_service import execute_task, ingest_signal, plan_project, route_task

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
        task = route_task(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": task.id,
        "status": task.status,
        "is_invalid": task.is_invalid,
        "invalid_reason": task.invalid_reason,
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
    tasks = db.query(Task).all()
    projects = db.query(Project).all()
    profile = compute_profile(tasks, projects)
    return {
        "continuity_score": profile["continuity_score"],
        "reciprocity_score": profile["reciprocity_score"],
        "sovereignty_score": profile["sovereignty_score"],
        "stability_margin": profile["stability_margin"],
    }


@router.get("/alerts", response_model=AlertSnapshot)
def get_alerts(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    projects = db.query(Project).all()
    profile = compute_profile(tasks, projects)
    weakest, alert = compute_alert(
        profile["continuity_score"],
        profile["reciprocity_score"],
        profile["sovereignty_score"],
    )
    return {"weakest_pillar": weakest, "alert": alert}


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
    tasks = db.query(Task).all()
    projects = db.query(Project).all()
    profile = compute_profile(tasks, projects)
    weakest, alert = compute_alert(
        profile["continuity_score"],
        profile["reciprocity_score"],
        profile["sovereignty_score"],
    )
    return {
        "continuity_score": profile["continuity_score"],
        "reciprocity_score": profile["reciprocity_score"],
        "sovereignty_score": profile["sovereignty_score"],
        "stability_margin": profile["stability_margin"],
        "weakest_pillar": weakest,
        "alert": alert,
        "generated_at": datetime.utcnow(),
    }
