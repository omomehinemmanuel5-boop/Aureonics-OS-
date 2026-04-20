# Aureonics Governor Engine

A research-grade prototype of a **constitutional governor engine** designed to maintain stability in adaptive systems. It implements the "Aureonics triad"—**Continuity**, **Reciprocity**, and **Sovereignty**—to monitor system health and intervene when stability thresholds are breached.

## Technologies

- **Language:** Python 3.12
- **Web Framework:** FastAPI
- **Web Server:** Uvicorn (dev) / Gunicorn (production)
- **Database:** SQLAlchemy 2.0 with PostgreSQL (Replit built-in) or SQLite fallback
- **Validation:** Pydantic 1.10

## Project Structure

```
app/
  controllers/    # API route definitions (routes.py, simulation_routes.py)
  models/         # SQLAlchemy entities and Pydantic schemas
  services/       # Core business logic (governor, metrics, simulation, etc.)
  database.py     # SQLAlchemy engine and session setup
  main.py         # Application entry point
docs/             # Documentation
scripts/          # Utility scripts
tests/            # Pytest test suite
```

## Running the Application

The app runs on port 5000 via the "Start application" workflow:
```
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

## Key Features

- **Triad Metrics:** Continuity (CCP), Reciprocity (IEC), Sovereignty (ADV)
- **Governor Engine:** Stability margin tracking and intervention system
- **Simulation Layer:** Replicator dynamics for modeling system drift

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (defaults to in-memory SQLite)

## Dependencies

See `requirements.txt`. Key packages: fastapi, uvicorn, sqlalchemy, pydantic, psycopg2-binary, gunicorn.
