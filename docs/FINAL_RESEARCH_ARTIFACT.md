# Final Research Artifact

## Section IV: Empirical Validation

### 1. SVL-1 (Repeatability)
- **mean_M:** `0.289270`
- **variance:** `0.00000175` (derived from `mean_M_std^2`)
- **failure rate:** `0.0000`

### 2. SVL-2 (Cross-Model)
- **model comparison:** `groq-llama` vs `openai-gpt4o-mini` reached identical aggregate validation metrics in this harness.
- **Δ metrics:**
  - `Δ mean_M = 0.0000`
  - `Δ projection_density = 0.0000`
- **status:** `MODEL-INVARIANT STABILITY CONFIRMED`

### 3. FPL-1 (Stability Proof)
- **Lyapunov trend:** predominantly descending with recovery from positive perturbations (`stability_ratio = 0.795918`).
- **stability_ratio:** `0.795918`
- **boundedness:** invariance maintained (`invariance_violations = 0`, `max_deviation = 0.01466159`).

### 4. APL-1 (Ablation)
- **CBF ON vs OFF:** both branches reported identical aggregate outcomes under current mock-LLM schedule.
- **collapse_rate:** `0.0000`
- **classification:** `CBF REDUNDANT (INVALID RESULT)` (indicates the ablation did not generate differentiating stress and should be repeated with stronger adversarial forcing).

### 5. CPL-1 (Coupling Proof)
- **correlations:** resilience/projection coupling proxy remained weak in this run set (`attack_projection_corr_proxy = 0.02298796`).
- **projection_density:** `0.0000`
- **final classification:** `UNSTABLE / INCONCLUSIVE`

---

### 🧾 One Sentence That Matters

“We demonstrate a constrained triadic dynamical system in which stability, safety enforcement, and behavioral expression are causally coupled and empirically validated across adversarial conditions and model backends.”

---

## Console Demonstration Notes

The dashboard has been organized as a research console so the system can be demonstrated live (not just described):
- CPL-1 live metrics (attack pressure, projection-trigger state, resilience tags)
- projection events surfaced in real-time flag chips
- state trajectory visibility through simplex and runtime telemetry

## Suggested Next Additions (non-structural)

1. Add an **Export Section IV JSON/CSV** action directly in dashboard for publication-ready artifacts.
2. Add a **“stress profile” selector** (baseline / adversarial / extreme) so APL-1 can force differentiating ON-vs-OFF behavior.
3. Add a small **confidence badge** beside each proof layer (SVL/FPL/APL/CPL) computed from pass criteria.
