# Aureonics Repo Rationalization + Productization Plan (April 29, 2026)

## Executive take: what to keep, what to cut, what to sell now

You currently have **two overlapping products** in one repo:
1. A Python/FastAPI “Lex API” surface (`app/`) with governance endpoints.
2. A Next.js SaaS frontend (`frontend/`) with pricing/checkout UX.

You also have substantial research/simulation artifacts mixed into the same root.

**Fastest path to revenue:** package this as **Lex Aureon Trust Visibility Pilot** with one clear deploy target, one demo flow, one pricing page, one checkout/invoice path, and one procurement pack.

---

## 1) Repository triage matrix (Keep / Archive / Remove)

> Rule used: If it directly supports customer demo, pilot delivery, security/procurement proof, billing, or production reliability in the next 30 days → KEEP. If useful but not required for first sales → ARCHIVE (move under `archive/`). If duplicate export/binary clutter → REMOVE from git and store externally.

### A. Core product runtime

| Path | Decision | Why |
|---|---|---|
| `app/` | **KEEP** | Current FastAPI product surface and static app UI used in docs/readme. |
| `requirements.txt` | **KEEP** | Core runtime dependency lock. |
| `Procfile`, `render.yaml`, `docker-compose.yml` | **KEEP** | Deployment paths and fallback run options. |
| `frontend/` | **KEEP (conditional)** | Keep only if this is your chosen go-to-market UI; otherwise archive to avoid split focus. |
| `frontend/tests/` + `vitest.config.ts` | **KEEP** | Maintains confidence on SaaS UX and output panels. |

### B. Enterprise/governance expansion modules

| Path | Decision | Why |
|---|---|---|
| `lex_aureon/backend/*` | **ARCHIVE (phase-2)** | Valuable microservice direction, but too heavy for immediate sales unless already deployed. |
| `packages/contracts/*` | **KEEP** | Contract files can support enterprise credibility and integrations. |
| `supabase/migrations/*` | **KEEP** | Tenant/procurement data model support for enterprise pilots. |
| `services/enterprise_agent/*` | **ARCHIVE (phase-2)** | Interesting differentiator, not required to close first pilots quickly. |
| `services/compliance/*` | **KEEP** | Can power trust/security story and controls evidence. |

### C. Research/simulation/testing assets

| Path | Decision | Why |
|---|---|---|
| `tests/` | **KEEP (split)** | Keep tests covering API/governance/product behavior; archive long-horizon research tests into `tests_research/`. |
| `scripts/run_simulation.py`, `tests/sss50_final.py`, `semantic_bridge_ab_results.json`, `simulation_output.json` | **ARCHIVE** | Useful for R&D proof, but clutter for customer-facing repo. |
| `svl_validation.py`, `tests/ablation_test.py` | **ARCHIVE** | Research validation, not required for shipping pilots. |

### D. Sales/procurement collateral

| Path | Decision | Why |
|---|---|---|
| `docs/procurement_pack/*` | **KEEP** | Critical to enterprise sales cycles and security review readiness. |
| `docs/FIRST_SALES_PLAYBOOK.md`, `docs/SAAS_LAUNCH.md`, `README.md` | **KEEP + consolidate** | Core GTM messaging but currently fragmented. |
| `docs/NEXT_STEP_PLAN.md`, `docs/AUTONOMOUS_GROWTH_ENGINE.md`, duplicates | **ARCHIVE** | Keep history but reduce decision fatigue. |

### E. Large binaries/exports in git root

| File | Decision | Why |
|---|---|---|
| `Aureonics_Section11_Final_Formatted.docx` | **REMOVE from git** | Heavy academic artifact, not product-critical. |
| `Aureonics_Final_Paper_Emmanuel_KingArxiv .pdf` | **REMOVE from git** | Keep as external link or release asset. |
| `ReplitExport-omomehinemmanue.tar.gz`, `Aureonics-OS-preupload-master-v2.zip` | **REMOVE from git ASAP** | Bloats repo and slows CI/clone; move to object storage. |

---

