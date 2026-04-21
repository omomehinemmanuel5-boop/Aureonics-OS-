# Aureonics Governor Engine

A research-grade prototype of a **constitutional governor engine** implementing the "Aureonics triad" — **Continuity (C)**, **Reciprocity (R)**, **Sovereignty (S)** — with Control Barrier Function (CBF) safety guarantees, an adaptive governor, and a basin intelligence layer that shapes convergence toward meaningful interior structure.

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
    cbf_service.py          # CBF + adaptive governor + basin intelligence
    simulation_service.py   # Legacy adaptive governor with preemptive buffer
    governor_service.py     # Base governor engine
    metrics_service.py      # Triad metric computation
  static/
    index.html              # Full dashboard (Chart.js, dark scientific theme)
  database.py               # SQLAlchemy engine and session setup
  main.py                   # Application entry point, mounts static files
```

## Running the Application

```
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

Dashboard served at `/` and `/dashboard`.

## Full Update Step (per simulation tick)

```
dx = replicator_dynamics + θ(t) * governor_force + u_basin
CBF enforcement applied LAST
```

1. **Intrinsic dynamics** — replicator + bounded mass-conserving Gaussian noise
2. **Governor force** — G_i = k(φ_i − φ̄), scaled by adaptive gain θ(t)
3. **Basin force** — gradient descent on Φ, simplex-projected, force-capped
   - Safety interaction rule: basin force zeroed when min(x) < 0.1
   - Descent guard: basin force halved if Φ would increase
4. **CBF filter** — discrete-time QP guarantees min(x_next_i) ≥ τ_cbf exactly
5. **Simplex projection** — mass-conserving normalization

## Key Features

### Safety
- **Guarantee:** min(C, R, S) ≥ τ_cbf = 0.05 for all t, all seeds
- **Method:** Exact discrete-time CBF (analytic QP solver for n=3)
- Validated over 8 random seeds: `all_seeds_safe = True`

### Basin Intelligence Layer
- **Φ(x) = −w₁·CCP + w₂·(IEC − IEC_target)²** (lower = better)
- **CCP** (Constitutional Coherence Profile): 1 at centroid, 0 at corners
- **IEC** (Internal Energy Coherence): 3·min(x), measures distance from collapse
- Basin force = −∇Φ projected onto tangent plane of simplex, λ=0.2, capped at 1.0
- **Directional gain** = Φ_initial − Φ_final > 0 confirms convergence

### Adaptive Governor
- Preemptive buffer δ=0.12 activates before τ breach
- θ rises under stress, decays toward θ₀=1.0 when stable
- θ ∈ [0.1, 5.0] bounded

### Dashboard Sections
| Section | Contents |
|---------|----------|
| Simulation Controls | seed, steps, alpha, dt, CBF toggle |
| Basin Intelligence (sidebar) | external signal, IEC target inputs |
| Constitutional State | min M, final θ, current basin badge |
| Safety Monitor | violations, recovery time, CBF HOLDS/BROKEN |
| Basin Intelligence | Φ_init, Φ_final, directional gain, basin timeline strip |
| Metrics & Outputs | Pillar chart (C/R/S), θ(t), M(t), Φ(t) charts |
| Multi-Seed Test | 8-seed grid with safety + directional gain per seed |

## CBF Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| τ_cbf | 0.05 | Hard safety floor |
| TAU_GOV | 0.25 | Governor activation threshold |
| θ₀ | 1.0 | Baseline adaptive gain |
| θ ∈ | [0.1, 5.0] | Gain bounds |
| α_θ | 0.8 | Gain increase rate |
| β_θ | 0.05 | Gain decay rate |
| λ_basin | 0.2 | Basin force gain |
| margin cutoff | 0.1 | Basin force zeroed below this |
| noise σ | 0.08 | Stochastic forcing std |
| noise clip | 0.15 | Noise saturation bound |

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (defaults to in-memory SQLite)

## Dependencies

See `requirements.txt`. Key packages: fastapi, uvicorn, sqlalchemy, pydantic, psycopg2-binary, gunicorn, aiofiles.
