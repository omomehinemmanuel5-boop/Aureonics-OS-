from fastapi import FastAPI

from app.controllers.routes import router
from app.controllers.simulation_routes import router as simulation_router
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aureonics Governor Engine")
app.include_router(router)
app.include_router(simulation_router)


@app.get("/")
def root():
    return {"service": "Aureonics Governor Engine", "status": "running"}
