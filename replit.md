# Aureonics Governor Engine

A research-grade prototype of a **constitutional governor engine** implementing the "Aureonics triad" — **Continuity**, **Reciprocity**, **Sovereignty** — with Control Barrier Function (CBF) safety guarantees and an adaptive governor that maintains pillar health under stochastic forcing.

## Technologies

- **Language:** Python 3.12
- **Web Framework:** FastAPI
- **Web Server:** Uvicorn (dev) / Gunicorn (production)
- **Database:** SQLAlchemy 2.0 with PostgreSQL (Replit built-in) or SQLite fallback
- **Validation:** Pydantic 1.10
- **Frontend:** Vanilla JS + Chart.js (served via FastAPI StaticFiles)

## Project Structure

```
app/
  controllers/
    routes.py               # Core governor routes
    simulation_routes.py    # Adaptive simulation endpoint (/simulate_adaptive)
    cbf_routes.py           # CBF safety endpoints (/cbf/simulate, /cbf/compare, /cbf/multi_seed)
  models/                   # SQLAlchemy entities and Pydantic schemas
  services/
    cbf_service.py          # CBF safety filter with discrete-time QP guarantee
    simulation_service.py   # Adaptive governor with preemptive buffer
    governor_service.py     # Base governor engine
    metrics_service.py      # Triad metric computation
  static/
    index.html              # Full dashboard (Chart.js, dark GitHub theme)
  database.py               # SQLAlchemy engine and session setup
  main.py                   # Application entry point, mounts static files
```

## Running the Application

The app runs on port 5000 via the "Start application" workflow:
```
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

The dashboard is served at `/` and `/dashboard`.

## Key Features

### Aureonics Triad
- **Continuity (C)**, **Reciprocity (R)**, **Sovereignty (S)** on the probability simplex
- Mass-conserving replicator dynamics with bounded stochastic noise

### Adaptive Governor (Section 11)
- Pillar deviation φ_i = max(0, τ - x_i), mass-conserving G_i = k(φ_i - φ̄)
- Preemptive buffer δ=0.12 activates governor before τ breach
- Achieves: time-below-threshold ≤ 5, avg recovery time ≤ 2

### CBF Safety Module (`app/services/cbf_service.py`)
- **Safety guarantee:** min(C, R, S) ≥ τ_cbf = 0.05 for all t
- **Algorithm:** Discrete-time CBF (exact QP projection), analytically solved for n=3
- Handles mass conservation exactly without a numerical QP solver
- Validated over 8 random seeds — all_seeds_safe = True
- Structured for future upgrade to full Quadratic Program controller

### Dashboard (`/dashboard`)
- Pillar values chart (C, R, S) with safety floor line
- Adaptive gain θ(t) chart
- Stability margin M(t) = min(C, R, S) chart
- Multi-seed safety test panel (8 seeds, pass/fail cards)
- Interactive controls: seed, steps, alpha, dt, CBF on/off toggle

## CBF Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| τ_cbf | 0.05 | Hard safety floor |
| γ | 5.0 | CBF decay rate |
| θ₀ | 1.0 | Baseline adaptive gain |
| θ ∈ | [0.1, 5.0] | Gain bounds |
| α_θ | 0.8 | Gain increase rate |
| β_θ | 0.05 | Gain decay rate |
| noise σ | 0.08 | Stochastic forcing std |
| noise clip | 0.15 | Noise saturation bound |

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (defaults to in-memory SQLite)

## Dependencies

See `requirements.txt`. Key packages: fastapi, uvicorn, sqlalchemy, pydantic, psycopg2-binary, gunicorn, aiofiles.
