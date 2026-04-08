import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.entities import Project, WeeklyProfile
from app.services.governor_service import THRESHOLD

ALPHA = 0.4
KAPPA = 0.9
DT = 0.05


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


def sample_environment() -> dict[str, float]:
    return {
        "delta": random.uniform(-0.5, 0.5),
        "uncertainty": random.uniform(0.0, 1.0),
    }


def a_C(z: dict[str, float]) -> float:
    return 0.5 + (0.25 * z["delta"]) - (0.15 * z["uncertainty"])


def a_R(z: dict[str, float]) -> float:
    return 0.5 - (0.15 * z["delta"]) + (0.2 * z["uncertainty"])


def a_S(z: dict[str, float]) -> float:
    return 0.5 - (0.1 * z["delta"]) + (0.1 * z["uncertainty"])


def compute_F(x: list[float], z: dict[str, float], alpha: float = ALPHA) -> list[float]:
    c, r, s = x

    f_c = a_C(z) - alpha * (r + s)
    f_r = a_R(z) - alpha * (c + s)
    f_s = a_S(z) - alpha * (c + r)

    f_bar = (c * f_c) + (r * f_r) + (s * f_s)

    F_c = c * (f_c - f_bar)
    F_r = r * (f_r - f_bar)
    F_s = s * (f_s - f_bar)

    return [F_c, F_r, F_s]


def compute_G(x: list[float], tau: float = THRESHOLD, k: float = KAPPA, governor_enabled: bool = True) -> list[float]:
    if not governor_enabled:
        return [0.0, 0.0, 0.0]

    phi = [max(0.0, tau - xi) for xi in x]
    phi_bar = sum(phi) / 3.0

    return [k * (phi[i] - phi_bar) for i in range(3)]


def simulate_mode(
    *,
    steps: int,
    governor_enabled: bool,
    tau: float = THRESHOLD,
    dt: float = DT,
) -> dict:
    x = [0.34, 0.33, 0.33]
    trajectory = []

    for t in range(steps):
        z = sample_environment()

        F = compute_F(x, z)
        G = compute_G(x, tau=tau, governor_enabled=governor_enabled)

        dx = [F[i] + G[i] for i in range(3)]
        x = [x[i] + (dt * dx[i]) for i in range(3)]

        total = sum(x)
        x = [xi / total for xi in x]

        M = min(x)

        trajectory.append(
            {
                "t": t,
                "C": x[0],
                "R": x[1],
                "S": x[2],
                "M": M,
            }
        )

    m_values = [step["M"] for step in trajectory]
    min_m = min(m_values) if m_values else 0.0
    avg_m = sum(m_values) / len(m_values) if m_values else 0.0

    return {
        "trajectory": trajectory,
        "min_M": min_m,
        "avg_M": avg_m,
        "governor_enabled": governor_enabled,
    }


def run_simulation(db: Session, weeks: int = 4) -> dict:
    seed_project(db)

    no_governor = simulate_mode(steps=weeks, governor_enabled=False, tau=THRESHOLD, dt=DT)
    with_governor = simulate_mode(steps=weeks, governor_enabled=True, tau=THRESHOLD, dt=DT)

    today = date.today()
    for step in with_governor["trajectory"]:
        week_start = today - timedelta(days=today.weekday()) + timedelta(days=step["t"] * 7)
        weekly = WeeklyProfile(
            id=f"weekly-{step['t']}-{int(datetime.utcnow().timestamp())}",
            week_start=week_start,
            continuity_score=round(step["C"], 4),
            reciprocity_score=round(step["R"], 4),
            sovereignty_score=round(step["S"], 4),
            stability_margin=round(step["M"], 4),
            weakest_pillar=min(
                {"Continuity": step["C"], "Reciprocity": step["R"], "Sovereignty": step["S"]},
                key={"Continuity": step["C"], "Reciprocity": step["R"], "Sovereignty": step["S"]}.get,
            ),
            alert="System stable" if step["M"] >= THRESHOLD else "Governor active",
        )
        db.add(weekly)
    db.commit()

    return {
        "mode_no_governor": no_governor,
        "mode_with_governor": with_governor,
    }
