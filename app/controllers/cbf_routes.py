from fastapi import APIRouter

from app.services.cbf_service import simulate_cbf, simulate_cbf_comparison

router = APIRouter(prefix="/cbf", tags=["cbf"])


def _build_input_data(signal: float, iec_target: float) -> dict:
    return {"signal": signal, "iec_target": iec_target}


@router.get("/simulate")
def cbf_simulate(
    steps: int = 150,
    dt: float = 1.0,
    seed: int = 42,
    alpha: float = 0.5,
    cbf_enabled: bool = True,
    signal: float = 0.0,
    iec_target: float = 0.333,
):
    return simulate_cbf(
        steps=steps,
        dt=dt,
        seed=seed,
        alpha=alpha,
        cbf_enabled=cbf_enabled,
        input_data=_build_input_data(signal, iec_target),
    )


@router.get("/compare")
def cbf_compare(
    steps: int = 150,
    dt: float = 1.0,
    seed: int = 42,
    alpha: float = 0.5,
    signal: float = 0.0,
    iec_target: float = 0.333,
):
    return simulate_cbf_comparison(
        steps=steps,
        dt=dt,
        seed=seed,
        alpha=alpha,
        input_data=_build_input_data(signal, iec_target),
    )


@router.get("/multi_seed")
def cbf_multi_seed(
    steps: int = 150,
    dt: float = 1.0,
    alpha: float = 0.5,
    signal: float = 0.0,
    iec_target: float = 0.333,
):
    seeds = [0, 1, 7, 13, 21, 42, 99, 123]
    input_data = _build_input_data(signal, iec_target)
    results = []
    for seed in seeds:
        r = simulate_cbf(steps=steps, dt=dt, seed=seed, alpha=alpha, cbf_enabled=True, input_data=input_data)
        results.append({
            "seed": seed,
            "min_M": r["min_M"],
            "safety_violated": r["safety_violated"],
            "time_below_safe": r["time_below_safe"],
            "avg_recovery_time": r["avg_recovery_time"],
            "directional_gain": r["directional_gain"],
            "phi_initial": r["phi_initial"],
            "phi_final": r["phi_final"],
        })
    all_safe = all(not r["safety_violated"] for r in results)
    all_converging = all(r["directional_gain"] >= 0 for r in results)
    return {
        "results": results,
        "all_seeds_safe": all_safe,
        "all_seeds_converging": all_converging,
    }
