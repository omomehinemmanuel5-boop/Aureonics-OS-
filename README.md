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
- **Operational endpoints**: `GET /health`, `GET /pricing`, `GET /demo`
- **Stripe-ready stub**: `POST /billing/checkout`

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

Frontend displays only:
- `final_output` (primary)
- `intervention` badge
- `M` score

`raw_output` and `governed_output` are available in **Developer mode** only.

## Pricing Model

- **Free**: 10 runs/day, watermark `Lex Demo`
- **Pro ($19/mo)**: 2,000 runs/month, no watermark, priority inference
- **Enterprise ($99+/mo)**: API access, bulk inference, governance tuning controls

Use `GET /pricing` for machine-readable plan metadata.

## Stripe Placeholder Layer

`POST /billing/checkout`

```json
{ "plan": "pro" }
```

Returns a stub checkout URL/session id to replace with real Stripe Checkout Session creation.

## Deployment (Render-safe)

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The app uses safe boot behavior:
- Import-time kernel failure does **not** block startup.
- `/health` returns `degraded: true` when bootstrap errors exist.

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
