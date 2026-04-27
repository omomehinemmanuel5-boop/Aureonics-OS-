# Aureonics / Lex SaaS Architecture Freeze

**Date:** April 27, 2026  
**Status:** Approved baseline for execution  
**Objective:** Freeze product boundaries so build effort aligns with conversion, trust, and monetization.

## 1) Product Position (locked)

Aureonics is **not** a generic AI dashboard. It is an **AI behavior governance layer** that sits between user intent and model output, ensuring results are safe, stable, and explainable before reaching end users.

## 2) System Layers (locked)

1. **Landing Layer (Acquisition):** `/` marketing page only
2. **Product UI Layer (Activation):** `/app` or `/dashboard` interactive experience
3. **API Layer (Execution):** `/lex/run`, `/praxis/run`, health/trace endpoints
4. **Intelligence Layer (Governance):** kernel, safety, intervention, stability logic
5. **Memory Layer (Learning):** retrieval + storage of governed interaction history

## 3) Response Contract (locked)

All primary execution endpoints must preserve this contract:

```json
{
  "raw_output": "",
  "governed_output": "",
  "final_output": "",
  "intervention": "",
  "intervention_reason": "",
  "semantic_diff_score": 0.0,
  "M": 0.0
}
```

## 4) Current-to-Target Mapping

This mapping preserves existing behavior while clarifying ownership by layer.

| Target Layer | Current Code Anchors | Target Direction |
|---|---|---|
| Landing | static UI served from app assets | move marketing to dedicated `/landing` directory and route |
| Product UI | `app/static/*`, dashboard routes | keep interactive demo in `/app` scope |
| API | `app/main.py` execution endpoints + controllers | split into `app/api` routers by domain |
| Intelligence | `sovereign_kernel_v2.py`, safety/governor logic | consolidate under `app/core` interfaces |
| Memory | `lex_memory/*`, Supabase migrations | align package naming to `memory_engine` abstraction |

## 5) Non-Goals (freeze protection)

- No new endpoint surface area unless required for contract parity.
- No pricing/entitlement complexity implementation during this phase.
- No model retraining work; memory stays retrieval-and-governance only.
- No additional dashboard analytics modules before acquisition path is clean.

## 6) Release Gates

A phase is complete only if all checks pass:

1. `pytest tests/test_lex_api_routes.py`
2. `pytest tests/test_import_safety.py`
3. `pytest tests/test_contract.py` (or equivalent schema-lock test)
4. Landing route returns marketing-only page with no internal dashboard leakage.
5. `/lex/run` and `/praxis/run` still return the locked response contract.

## 7) Execution Order (strict)

1. Freeze architecture (this document).
2. Create folder boundaries (`/landing`, `/app`, `/api`, `/core`, `/memory`) without changing behavior.
3. Ship landing page first and route `/` to acquisition content.
4. Run conversion experiments on landing CTA and demo click-through.
5. Iterate product UI only after landing conversion baseline is established.

## 8) Operational Success Metric

The primary near-term metric is:

**Landing clarity × demo simplicity × visible trust signal quality**

This outranks adding more governance internals during the current phase.
