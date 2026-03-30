# Aureonics Governor Engine

A FastAPI backend implementing the Aureonics constitutional framework using paper-aligned metrics:

- Continuity → **CCP** (Context Coherence Persistence)
- Reciprocity → **IEC** (Information Equilibrium Constant)
- Sovereignty → **ADV** (Autonomous Decision Variance)

The service computes:

- Stability Margin: `M = min(C, R, S)` where `C=CCP`, `R=IEC`, `S=ADV`
- Governor alerts with `tau = 0.6`

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Core endpoints

- `POST /signal`
- `POST /project`
- `POST /task`
- `PATCH /task/{task_id}`
- `GET /profile`
- `GET /alerts`
- `GET /tasks/invalid`
- `POST /simulate?weeks=4`

## Experimental metric test endpoints

- `POST /test/continuity`
- `POST /test/reciprocity`
- `POST /test/sovereignty`

## Simulation output

`/simulate` returns structured trajectory data:

- Time series of `C`, `R`, `S`, `M`
- Governor alerts (`alert` boolean) and `alert_events`
- `weakest_pillar` per step
- Basin labels (`analytical`, `collaborative`, `exploratory`)
- `basin_transitions`


## Fallback export

When live dependency install is blocked, use `simulation_output.json` (synthetic fallback) which matches the `/simulate` output structure for downstream analysis.
