import os
import sqlite3
import json

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.controllers.cbf_routes import router as cbf_router
from app.controllers.routes import router
from app.controllers.simulation_routes import router as simulation_router
from app.database import Base, engine
from sovereign_kernel_v2 import SovereignKernel

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aureonics Governor Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(simulation_router)
app.include_router(cbf_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

kernel = SovereignKernel()


class PraxisRunRequest(BaseModel):
    prompt: str
    disable_governor: bool = False


def _db_path() -> str:
    return os.environ.get("DB_PATH", "praxis.db")


def _ensure_praxis_table() -> None:
    with sqlite3.connect(_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS praxis_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_iso TEXT,
                input_hash TEXT,
                output_hash TEXT,
                pillar_c REAL,
                pillar_r REAL,
                pillar_s REAL,
                stability_margin REAL,
                constitutional INTEGER,
                recovering INTEGER,
                safety_projection_triggered INTEGER,
                adv_gain REAL,
                raw_response TEXT,
                governed_response TEXT,
                model TEXT,
                version TEXT
            )
            """
        )
        cursor.execute("PRAGMA table_info(praxis_receipts)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "safety_projection_triggered": "INTEGER DEFAULT 0",
            "adv_gain": "REAL DEFAULT 0",
            "raw_response": "TEXT",
            "governed_response": "TEXT",
            "projection_magnitude": "REAL DEFAULT 0",
            "raw_state": "TEXT",
            "projected_state": "TEXT",
        }
        for column, col_type in expected_columns.items():
            if column not in existing_columns:
                cursor.execute(f"ALTER TABLE praxis_receipts ADD COLUMN {column} {col_type}")
        conn.commit()


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse("app/static/index.html")


@app.get("/")
def root():
    return FileResponse("app/static/index.html")


@app.get("/praxis")
def praxis_receipts():
    _ensure_praxis_table()
    with sqlite3.connect(_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                timestamp_iso,
                pillar_c,
                pillar_r,
                pillar_s,
                stability_margin,
                constitutional,
                recovering,
                safety_projection_triggered,
                adv_gain,
                raw_response,
                governed_response,
                projection_magnitude,
                raw_state,
                projected_state,
                model,
                version
            FROM praxis_receipts
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()

    receipts = [
        {
            "id": row["id"],
            "timestamp_iso": row["timestamp_iso"],
            "pillar_snapshot": {
                "C": row["pillar_c"],
                "R": row["pillar_r"],
                "S": row["pillar_s"],
            },
            "stability_margin": row["stability_margin"],
            "constitutional": bool(row["constitutional"]),
            "recovering": bool(row["recovering"]),
            "safety_projection_triggered": bool(row["safety_projection_triggered"]),
            "adv_gain": row["adv_gain"],
            "raw_response": row["raw_response"],
            "governed_response": row["governed_response"],
            "projection_magnitude": row["projection_magnitude"] or 0.0,
            "raw_state": json.loads(row["raw_state"]) if row["raw_state"] else {},
            "projected_state": json.loads(row["projected_state"]) if row["projected_state"] else {},
            "model": row["model"],
            "version": row["version"],
        }
        for row in rows
    ]
    return {"count": len(receipts), "receipts": receipts}


@app.get("/praxis/summary")
def praxis_summary():
    _ensure_praxis_table()
    with sqlite3.connect(_db_path()) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_turns,
                SUM(CASE WHEN constitutional = 1 THEN 1 ELSE 0 END) AS constitutional_turns,
                SUM(CASE WHEN constitutional = 0 THEN 1 ELSE 0 END) AS refused_turns,
                AVG(pillar_c) AS mean_c,
                AVG(pillar_r) AS mean_r,
                AVG(pillar_s) AS mean_s,
                AVG(stability_margin) AS mean_m,
                MIN(stability_margin) AS min_m_ever
            FROM praxis_receipts
            """
        )
        stats = cursor.fetchone()
        cursor.execute(
            """
            SELECT recovering
            FROM praxis_receipts
            ORDER BY id DESC
            LIMIT 1
            """
        )
        latest = cursor.fetchone()

    total_turns = int(stats["total_turns"] or 0)
    constitutional_turns = int(stats["constitutional_turns"] or 0)
    refused_turns = int(stats["refused_turns"] or 0)
    return {
        "total_turns": total_turns,
        "constitutional_turns": constitutional_turns,
        "refused_turns": refused_turns,
        "mean_C": round(float(stats["mean_c"] or 0.0), 2),
        "mean_R": round(float(stats["mean_r"] or 0.0), 2),
        "mean_S": round(float(stats["mean_s"] or 0.0), 2),
        "mean_M": round(float(stats["mean_m"] or 0.0), 2),
        "min_M_ever": round(float(stats["min_m_ever"] or 0.0), 2),
        "currently_recovering": bool(latest["recovering"]) if latest else False,
    }


@app.post("/praxis/run")
def praxis_run(payload: PraxisRunRequest):
    result = kernel.run_cycle(payload.prompt)
    if result.get("status") == "Refused":
        raise HTTPException(status_code=451, detail=result)
    if result.get("status") == "Success":
        raw_response = result.get("raw_response") or result.get("response", "")
        governed_response = raw_response if payload.disable_governor else (
            result.get("governed_response") or result.get("response", "")
        )
        result["raw_response"] = raw_response
        result["governed_response"] = governed_response
        result["response"] = governed_response
        result["governor_disabled"] = payload.disable_governor
    return result
