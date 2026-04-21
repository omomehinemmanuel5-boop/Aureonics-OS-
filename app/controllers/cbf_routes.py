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
    """
    Runs each seed both with and without the CBF governor so the
    user can see the clear difference between governed and ungoverned.
    """
    seeds = [0, 1, 7, 13, 21, 42, 99, 123]
    input_data = _build_input_data(signal, iec_target)
    results = []
    for seed in seeds:
        gov = simulate_cbf(steps=steps, dt=dt, seed=seed, alpha=alpha, cbf_enabled=True, input_data=input_data)
        ungov = simulate_cbf(steps=steps, dt=dt, seed=seed, alpha=alpha, cbf_enabled=False, input_data=input_data)
        results.append({
            "seed": seed,
            "governed": {
                "min_M": gov["min_M"],
                "safety_violated": gov["safety_violated"],
                "time_below_safe": gov["time_below_safe"],
                "directional_gain": gov["directional_gain"],
            },
            "ungoverned": {
                "min_M": ungov["min_M"],
                "safety_violated": ungov["safety_violated"],
                "time_below_safe": ungov["time_below_safe"],
            },
        })
    all_governed_safe = all(not r["governed"]["safety_violated"] for r in results)
    all_ungoverned_violated = all(r["ungoverned"]["safety_violated"] for r in results)
    return {
        "results": results,
        "all_governed_safe": all_governed_safe,
        "all_ungoverned_violated": all_ungoverned_violated,
    }
