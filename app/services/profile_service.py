from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.entities import Project, Task, WeeklyProfile
from app.services.governor_service import compute_alert, governor_policy, governor_state
from app.services.metrics_service import compute_profile


def week_start_for_day(day: date | None = None) -> date:
    day = day or datetime.now(timezone.utc).date()
    return day - timedelta(days=day.weekday())


def live_constitutional_snapshot(db: Session) -> dict:
    tasks = db.query(Task).all()
    projects = db.query(Project).all()
    profile = compute_profile(tasks, projects)
    state = governor_state(
        profile["continuity_score"],
        profile["reciprocity_score"],
        profile["sovereignty_score"],
    )
    weakest, alert = compute_alert(
        profile["continuity_score"],
        profile["reciprocity_score"],
        profile["sovereignty_score"],
    )
    return {
        **profile,
        **state,
        "weakest_pillar": weakest,
        "alert": alert,
        "policy": governor_policy(state),
        "task_count": len(tasks),
        "project_count": len(projects),
    }


def persist_weekly_profile(db: Session, snapshot: dict, on_day: date | None = None) -> WeeklyProfile:
    week_start = week_start_for_day(on_day)
    record_id = f"weekly-{week_start.isoformat()}"
    record = db.get(WeeklyProfile, record_id)
    if record is None:
        record = WeeklyProfile(id=record_id, week_start=week_start)

    record.continuity_score = snapshot["continuity_score"]
    record.reciprocity_score = snapshot["reciprocity_score"]
    record.sovereignty_score = snapshot["sovereignty_score"]
    record.stability_margin = snapshot["stability_margin"]
    record.weakest_pillar = snapshot["weakest_pillar"]
    record.alert = snapshot["alert"]

    db.add(record)
    db.commit()
    db.refresh(record)
    return record
