from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    risks: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    success_criteria: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=True)
    priority: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True)

    from_signal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_metric: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    task_type: Mapped[str] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=True)

    is_invalid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    invalid_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    correction_queue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(String, ForeignKey("tasks.id"), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class WeeklyProfile(Base):
    __tablename__ = "weekly_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)

    continuity_score: Mapped[float] = mapped_column(Float, nullable=False)
    reciprocity_score: Mapped[float] = mapped_column(Float, nullable=False)
    sovereignty_score: Mapped[float] = mapped_column(Float, nullable=False)
    stability_margin: Mapped[float] = mapped_column(Float, nullable=False)

    weakest_pillar: Mapped[str] = mapped_column(String, nullable=False)
    alert: Mapped[str] = mapped_column(Text, nullable=False)


class CorrectionQueue(Base):
    __tablename__ = "correction_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String, ForeignKey("tasks.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class AuditLedgerEntry(Base):
    __tablename__ = "audit_ledger_entries"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    receipt_json: Mapped[str] = mapped_column(Text, nullable=False)
    receipt_signature: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(24), nullable=False, default="free")
    value_proposition: Mapped[str] = mapped_column(Text, nullable=False)
    badge_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


@event.listens_for(AuditLedgerEntry, "before_update", propagate=True)
def _immutable_ledger_update(*_args, **_kwargs):
    raise ValueError("Audit ledger is immutable: updates are not allowed.")


@event.listens_for(AuditLedgerEntry, "before_delete", propagate=True)
def _immutable_ledger_delete(*_args, **_kwargs):
    raise ValueError("Audit ledger is immutable: deletes are not allowed.")
