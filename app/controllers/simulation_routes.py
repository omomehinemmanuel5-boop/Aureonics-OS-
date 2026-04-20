from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.simulation_service import export_simulation_payload, run_simulation, simulate_adaptive_mode

router = APIRouter()


@router.get("/simulate_adaptive")
@router.post("/simulate_adaptive")
def simulate_adaptive(
    steps: int = 150,
    alpha: float = 0.5,
    dt: float = 1.0,
    seed: int = 42,
    tau: float = 0.15,
    delta: float = 0.12,
):
    result = simulate_adaptive_mode(steps=steps, alpha=alpha, dt=dt, seed=seed, tau=tau, delta=delta)
    return result


@router.post("/simulate")
def simulate(
    steps: int = 150,
    alpha: float = 0.5,
    k: float = 4.0,
    dt: float = 0.05,
    seed: int | None = None,
    export: bool = False,
    db: Session = Depends(get_db),
):
    profiles = run_simulation(db, steps=steps, alpha=alpha, k=k, dt=dt, seed=seed)
    governor_metrics = profiles.get("mode_with_governor", {})

    response = {
        "steps": steps,
        "alpha": alpha,
        "k": k,
        "dt": dt,
        "seed": seed,
        "normalization_fallback_count": governor_metrics.get("normalization_fallback_count", 0),
        "collapse_detected": governor_metrics.get("collapse_detected", False),
        "avg_recovery_time": governor_metrics.get("avg_recovery_time", 0.0),
        "time_below_tau": governor_metrics.get("time_below_tau", 0),
        "profiles": profiles,
    }
    if export:
        response["export_path"] = export_simulation_payload(response)
    return response
