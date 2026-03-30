import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.entities import Metric, Project, Signal, Task
from app.models.schemas import ProjectCreate, SignalCreate, TaskCreate
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


def route_task(db: Session, payload: TaskCreate) -> Task:
    task = Task(
        id=payload.id,
        title=payload.title,
        project_id=payload.project_id,
        priority=payload.priority,
        status=payload.status,
        from_signal=payload.from_signal,
        has_metric=payload.has_metric,
        task_type=payload.task_type,
        mode=payload.mode,
    )

    enforce_task_creation_rules(db, task)
    enforce_planning_exists(db)

    is_valid, reason = validate_task(task)
    if not is_valid:
        mark_invalid_and_queue(db, task, reason)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def execute_task(db: Session, task: Task, new_status: str) -> Task:
    task.status = new_status
    if new_status == "Done":
        task.completed_at = datetime.utcnow()
        if task.has_metric:
            metric = Metric(id=f"metric-{task.id}-{int(datetime.utcnow().timestamp())}", task_id=task.id, value=1.0)
            db.add(metric)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
