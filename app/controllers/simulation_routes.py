from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.simulation_service import run_simulation

router = APIRouter()


@router.post("/simulate")
def simulate(weeks: int = 4, db: Session = Depends(get_db)):
    return {"weeks": weeks, "profiles": run_simulation(db, weeks=weeks)}
