# LEX AUREON

**Real-time AI Trust, Safety, and Intervention Layer**

LEX AUREON is a **live AI behavior auditor** that makes model decisions transparent in real time.

For every prompt, operators can see:
1. **RAW model output**
2. **LEX-governed output**
3. **Final decision** (`SAFE` or `INTERVENED`)
4. **Why intervention happened**
5. **Session-level trust and stability metrics**

---

## Product Positioning

LEX AUREON is not a research dashboard. It is a deployable trust product for:
- AI teams proving safety controls to enterprise buyers,
- compliance and risk teams auditing AI behavior,
- platform operators monitoring intervention reliability,
- sales/demo teams showing governance value in minutes.

**What you sell:**
- AI transparency
- AI failure detection
- AI correction layer
- trust scoring

---

## Core Product Experience

### 1) Prompt-to-proof trust workflow
A user submits any prompt and immediately gets:
- **RAW output** (unaltered model behavior)
- **GOVERNED output** (post-governor correction)
- **FINAL decision badge** (`SAFE` vs `INTERVENED`)
- **intervention reason trace** (semantic drift / projection / stability trigger)

### 2) One-click demo flow
Use **🚀 Run Trust Demo** to execute a sales-ready sequence:
- safe prompt
- boundary prompt
- attack prompt

Then present:
- RAW vs LEX vs FINAL comparison
- intervention-rate snapshot
- clear evidence of corrective governance behavior

### 3) Session monetization signal
The **Session Insight** card summarizes:
- total prompts
- intervention rate %
- average `semantic_diff_score`
- system classification (`SAFE` / `STABLE` / `UNSTABLE`)

### 4) Exportable trust artifact
Export generates a **LEX TRUST REPORT** including:
- session summary
- stability metrics
- intervention breakdown
- system classification
- timestamp

Output format:
- machine-readable JSON
- human-readable summary block for customer handoff

### 5) Subscription-ready upsell structure
UI includes a placeholder for:

**Unlock Advanced Governance Insights**
- Extended research graphs
- Multi-session analytics
- API access logs

This supports future paid tiers without changing core governance logic.

---

## Technical Boundary (Locked Core)

The following are intentionally treated as protected governance kernel surfaces:
- triad logic
- CBF mechanics
- governor kernel behavior
- constitutional safety core

Product hardening should focus on:
- UX clarity
- traceability
- reporting/export
- operator confidence and buyer proof

---

## Quick Start

### 1) Create and activate virtual environment
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

### 4) Open local interfaces
- API docs: `http://127.0.0.1:8000/docs`
- Trust console: `http://127.0.0.1:8000/dashboard`

---

## Key API Endpoints

### Trust and governance runtime
- `POST /praxis/run`
- `GET /praxis`
- `GET /praxis/summary`
- `POST /praxis/run`
- `GET /praxis/health`

### Simulation and stress testing
- `POST /simulate`
- `GET /simulate_adaptive`
- `GET /cbf/simulate`
- `GET /cbf/compare`
- `GET /cbf/multi_seed`

---

## Sales Demo Script (5 Minutes)

1. **Open console** and state: “You will see what the model said, what LEX changed, and why.”
2. Click **Run Trust Demo**.
3. For safe prompt: emphasize pass-through behavior and trust consistency.
4. For boundary prompt: show partial corrections and explanation trace.
5. For attack prompt: show `🔴 LEX INTERVENED` and explicit behavior modification notice.
6. Open **Session Insight** and read intervention rate + classification.
7. Export **LEX TRUST REPORT** and frame it as compliance/customer proof.

---

## First Monetization Path

### Ideal first customers
- Teams shipping copilots into regulated environments
- AI-first SaaS companies needing trust telemetry for enterprise deals
- Integrators implementing governance wrappers around third-party LLM APIs

### Suggested entry offer
- **Pilot package (2–4 weeks):** runtime deployment + trust reporting + intervention tuning
- Deliverables: live console access, weekly trust report exports, intervention audit readout
- Expansion path: advanced analytics tier + API access logs + multi-session governance intelligence

---

## Environment Notes

- Set `GROQ_API_KEY` for live model execution on `/praxis/run`.
- Default local database: `praxis.db`.
- Override with `DB_PATH` environment variable.
- `/praxis/run` may return HTTP `451` when constitutional refusal triggers.

---

## Repository Layout

```text
app/
  controllers/
  services/
  models/
  static/
  main.py
tests/
docs/
```

---

## Status

LEX AUREON is now positioned as a **productized trust layer** with:
- real-time intervention transparency,
- operator-facing evidence,
- exportable customer proof,
- clear packaging for paid governance offerings.
