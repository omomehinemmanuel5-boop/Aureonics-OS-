from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import UsageLog


def _utc_day_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.now(timezone.utc)
    day_start = datetime.combine(current.date(), time.min, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    return day_start, day_end


def get_today_usage(db: Session, user_id: str) -> int:
    day_start, day_end = _utc_day_bounds()
    stmt = select(func.count(UsageLog.id)).where(
        UsageLog.user_id == user_id,
        UsageLog.timestamp >= day_start,
        UsageLog.timestamp < day_end,
    )
    return int(db.scalar(stmt) or 0)


def log_usage(db: Session, user_id: str) -> UsageLog:
    entry = UsageLog(user_id=user_id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
