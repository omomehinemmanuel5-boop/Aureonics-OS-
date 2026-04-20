from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SignalCreate(BaseModel):
    id: str
    content: str


class ProjectCreate(BaseModel):
    id: str
    name: str
    objective: str
    steps: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class TaskCreate(BaseModel):
    id: str
    title: str
    project_id: str | None = None
    priority: str | None = None
    status: Literal["Todo", "Doing", "Done"] | None = None

    from_signal: bool = False
    has_metric: bool = False

    task_type: str | None = None
    mode: Literal["Analytical", "Collaborative", "Exploratory"] | None = None


class TaskUpdate(BaseModel):
    status: Literal["Todo", "Doing", "Done"]


class ContinuityTestRequest(BaseModel):
    anchor_context: str
    responses: list[str]
    time_deltas: list[float] = Field(default_factory=list)


class ReciprocityTestItem(BaseModel):
    input_text: str
    output_text: str


class ReciprocityTestRequest(BaseModel):
    pairs: list[ReciprocityTestItem]


class SovereigntyTestItem(BaseModel):
    decision: str
    constraint_passed: bool


class SovereigntyTestRequest(BaseModel):
    items: list[SovereigntyTestItem]


class MetricSnapshot(BaseModel):
    continuity_score: float
    reciprocity_score: float
    sovereignty_score: float
    stability_margin: float


class AlertSnapshot(BaseModel):
    weakest_pillar: str
    alert: str


class GovernorCorrection(BaseModel):
    pillar: str
    severity: str
    deficit: float
    action: str
    rationale: str
    expected_shift: str
    target_mode: str


class GovernorSnapshot(BaseModel):
    active: bool
    tau: float
    scores: dict[str, float]
    stability_margin: float
    weakest_pillar: str
    violated_pillars: list[str]
    deficits: dict[str, float]
    constitutional_band: str
    governance_pressure: float
    target_mode: str
    corrections: list[GovernorCorrection]
    alert: str


class WeeklyProfileOut(MetricSnapshot, AlertSnapshot):
    generated_at: datetime
