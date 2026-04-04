import random
import statistics
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entities import Project, WeeklyProfile
from app.services.governor_service import THRESHOLD, compute_alert, governor_state, weakest_pillar

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
        success_criteria='["M >= tau"]',
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _normalize_simplex(c: float, r: float, s: float) -> tuple[float, float, float]:
    c = max(c, 1e-6)
    r = max(r, 1e-6)
    s = max(s, 1e-6)
    total = c + r + s
    return c / total, r / total, s / total


def _basin_for_step(c: float, r: float, s: float) -> str:
    dominant = max({"Continuity": c, "Reciprocity": r, "Sovereignty": s}, key={"Continuity": c, "Reciprocity": r, "Sovereignty": s}.get)
    return BASIN_BY_PILLAR[dominant]


def _intrinsic_update(c: float, r: float, s: float, delta: float, uncertainty: float) -> tuple[float, float, float]:
    # Continuity persistence avoids instant collapse if CCP-like signal goes weak.
    persistence = 0.88
    c_signal = (0.75 * c) + (0.25 * persistence * c)

    # Environmental instability introduces bounded irregular motion.
    r_signal = r + (0.12 * delta) - (0.05 * uncertainty)
    s_signal = s + (0.10 * uncertainty) - (0.04 * delta)

    c_next = c_signal + random.uniform(-0.03, 0.03)
    r_next = r_signal + random.uniform(-0.03, 0.03)
    s_next = s_signal + random.uniform(-0.03, 0.03)
    return _normalize_simplex(c_next, r_next, s_next)


def _apply_governor(c: float, r: float, s: float, violated: list[str]) -> tuple[float, float, float]:
    # Small targeted corrections (not hard overrides) to preserve basin motion.
    if "Continuity" in violated:
        c += 0.04
        r -= 0.02
        s -= 0.02
    if "Reciprocity" in violated:
        r += 0.04
        c -= 0.02
        s -= 0.02
    if "Sovereignty" in violated:
        s += 0.04
        c -= 0.02
        r -= 0.02
    return _normalize_simplex(c, r, s)


def run_simulation(db: Session, weeks: int = 4) -> dict:
    seed_project(db)

    trajectory = []
    alert_events = []
    threshold_violations = []
    basin_transitions = []

    today = date.today()
    previous_basin = None

    c, r, s = 0.34, 0.33, 0.33

    for w in range(weeks):
        week_start = today - timedelta(days=today.weekday()) + timedelta(days=w * 7)
        delta = random.uniform(-1.0, 1.0)
        uncertainty = random.uniform(0.0, 1.0)

        c_pre, r_pre, s_pre = _intrinsic_update(c, r, s, delta, uncertainty)
        m_pre = min(c_pre, r_pre, s_pre)

        gov = governor_state(c_pre, r_pre, s_pre, THRESHOLD)
        violated = gov["violated_pillars"]
        if gov["active"]:
            c_post, r_post, s_post = _apply_governor(c_pre, r_pre, s_pre, violated)
        else:
            c_post, r_post, s_post = c_pre, r_pre, s_pre

        c_post, r_post, s_post = _normalize_simplex(c_post, r_post, s_post)
        m_post = min(c_post, r_post, s_post)

        weakest = weakest_pillar(c_post, r_post, s_post)
        basin = _basin_for_step(c_post, r_post, s_post)
        _, alert = compute_alert(c_post, r_post, s_post)

        step_item = {
            "step": w,
            "timestamp": datetime.utcnow().isoformat(),
            "week_start": week_start.isoformat(),
            "delta": round(delta, 4),
            "uncertainty": round(uncertainty, 4),
            "C": round(c_post, 4),
            "R": round(r_post, 4),
            "S": round(s_post, 4),
            "M": round(m_post, 4),
            "pre_correction": {"C": round(c_pre, 4), "R": round(r_pre, 4), "S": round(s_pre, 4), "M": round(m_pre, 4)},
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

        c, r, s = c_post, r_post, s_post

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
