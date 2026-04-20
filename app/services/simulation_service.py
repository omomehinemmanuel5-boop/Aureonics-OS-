import json
import random
from argparse import ArgumentParser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.entities import Project, WeeklyProfile
from app.services.governor_service import THRESHOLD

ALPHA = 0.4
KAPPA = 2.0
DT = 0.05
# NOTE:
# Large dt values (for example 1.0) can destabilize replicator dynamics and produce
# non-physical oscillations or collapse. Use a small dt for accurate simulation.
SWEEP_ALPHA = [0.2, 0.5, 1.0]
SWEEP_K = [2.0, 5.0, 10.0, 20.0]
NORMALIZATION_EPSILON = 1e-12
NEAR_ZERO_EPSILON = 0.01
NEAR_ZERO_THRESHOLD = 0.02


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


def compute_F(
    x: list[float],
    z: dict[str, float],
    alpha: float = ALPHA,
    symmetric_mode: bool = False,
) -> list[float]:
    c, r, s = x

    if symmetric_mode:
        common_a = 0.5
        f_c = common_a - alpha * (r + s)
        f_r = common_a - alpha * (c + s)
        f_s = common_a - alpha * (c + r)
    else:
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


def apply_safe_normalization(state_vector: list[float], epsilon: float = NORMALIZATION_EPSILON) -> tuple[list[float], bool]:
    clamped_state = [max(0.0, value) for value in state_vector]
    total = sum(clamped_state)
    if total <= epsilon:
        dim = len(clamped_state)
        return ([1.0 / dim] * dim), True
    return ([value / total for value in clamped_state]), False


def simulate_mode(
    *,
    steps: int,
    governor_enabled: bool,
    tau: float = THRESHOLD,
    dt: float = DT,
    alpha: float = ALPHA,
    k: float = KAPPA,
    seed: int | None = None,
    symmetry_test: bool = False,
) -> dict:
    if dt > 0.2:
        print("Warning: dt too large, may destabilize replicator dynamics")

    rng = random.Random(seed) if seed is not None else random
    x = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0] if symmetry_test else [0.34, 0.33, 0.33]
    trajectory = []
    violations = 0
    time_below_tau = 0
    recovery_times: list[int] = []
    violation_start: int | None = None
    collapse_detected = False
    near_collapse_count = 0
    non_physical_state_count = 0
    normalization_fallback_count = 0

    for t in range(steps):
        if symmetry_test:
            z = {"delta": 0.0, "uncertainty": 0.0}
        else:
            z = {
                "delta": rng.uniform(-0.5, 0.5),
                "uncertainty": rng.uniform(0.0, 1.0),
            }

        F = compute_F(x, z, alpha=alpha, symmetric_mode=symmetry_test)
        G = compute_G(x, tau=tau, k=k, governor_enabled=governor_enabled)
        # Keep near-zero protection symmetric so no pillar gets a built-in advantage.
        for i in range(3):
            if x[i] < NEAR_ZERO_THRESHOLD:
                G[i] += NEAR_ZERO_EPSILON

        dx = [F[i] + G[i] for i in range(3)]
        x = [x[i] + (dt * dx[i]) for i in range(3)]

        if all(xi <= 0.0 for xi in x):
            non_physical_state_count += 1
        x, used_fallback = apply_safe_normalization(x)
        if used_fallback:
            normalization_fallback_count += 1
            collapse_detected = True

        M = min(x)
        is_below = M < tau
        if is_below:
            time_below_tau += 1
            if violation_start is None:
                violation_start = t
                violations += 1
        elif violation_start is not None:
            recovery_times.append(t - violation_start)
            violation_start = None

        if M < 0.01:
            collapse_detected = True
        if M < 0.02:
            near_collapse_count += 1

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
    mean_c = sum(step["C"] for step in trajectory) / len(trajectory) if trajectory else 0.0
    mean_r = sum(step["R"] for step in trajectory) / len(trajectory) if trajectory else 0.0
    mean_s = sum(step["S"] for step in trajectory) / len(trajectory) if trajectory else 0.0
    if violation_start is not None:
        recovery_times.append(steps - violation_start)

    return {
        "trajectory": trajectory,
        "min_M": min_m,
        "avg_M": avg_m,
        "governor_enabled": governor_enabled,
        "alpha": alpha,
        "k": k,
        "dt": dt,
        "steps": steps,
        "seed": seed,
        "violations": violations,
        "time_below_tau": time_below_tau,
        "recovery_times": recovery_times,
        "max_recovery_time": max(recovery_times) if recovery_times else 0,
        "avg_recovery_time": (sum(recovery_times) / len(recovery_times)) if recovery_times else 0.0,
        "collapse_detected": collapse_detected,
        "near_collapse_count": near_collapse_count,
        "mean_C": mean_c,
        "mean_R": mean_r,
        "mean_S": mean_s,
        "non_physical_state_count": non_physical_state_count,
        "integration_anomaly_detected": non_physical_state_count > 0,
        "normalization_fallback_count": normalization_fallback_count,
    }


