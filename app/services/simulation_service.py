import random
import statistics
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entities import Project, Task, WeeklyProfile
from app.services.governor_service import THRESHOLD, compute_alert, governor_state, weakest_pillar
from app.services.metrics_service import compute_profile

MODES = ["Analytical", "Collaborative", "Exploratory"]
TASK_TYPES = ["Audit", "Research", "Execution", "Review"]
PRIORITIES = ["Low", "Medium", "High"]

BASIN_BY_PILLAR = {
    "Continuity": "analytical",
    "Reciprocity": "collaborative",
    "Sovereignty": "exploratory",
}


def seed_project(db: Session) -> Project:
    project = db.get(Project, "sim-project")
    if project:
        return project

    project = Project(
        id="sim-project",
        name="Simulation Project",
        objective="Stress test constitutional governance",
        steps='["ingest", "plan", "execute"]',
        risks='["invalid tasks", "low reciprocity"]',
        success_criteria='["M >= 0.6"]',
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _basin_for_step(c: float, r: float, s: float) -> str:
    dominant = max({"Continuity": c, "Reciprocity": r, "Sovereignty": s}, key={"Continuity": c, "Reciprocity": r, "Sovereignty": s}.get)
    return BASIN_BY_PILLAR[dominant]


def _correction_boost(c: float, r: float, s: float, violated: list[str]) -> tuple[float, float, float]:
    # This simulates post-governor correction effects while keeping values bounded.
    if "Continuity" in violated:
        c = min(1.0, c + 0.12)
    if "Reciprocity" in violated:
        r = min(1.0, r + 0.12)
    if "Sovereignty" in violated:
        s = min(1.0, s + 0.12)
    return c, r, s


def run_simulation(db: Session, weeks: int = 4) -> dict:
    project = seed_project(db)
    trajectory = []
    alert_events = []
    threshold_violations = []
    basin_transitions = []

    today = date.today()
    previous_basin = None

    for w in range(weeks):
        week_start = today - timedelta(days=today.weekday()) + timedelta(days=w * 7)
        for i in range(10):
            idx = f"w{w}-t{i}-{int(datetime.utcnow().timestamp())}-{random.randint(100,999)}"
            invalid = random.random() < (0.10 + (0.06 * w))
            from_signal = random.random() < 0.6
            has_metric = from_signal and (random.random() < max(0.2, 0.8 - (0.1 * w)))
            task = Task(
                id=idx,
                title=f"Sim task {idx}",
                project_id=None if invalid else project.id,
                priority=None if invalid else random.choice(PRIORITIES),
                status="Done",
                from_signal=from_signal,
                has_metric=has_metric,
                task_type=random.choice(TASK_TYPES),
                mode=random.choice(MODES),
                is_invalid=invalid,
                invalid_reason="simulated invalid" if invalid else "",
                correction_queue=invalid,
                completed_at=datetime.utcnow(),
            )
            db.add(task)

        db.commit()

        all_tasks = db.query(Task).all()
        all_projects = db.query(Project).all()
        profile = compute_profile(all_tasks, all_projects)

        c_pre = profile["continuity_score"]
        r_pre = profile["reciprocity_score"]
        s_pre = profile["sovereignty_score"]
        m_pre = min(c_pre, r_pre, s_pre)

        gov = governor_state(c_pre, r_pre, s_pre, THRESHOLD)
        violated = gov["violated_pillars"]
        if gov["active"]:
            c_post, r_post, s_post = _correction_boost(c_pre, r_pre, s_pre, violated)
        else:
            c_post, r_post, s_post = c_pre, r_pre, s_pre

        m_post = min(c_post, r_post, s_post)
        weakest = weakest_pillar(c_post, r_post, s_post)
        basin = _basin_for_step(c_post, r_post, s_post)
        _, alert = compute_alert(c_post, r_post, s_post)

        step_item = {
            "step": w,
            "timestamp": datetime.utcnow().isoformat(),
            "week_start": week_start.isoformat(),
            "C": round(c_post, 4),
            "R": round(r_post, 4),
            "S": round(s_post, 4),
            "M": round(m_post, 4),
            "pre_correction": {"C": c_pre, "R": r_pre, "S": s_pre, "M": m_pre},
            "post_correction": {"C": round(c_post, 4), "R": round(r_post, 4), "S": round(s_post, 4), "M": round(m_post, 4)},
            "governor_active": gov["active"],
            "violated_pillars": violated,
            "corrections": gov["corrections"],
            "weakest_pillar": weakest,
            "governor_alert": alert,
            "basin": basin,
        }
        trajectory.append(step_item)

        if gov["active"]:
            alert_events.append({"step": w, "timestamp": step_item["timestamp"]})
            threshold_violations.append({"step": w, "violated_pillars": violated})

        if previous_basin is not None and previous_basin != basin:
            basin_transitions.append({"step": w, "from": previous_basin, "to": basin})
        previous_basin = basin

        weekly = WeeklyProfile(
            id=f"weekly-{w}-{int(datetime.utcnow().timestamp())}",
            week_start=week_start,
            continuity_score=step_item["C"],
            reciprocity_score=step_item["R"],
            sovereignty_score=step_item["S"],
            stability_margin=step_item["M"],
            weakest_pillar=weakest,
            alert=alert,
        )
        db.add(weekly)
        db.commit()

    m_values = [step["post_correction"]["M"] for step in trajectory]
    mean_m = float(statistics.fmean(m_values)) if m_values else 0.0
    std_m = float(statistics.pstdev(m_values)) if len(m_values) > 1 else 0.0
    tau_empirical = max(0.0, mean_m - std_m)

    return {
        "tau_configured": THRESHOLD,
        "tau_empirical": round(tau_empirical, 4),
        "mean_M": round(mean_m, 4),
        "std_M": round(std_m, 4),
        "trajectory": trajectory,
        "alert_events": alert_events,
        "threshold_violations": threshold_violations,
        "basin_transitions": basin_transitions,
    }
