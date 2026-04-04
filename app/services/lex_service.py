from sqlalchemy.orm import Session

from app.models.entities import CorrectionQueue, Project, Task


VALID_STATUSES = {"Todo", "Doing", "Done"}


def validate_task(task: Task) -> tuple[bool, str]:
    missing = []
    if not task.project_id:
        missing.append("project_id")
    if not task.priority:
        missing.append("priority")
    if not task.status:
        missing.append("status")
    elif task.status not in VALID_STATUSES:
        missing.append("status_invalid")

    if missing:
        return False, f"Missing/invalid required fields: {', '.join(missing)}"
    return True, ""


def enforce_task_creation_rules(db: Session, task: Task) -> None:
    if task.project_id is None:
        raise ValueError("project_id is required: task creation rejected")

    project = db.get(Project, task.project_id)
    if project is None:
        raise ValueError("project_id does not exist")


def enforce_planning_exists(db: Session) -> None:
    has_planning = db.query(Project).count() > 0
    if not has_planning:
        raise ValueError("No planning exists: execution blocked")


def enforce_done_task_immutable(existing_task: Task) -> None:
    if existing_task.status == "Done":
        raise ValueError("Done task is immutable by audit law")


def mark_invalid_and_queue(db: Session, task: Task, reason: str) -> None:
    task.is_invalid = True
    task.invalid_reason = reason
    task.correction_queue = True
    queue_item = CorrectionQueue(task_id=task.id, reason=reason)
    db.add(queue_item)