def parameter_sweep(*, steps: int, dt: float, tau: float, seed: int | None = None) -> list[dict]:
    sweep_results: list[dict] = []
    for alpha in SWEEP_ALPHA:
        for k in SWEEP_K:
            run_metrics = []
            for offset in range(3):
                run_seed = (seed + offset) if seed is not None else None
                result = simulate_mode(
                    steps=steps,
                    governor_enabled=True,
                    tau=tau,
                    dt=dt,
                    alpha=alpha,
                    k=k,
                    seed=run_seed,
                )
                run_metrics.append(result)

            avg_time_below_tau = sum(run["time_below_tau"] for run in run_metrics) / len(run_metrics)
            avg_recovery_time = sum(run["avg_recovery_time"] for run in run_metrics) / len(run_metrics)
            max_recovery_time = max(run["max_recovery_time"] for run in run_metrics)
            consistency_score = max(
                abs(run_metrics[i]["avg_recovery_time"] - run_metrics[0]["avg_recovery_time"])
                for i in range(1, len(run_metrics))
            ) if len(run_metrics) > 1 else 0.0

            sweep_results.append(
                {
                    "alpha": alpha,
                    "k": k,
                    "avg_time_below_tau": avg_time_below_tau,
                    "avg_recovery_time": avg_recovery_time,
                    "max_recovery_time": max_recovery_time,
                    "collapse_runs": sum(1 for run in run_metrics if run["collapse_detected"]),
                    "consistent_across_runs": consistency_score <= 1.0,
                    "meets_goal": (
                        max_recovery_time <= 3
                        and avg_time_below_tau <= 3
                        and sum(1 for run in run_metrics if run["collapse_detected"]) == 0
                    ),
                }
            )
    return sweep_results


def export_simulation_payload(payload: dict, output_path: str = "simulation_latest.json") -> str:
    path = Path(output_path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def run_simulation(
    db: Session,
    *,
    steps: int = 4,
    tau: float = THRESHOLD,
    dt: float = DT,
    alpha: float = ALPHA,
    k: float = KAPPA,
    seed: int | None = None,
    symmetry_test: bool = False,
) -> dict:
    seed_project(db)

    no_governor = simulate_mode(
        steps=steps,
        governor_enabled=False,
        tau=tau,
        dt=dt,
        alpha=alpha,
        k=k,
        seed=seed,
        symmetry_test=symmetry_test,
    )
    with_governor = simulate_mode(
        steps=steps,
        governor_enabled=True,
        tau=tau,
        dt=dt,
        alpha=alpha,
        k=k,
        seed=seed,
        symmetry_test=symmetry_test,
    )
    sweep = parameter_sweep(steps=steps, dt=dt, tau=tau, seed=seed)

    today = date.today()
    for step in with_governor["trajectory"]:
        week_start = today - timedelta(days=today.weekday()) + timedelta(days=step["t"] * 7)
        weekly = WeeklyProfile(
            id=f"weekly-{step['t']}-{int(datetime.now(timezone.utc).timestamp())}",
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
        "parameter_sweep": sweep,
    }


def cli() -> None:
    parser = ArgumentParser(description="Run Aureonics simulation and control sweep")
    parser.add_argument("--alpha", type=float, default=ALPHA)
    parser.add_argument("--k", type=float, default=KAPPA)
    parser.add_argument("--dt", type=float, default=DT)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--tau", type=float, default=THRESHOLD)
    parser.add_argument("--symmetry-test", action="store_true")
    args = parser.parse_args()

    if args.dt not in [0.05, 0.02, 0.01]:
        raise ValueError("dt must be one of: 0.05, 0.02, 0.01")

    payload = simulate_mode(
        steps=args.steps,
        governor_enabled=True,
        tau=args.tau,
        dt=args.dt,
        alpha=args.alpha,
        k=args.k,
        seed=args.seed,
        symmetry_test=args.symmetry_test,
    )
    print(payload)


if __name__ == "__main__":
    cli()
