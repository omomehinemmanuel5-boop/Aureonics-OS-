from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.controllers.cbf_routes import router as cbf_router
from app.controllers.routes import router
from app.controllers.simulation_routes import router as simulation_router
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aureonics Governor Engine")
app.include_router(router)
app.include_router(simulation_router)
app.include_router(cbf_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse("app/static/index.html")


@app.get("/")
def root():
    return FileResponse("app/static/index.html")
