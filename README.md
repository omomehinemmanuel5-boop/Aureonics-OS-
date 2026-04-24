# Aureonics-OS

Aureonics-OS is a FastAPI-based **constitutional governance engine** and audit dashboard for the Aureonics triad:

- **Continuity (C)** → context coherence persistence
- **Reciprocity (R)** → information equilibrium
- **Sovereignty (S)** → lawful adaptive variance

The platform computes a live constitutional state, tracks stability over time, and exposes both API and dashboard surfaces to inspect how governance logic behaves in practice.

---

## Why this repo exists

This is not just a paper companion. It is an executable prototype that lets you:

- calculate live C/R/S constitutional scores,
- monitor the **stability margin** (`M = min(C, R, S)`),
- apply governor interventions when the system drifts,
- and inspect receipts through a frontend audit interface.

---

## Core capabilities

### 1) Constitutional state tracking
- Computes C/R/S signals from workflow and metric inputs.
- Classifies state into operating bands (stable/watch/intervention/collapse-risk).
- Exposes policy hints for routing and remediation.

### 2) Governor logic
- Detects weakest pillar and deficits.
- Produces correction plans and governance pressure indicators.
- Supports queue-based correction workflows.

### 3) Simulation services
- Runs governed and unguided dynamics.
- Supports adaptive and parameterized simulation endpoints.
- Generates comparative outputs for stress testing.

### 4) Praxis + dashboard auditing
- Stores/reads constitutional receipts from SQLite (`praxis.db` by default).
- Exposes `/praxis`, `/praxis/summary`, and `/praxis/run`.
- Serves a dashboard at `/` and `/dashboard` for real-time interface inspection.

---

## Architecture at a glance

```text
app/
  controllers/
    routes.py               # workflow, governance, panels, profile
    simulation_routes.py    # simulation APIs
    cbf_routes.py           # CBF-focused simulation comparisons
  models/
    entities.py
    schemas.py
  services/
    governor_service.py
    lex_service.py
    metrics_service.py
    profile_service.py
    simulation_service.py
    workflow_service.py
  static/
    index.html              # Sovereign Audit Interface frontend
  database.py
  main.py                   # app wiring + praxis endpoints + dashboard routes
tests/
docs/
```

---

## API surface

### Workflow and governance
- `POST /signal`
- `POST /project`
- `POST /task`
- `PATCH /task/{task_id}`
- `GET /tasks/invalid`
- `GET /profile`
- `GET /alerts`
- `GET /governor`
- `GET /governor/policy`
- `GET /weekly-profile`
- `GET /corrections/queue`
- `POST /corrections/apply?limit=5`

### Analytical panels
- `GET /panels/analytical`
- `GET /panels/collaborative`
- `GET /panels/exploratory`

### Metric probes
- `POST /test/continuity`
- `POST /test/reciprocity`
- `POST /test/sovereignty`

### Simulation
- `POST /simulate?steps=150&alpha=0.5&k=4.0&dt=0.05`
- `GET /simulate_adaptive`
- `POST /simulate_adaptive`
- `GET /cbf/simulate`
- `GET /cbf/compare`
- `GET /cbf/multi_seed`

### Praxis and dashboard
- `GET /` (dashboard)
- `GET /dashboard` (dashboard)
- `GET /praxis`
- `GET /praxis/summary`
- `POST /praxis/run`

---

## Quick start

### 1) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Run the app

```bash
uvicorn app.main:app --reload
```

### 4) Open interfaces

- Swagger docs: `http://127.0.0.1:8000/docs`
- Dashboard: `http://127.0.0.1:8000/dashboard`

---

## Minimal usage flow

### Create a project

```json
POST /project
{
  "id": "p1",
  "name": "Governor Build",
  "objective": "Build a constitutional adaptive governor",
  "steps": ["design", "implement", "test"],
  "risks": ["metric drift", "weak benchmarks"],
  "success_criteria": ["M >= tau", "recovery under stress"]
}
```

### Add a task

```json
POST /task
{
  "id": "t1",
  "title": "Refine governor logic",
  "project_id": "p1",
  "priority": "High",
  "status": "Todo",
  "from_signal": true,
  "has_metric": true,
  "task_type": "architecture"
}
```

### Inspect constitutional state
- `GET /profile`
- `GET /governor`
- `GET /governor/policy`

### Run praxis for a prompt

```json
POST /praxis/run
{
  "prompt": "Evaluate this proposal under continuity, reciprocity, and sovereignty constraints."
}
```

### Review receipts
- `GET /praxis`
- `GET /praxis/summary`

---

## Runtime and data notes

- Default Praxis database file is `praxis.db`.
- You can override database path with `DB_PATH` environment variable.
- `/praxis/run` can return HTTP `451` when the kernel refuses due to constitutional constraints.

---

## Project maturity

This remains a **research-grade prototype** with strong paper-to-code alignment and a practical governance API/dashboard loop.

Best current use:
- constitutional experimentation,
- governed-vs-unguided simulation analysis,
- and operator-facing audit of C/R/S behavior over time.

