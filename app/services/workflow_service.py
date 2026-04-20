import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.entities import CorrectionQueue, Metric, Project, Signal, Task
from app.models.schemas import ProjectCreate, SignalCreate, TaskCreate
from app.services.governor_service import governor_policy
from app.services.lex_service import (
    enforce_planning_exists,
    enforce_task_creation_rules,
    mark_invalid_and_queue,
    validate_task,
)


def ingest_signal(db: Session, payload: SignalCreate) -> Signal:
    signal = Signal(id=payload.id, content=payload.content)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


def plan_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(
        id=payload.id,
        name=payload.name,
        objective=payload.objective,
        steps=json.dumps(payload.steps),
        risks=json.dumps(payload.risks),
        success_criteria=json.dumps(payload.success_criteria),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def route_task(db: Session, payload: TaskCreate, governor_snapshot: dict | None = None) -> tuple[Task, dict]:
    governor_snapshot = governor_snapshot or {"active": False, "target_mode": payload.mode or "Collaborative"}
    policy = governor_policy(governor_snapshot)
    governor_applied = False

    assigned_mode = payload.mode
    if not assigned_mode:
        assigned_mode = policy["routing_bias"] if policy["routing_bias"] != "Balanced" else "Collaborative"
        governor_applied = governor_snapshot.get("active", False)

    assigned_priority = payload.priority or ("High" if governor_snapshot.get("active") else "Medium")
    assigned_has_metric = bool(payload.has_metric or payload.from_signal or policy["metric_required"])

    task = Task(
        id=payload.id,
        title=payload.title,
        project_id=payload.project_id,
        priority=assigned_priority,
        status=payload.status,
        from_signal=payload.from_signal,
        has_metric=assigned_has_metric,
        task_type=payload.task_type,
        mode=assigned_mode,
    )

    enforce_task_creation_rules(db, task)
    enforce_planning_exists(db)

    is_valid, reason = validate_task(task)
    if not is_valid:
        mark_invalid_and_queue(db, task, reason)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task, {
        "governor_applied": governor_applied,
        "assigned_mode": assigned_mode,
        "assigned_priority": assigned_priority,
        "metric_required": assigned_has_metric,
        "policy": policy,
    }


def execute_task(db: Session, task: Task, new_status: str) -> Task:
    task.status = new_status
    if new_status == "Done":
        task.completed_at = datetime.now(timezone.utc)
        if task.has_metric:
            metric = Metric(id=f"metric-{task.id}-{int(datetime.now(timezone.utc).timestamp())}", task_id=task.id, value=1.0)
            db.add(metric)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def queued_corrections(db: Session) -> list[dict]:
    queue_items = db.query(CorrectionQueue).order_by(CorrectionQueue.created_at.asc()).all()
    result = []
    for item in queue_items:
        task = db.get(Task, item.task_id)
        result.append(
            {
                "queue_id": item.id,
                "task_id": item.task_id,
                "task_title": task.title if task else None,
                "reason": item.reason,
                "created_at": item.created_at.isoformat(),
            }
        )
    return result


def apply_corrections(db: Session, governor_snapshot: dict, limit: int = 5) -> list[dict]:
    queue_items = db.query(CorrectionQueue).order_by(CorrectionQueue.created_at.asc()).limit(max(1, limit)).all()
    created = []
    target_mode = governor_snapshot.get("target_mode", "Analytical")

    for item in queue_items:
        task = db.get(Task, item.task_id)
        if task is None:
            db.delete(item)
            continue

        remediation_id = f"corr-{task.id}"
        remediation = db.get(Task, remediation_id)
        if remediation is None:
            remediation = Task(
                id=remediation_id,
                title=f"Correction: {task.title}",
                project_id=task.project_id,
                priority="High",
                status="Todo",
                from_signal=False,
                has_metric=True,
                task_type="correction",
                mode=target_mode,
            )
            db.add(remediation)
            created.append(
                {
                    "id": remediation.id,
                    "title": remediation.title,
                    "project_id": remediation.project_id,
                    "mode": remediation.mode,
                    "source_task_id": task.id,
                }
            )

        task.correction_queue = False
        db.add(task)
        db.delete(item)

    db.commit()
    return created
