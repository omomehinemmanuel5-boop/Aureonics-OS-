from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.simulation_service import run_simulation

router = APIRouter()


@router.post("/simulate")
def simulate(
    steps: int = 30,
    alpha: float = 0.4,
    k: float = 2.0,
    dt: float = 0.05,
    seed: int | None = None,
    db: Session = Depends(get_db),
):
    return {
        "steps": steps,
        "profiles": run_simulation(db, steps=steps, alpha=alpha, k=k, dt=dt, seed=seed),
    }