## 2) Productization architecture decision (pick one and execute)

## Decision needed this week

### Option A (recommended for speed): **FastAPI-first**
- Treat `app/main.py` + static dashboard as production product.
- Keep Next.js frontend as future upgrade or marketing mirror.
- Advantage: one runtime, less integration risk, faster demo-to-pilot motion.

### Option B: **Next.js-first**
- Frontend is primary customer touchpoint.
- Python API becomes backend-only service.
- Advantage: better SaaS UX and Stripe workflow.

**Do not run both as equal primaries.** That ambiguity will cost velocity and sales confidence.

---

## 3) “Sell ASAP” packaging (what to ship in 7 days)

## Day 1–2: Product hardening baseline
- Freeze one public API contract (`POST /lex/run`, auth, pricing, health).
- Add deterministic demo payload endpoint with one “intervention happened” scenario.
- Create single `.env.example` for all required runtime variables.
- Add uptime and error logging for `/lex/run`.

## Day 3–4: Commercial readiness
- Publish one canonical pricing page (free/pro/enterprise + pilot CTA).
- Implement one checkout path (manual invoice OR Stripe, not both messaging-heavy).
- Add procurement quick-send bundle:
  - architecture one-pager
  - security whitepaper
  - DPA
  - questionnaire

## Day 5–7: Sales execution assets
- Produce 3 vertical demo scripts (Legal Ops, Procurement, Support Escalations).
- Generate 1 “trust receipt” export format (input hash, output hash, intervention reason, M score).
- Build outbound kit:
  - one-page PDF overview
  - 10-email sequence
  - live demo booking CTA

---

## 4) Cleanup operations checklist (engineering)

1. Create top-level folders:
   - `product/` (runtime)
   - `docs/` (customer-facing + internal concise)
   - `archive/` (research + deprecated assets)
2. Move non-critical experimental folders/files into `archive/` with date stamp.
3. Remove large binary exports from git history (use BFG or `git filter-repo`).
4. Add CI lanes:
   - backend API tests
   - frontend tests (if frontend kept active)
   - lint + import safety checks
5. Add `OWNERSHIP.md`:
   - API owner
   - Frontend owner
   - Sales ops owner
   - Security questionnaire owner

---

## 5) Monetization offers to launch immediately

### Offer 1: Trust Visibility Pilot (recommended)
- **Price:** $7.5k–$15k/month
- **Term:** 2–4 weeks
- **Deliverables:** governed run telemetry, weekly trust report, risk findings readout

### Offer 2: API Governance Starter
- **Price:** $1.5k–$3k/month
- **Term:** monthly
- **Deliverables:** run quota + intervention metrics dashboard + email support

### Offer 3: Enterprise Procurement-Ready
- **Price:** $25k+/quarter
- **Deliverables:** SSO/SAML roadmap, custom policy controls, audit export integration

---

## 6) What is not needed *right now* for first revenue

- Multi-service decomposition across many `lex_aureon/backend/*` services (unless already productionized).
- Deep research benchmark publication loops in the main repo branch.
- Multiple overlapping GTM docs with different narratives.
- Large raw exports and zipped snapshots in source control.

These are strategic assets, but they are **not first-customer blockers**.

---

## 7) Immediate next 10 actions (owner can execute today)

1. Pick product primary: FastAPI-first vs Next.js-first.
2. Declare “single source of truth” README and deprecate conflicting docs.
3. Create `archive/2026-04-29/` and move non-selling artifacts there.
4. Remove root binaries/zips from git tracking.
5. Freeze pilot package + pricing in one page.
6. Add trust receipt export endpoint/spec.
7. Record 5-minute live demo video.
8. Build 50-account ICP prospect list.
9. Send 20 outbound messages with demo link.
10. Target 5 discovery calls in 7 days.

---

## 8) KPI dashboard for the next 30 days

Track weekly:
- # outbound messages sent
- # demos booked
- demo → pilot conversion rate
- average intervention rate in demos
- # procurement packets requested
- time from first demo to paid pilot

If a metric is not improving weekly, simplify the product story further.
