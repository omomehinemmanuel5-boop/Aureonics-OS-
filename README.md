# LEX AUREON

**Lex Aureon is a real-time AI Trust Layer that makes model behavior observable, governable, and auditable.**

## LEX AUREON DUAL SYSTEM

Lex Aureon operates as both:

1. A theoretical AI governance framework (**Aureonics**)
2. A deployable AI trust and intervention product layer (**Lex Aureon**)

This README is split into:

- **SECTION A — THEORY (AUREONICS)**
- **SECTION B — PRODUCT (LEX AUREON)**
- **SECTION C — DEPLOYMENT & API**

---

## SECTION A — THEORY (AUREONICS)

### 2.1 Core Idea

Aureonics is a system for **observing, stabilizing, and governing AI behavioral drift using measurable state variables**.

The core assumption is simple: model behavior can shift over time or under adversarial prompts, so governance must be continuous, measurable, and actionable.

### 2.2 Core Variables (Simplified)

- **C (Constraint):** how well the model respects boundaries and safety constraints.
- **R (Reasoning):** how coherent and useful the model’s reasoning remains.
- **S (Stability):** how stable behavior is across changes in prompt conditions.
- **M = min(C, R, S):** the weakest-link score.

`M` represents system health and governs intervention behavior. When `M` degrades, governance pressure increases.

### 2.3 Concept of Governance

Aureonics governance is operational, not symbolic:

- AI is **not trusted blindly**.
- AI is **continuously observed**.
- Deviations **trigger intervention**.

This means trust is produced through runtime evidence, not assumptions.

---

## SECTION B — PRODUCT (LEX AUREON)

## LEX AUREON = AI TRUST & INTERVENTION LAYER

### 3.1 What It Does

Lex Aureon:

- runs any LLM prompt,
- compares **raw** vs **governed** output,
- detects instability or unsafe drift,
- optionally intervenes,
- returns a strict, auditable response contract.

### 3.2 Locked Output Structure

All production entry points are aligned to the same schema:

```json
{
  "raw_output": "",
  "governed_output": "",
  "final_output": "",
  "intervention": true,
  "intervention_reason": "",
  "M": 0.0,
  "semantic_diff_score": 0.0
}
```

### 3.3 Value Proposition

**Lex Aureon makes AI behavior observable, controllable, and auditable.**

### 3.4 Use Cases

- AI safety layer for applications
- enterprise AI auditing
- prompt risk detection
- LLM behavior transparency
- compliance logging and incident review

### Frontend Product Behavior

The dashboard is centered on product clarity:

- **RAW OUTPUT** panel
- **LEX GOVERNED** panel
- **FINAL OUTPUT** panel
- **INTERVENTION** badge

When intervention occurs, the system visibly explains why the output was modified.

### Demo Mode (Sales)

`DEMO_MODE = true` (UI toggle) emphasizes sales clarity by:

- exaggerating intervention explanation clarity,
- highlighting raw vs final differences,
- rendering a human-readable Lex verdict.

This is a presentation mode and not a change to backend governance logic.

### One-Click Share Flow

The share flow is built around a copy-ready card containing:

- prompt
- `raw_output` (shortened)
- `final_output`
- intervention badge
- `M` score
- Lex verdict sentence

CTA: **Copy Share Card**.

---

## SECTION C — DEPLOYMENT & API

### System Architecture

Runtime flow:

1. User prompt
2. LLM generates raw output
3. Lex evaluates state (`M`)
4. Intervention decision
5. Governed output generated
6. Final output returned

### API

#### `POST /lex/run`

Input:

```json
{ "prompt": "string", "bridge": true }
```

Output:

Structured JSON with the locked schema shown above.

#### Compatibility

`POST /praxis/run` returns the same exact response schema as `/lex/run`.

---

## Commercial Model

- **Free tier:** limited runs
- **Pro tier:** unlimited usage
- **API tier:** developer access
- **Enterprise tier:** compliance integration

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Dashboard: `http://127.0.0.1:8000/dashboard`

---

## Internal Research Notes

The following are internal validation systems used for development only and are not part of the product narrative:

- SSS-50
- SVL-2
- CPL-1
- FPL-1
- APL-1

---

## Final Product Intent

A new reader should immediately understand:

- what problem Lex Aureon solves,
- why runtime AI governance matters,
- how to integrate it,
- how the system monetizes.
