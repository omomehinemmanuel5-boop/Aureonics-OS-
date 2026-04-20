# Aureonics-OS

**A constitutional governor engine for adaptive stability.**

Aureonics-OS is a FastAPI backend that operationalizes the Aureonics triad:

- **Continuity** → **CCP** (Context Coherence Persistence)
- **Reciprocity** → **IEC** (Information Equilibrium Constant)
- **Sovereignty** → **ADV** (Autonomous Decision Variance)

The system treats adaptive behavior as a constitutional state on a triadic profile. It computes:

- constitutional scores for **C, R, S**
- **stability margin** `M = min(C, R, S)`
- a constitutional threshold `tau = 0.15`
- governor interventions when the system drifts toward violation or collapse

This repo is not just an API wrapper around a paper. It is an executable governor prototype for the Aureonics framework.

---

## What the system does

### 1. Tracks constitutional state
From tasks, projects, and signals, the engine estimates:

- **Continuity**: anchor retention and coherence persistence
- **Reciprocity**: exchange stability and input-output alignment
- **Sovereignty**: lawful decision variance under constraint

### 2. Computes a governor view
The governor identifies:

- weakest pillar
- violated pillars
- constitutional band (`stable-core`, `watch`, `intervention`, `collapse-risk`)
- governance pressure
- target operating mode
- structured correction plans
- live routing policy

### 3. Simulates governed dynamics
The simulation layer implements:

- replicator-style intrinsic dynamics
- threshold-driven governor correction
- simplex-preserving normalization
- recovery and collapse metrics
- parameter sweeps over `alpha` and `k`

### 4. Closes the loop
The workflow layer is now governor-aware:

- new tasks can inherit a governor-biased operating mode
- higher constitutional strain can force metric collection
- correction queue items can be converted into remediation tasks
- weekly profiles can be persisted as constitutional memory

---

## Repository structure

```text
app/
  controllers/
    routes.py
    simulation_routes.py
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
  database.py
  main.py
tests/
docs/
README.md
simulation_output.json
```

---

## Core architecture

### Workflow layer
Handles:

- signal ingestion
- project planning
- task routing
- execution updates
- invalid task detection and correction queueing
- governor-aware remediation creation

### Metrics layer
Implements:

- **CCP** with similarity, anchor coverage, and contradiction penalty
- **IEC** with exchange-ratio variance and input-output alignment
- **ADV** with lawful variance, transition rate, and compliance

### Governor layer
Converts profile scores into a constitutional control snapshot with:

- deficits by pillar
- weakest pillar
- intervention band
- governance pressure
- correction plans
- policy outputs for routing, review intensity, and signal handling

### Profile layer
Builds and persists the live constitutional snapshot used by the governor and weekly reporting.

### Simulation layer
Runs governed vs unguided comparative dynamics and writes weekly profiles.

---

## Endpoints

### Core workflow

- `POST /signal`
- `POST /project`
- `POST /task`
- `PATCH /task/{task_id}`
- `GET /tasks/invalid`

### Constitutional state

- `GET /profile`
- `GET /alerts`
- `GET /governor`
- `GET /governor/policy`
- `GET /weekly-profile`

### Correction loop

- `GET /corrections/queue`
- `POST /corrections/apply?limit=5`

### Experimental metric probes

- `POST /test/continuity`
- `POST /test/reciprocity`
- `POST /test/sovereignty`

### Simulation

- `POST /simulate?steps=150&alpha=0.5&k=4.0&dt=0.05`

---

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the docs at:

```text
http://127.0.0.1:8000/docs
```

---

## Minimal usage flow

### 1. Create a project

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

### 2. Add a task

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

### 3. Read the constitutional state

- `GET /profile`
- `GET /governor`
- `GET /governor/policy`

### 4. Apply queued corrections

- `GET /corrections/queue`
- `POST /corrections/apply`

---

## Simulation output

The simulation layer reports governed dynamics, including:

- `trajectory`
- `min_M`, `avg_M`
- `violations`
- `time_below_tau`
- `recovery_times`
- `collapse_detected`
- `near_collapse_count`
- `mean_C`, `mean_R`, `mean_S`
- `parameter_sweep`

Use this to compare governed and unguided behavior.

---

## Current maturity

This repo is best understood as a **research-grade prototype**.

Strong already:

- paper-to-code alignment
- executable governor logic
- metric pathways for the full triad
- simulation harness for stress testing
- persistence and API structure
- early closed-loop correction workflow

Still being hardened:

- richer benchmark scenarios
- tighter empirical validation of CCP / IEC / ADV
- stronger coupling between live workflow and closed-loop control
- dashboard and visualization layer
- experiment tracking and baseline reporting

---

## Roadmap

See:

- `docs/AUREONICS_SUCCESS_PATH.md`

That file defines the path from prototype to formal governor system:

1. formal hardening
2. metric hardening
3. benchmark suite
4. closed-loop governor behavior
5. public research/demo release

---

## Research basis

This repo is aligned with the Aureonics framework documents included in the project:

- `Aureonics_Final_Paper_Emmanuel_KingArxiv .pdf`
- `Aureonics_Section11_Final_Formatted.docx`

---

## Positioning

Aureonics-OS is building toward a measurable claim, not a vague brand statement:

> A governed triadic system can remain more stable, recoverable, and lawfully adaptive than an unguided one.

That is the standard this repo is trying to earn.
