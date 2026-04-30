# Lex API — Governed AI Responses

Lex API is a sellable SaaS surface for governed inference: paste a prompt, receive a stabilized final output, and scale usage by plan.

## First-Sales Positioning (April 27, 2026)

If your goal is to close first customers quickly, sell **trust + control** rather than generic model quality:

1. Show one risky prompt in `/dashboard`.
2. Let the pre-send invariance scanner flag risk before submit.
3. Run the prompt and show intervention + stability margin `M(t)`.
4. Export/share the corrected output as proof of governed execution.

This creates a concrete “before/after” demo that buyers understand in minutes.

## Product Surface

- **Landing page**: `/` (marketing only)
- **Dashboard**: `/dashboard` (minimal SaaS runner)
- **Core API endpoint**: `POST /lex/run`
- **Trust receipt export**: `POST /lex/trust-receipt`
- **Operational endpoints**: `GET /health`, `GET /pricing`, `GET /demo`
- **Auth endpoints**: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- **Stripe-ready stub**: `POST /billing/checkout` (auth required)

## Response Contract (`POST /lex/run`)

```json
{
  "raw_output": "string",
  "governed_output": "string",
  "final_output": "string",
  "intervention": true,
  "intervention_reason": "string",
  "semantic_diff_score": 0.0,
  "M": 0.0
}
```

## Trust Receipt Export (`POST /lex/trust-receipt`)

Generate an auditable trust receipt from a completed governed run. The receipt includes:

- Input/output SHA-256 hashes (`input_hash`, `raw_output_hash`, `governed_output_hash`, `final_output_hash`)
- Governance outcomes (`intervention`, `intervention_reason`, `semantic_diff_score`, `M`)
- Stability timeline (`raw` → `governed` → `final`)
- Integrity HMAC signature (`integrity_signature`) for tamper detection

Use this endpoint to produce buyer-facing trust artifacts for compliance and procurement review.

Frontend displays only:
- `final_output` (primary)
- `intervention` badge
- `M` score

`raw_output` and `governed_output` are available in **Developer mode** only.


## Customer-Ready Authentication

Lex API now includes first-party customer authentication for production pilots:

- `POST /auth/register` creates a customer account and returns a signed bearer token.
- `POST /auth/login` returns a new bearer token for existing users.
- `GET /auth/me` validates the token and returns account profile + active plan context.
- Paid plan execution (`x-subscription-plan: pro|enterprise`) requires a valid bearer token.
- `POST /billing/checkout` requires authentication to prevent anonymous invoice generation.

Use the returned token in `Authorization: Bearer <token>` for API and console runs.

## Pricing Model

- **Free**: 10 runs/day, watermark `Lex Demo`
- **Pro ($19/mo)**: 2,000 runs/month, no watermark, priority inference
- **Enterprise ($99+/mo)**: API access, bulk inference, governance tuning controls

Use `GET /pricing` for machine-readable plan metadata.

## Billing Layer (Manual Payment Mode)

`POST /billing/checkout`

```json
{
  "plan": "pro",
  "buyer_email": "buyer@example.com",
  "company_name": "Acme Corp",
  "seats": 3
}
```

Returns a manual invoice payload (invoice id, amount, due date, payment instructions, wire reference).
This is intentionally optimized for immediate pilot sales without Stripe dependency.


## Console UX Upgrades (Mobile + Keyboard Safe)

The dashboard console now includes a **keyboard-aware sensory dock** so critical safety signal data stays visible while typing on mobile:

- Sticky sensory rail on desktop + floating sensory dock on keyboard-open mobile states.
- Real-time intervention/risk/meaning telemetry mirrored into the dock.
- Inline auth controls in the console for immediate customer onboarding.

## Deployment (Render-safe)

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The app uses safe boot behavior:
- Import-time kernel failure does **not** block startup.
- `/health` returns `degraded: true` when bootstrap errors exist.

### Frontend routing mode (important)

By default, FastAPI serves the embedded frontend:
- `GET /` → `app/static/index.html`
- `GET /dashboard` → `app/static/console.html`

If you want your deployed site to show the **Next.js frontend** instead, set:

```bash
LEX_FRONTEND_BASE_URL=https://your-nextjs-domain.com
```

Then the backend will redirect:
- `GET /` → `https://your-nextjs-domain.com/`
- `GET /dashboard` → `https://your-nextjs-domain.com/app`

Use `GET /frontend/status` to verify which mode is active.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:
- Landing: `http://127.0.0.1:8000/`
- Dashboard: `http://127.0.0.1:8000/dashboard`

### Frontend routing mode (important)

If you deployed the new Next.js frontend separately (e.g., Vercel) but still hit the legacy static pages, set:

```bash
LEX_FRONTEND_BASE_URL=https://your-frontend-domain.com
```

When set, backend routes redirect as follows:
- `/` → `https://your-frontend-domain.com/`
- `/dashboard` → `https://your-frontend-domain.com/app`

Without this variable, the backend intentionally serves the legacy static HTML pages from `app/static/*`.

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

## Recommended Next Path (0 → 3 customers)

- **Week 1:** Create a vertical demo pack (legal ops, procurement, customer support escalations) using saved prompts and traces.
- **Week 2:** Add “trust receipts” export (input hash, output hash, intervention reason, M(t) timeline) for buyer audits.
- **Week 3:** Ship a lightweight hosted trial with 20 governed runs and in-app upgrade CTA.

---

## Frontend SaaS (Next.js)

A sell-ready frontend lives in `frontend/` using Next.js App Router + Tailwind + Stripe Checkout.

Key routes:
- `/` Marketing landing page
- `/demo` Conversion demo funnel
- `/app` Dashboard for users
- `/pricing` Subscription plans

Start frontend:
```bash
cd frontend
npm install
npm run dev
```
