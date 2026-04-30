# Lex Aureon Frontend (Sell-Ready SaaS)

## Stack
- Next.js App Router
- Tailwind CSS
- Invoice-first checkout (Stripe not required)
- Existing backend API: `POST /lex/run`

## Routes
- `/` Landing page (conversion-focused)
- `/demo` Demo funnel with share-card loop
- `/app` Product dashboard with no login/trial gate
- `/pricing` Pricing + invoice request flow
- `/api/checkout` Manual invoice request creator

## Setup
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Deployment
- **Vercel**: deploy `frontend` directory.
- **Render**: deploy backend API from repository root (`app.main:app`).

## Environment Variables
- `NEXT_PUBLIC_LEX_API_BASE_URL`: Optional direct backend origin for `/lex/run` (when omitted, frontend calls Next API proxy at `/api/lex/run`).
- `LEX_API_BASE_URL`: Server-only backend origin used by `/api/lex/run` route (recommended in production).
- `SALES_CONTACT_EMAIL`: fallback contact for invoice fulfilment (optional)
- `SALES_PHONE_E164`: WhatsApp-enabled sales phone in E.164 format (optional)
- `MANUAL_INVOICE_TERMS_DAYS`: invoice terms in days (optional, default 7)

## Troubleshooting
- If the **FINAL SOVEREIGN OUTPUT** panel appears blank, the UI now auto-falls back to `governed_output` and then `raw_output`.
- If runs are not executing, verify backend is reachable from the Next server via `LEX_API_BASE_URL` (or `NEXT_PUBLIC_LEX_API_BASE_URL`) and that `POST /lex/run` returns JSON.

## Website optimization defaults (enabled)

- SEO metadata wired in `app/layout.tsx` (Open Graph + Twitter cards + canonical metadata base).
- Search crawler helpers:
  - `app/robots.ts`
  - `app/sitemap.ts`
- API resilience in `lib/api.ts`:
  - 15s request timeout via `AbortController`
  - `cache: 'no-store'` for governed run requests to avoid stale inference responses

## Website optimization defaults (enabled)

- SEO metadata wired in `app/layout.tsx` (Open Graph + Twitter cards + canonical metadata base).
- Search crawler helpers:
  - `app/robots.ts`
  - `app/sitemap.ts`
- API resilience in `lib/api.ts`:
  - 15s request timeout via `AbortController`
  - `cache: 'no-store'` for governed run requests to avoid stale inference responses

## Landing page conversion architecture (2026-04-29)

The `/` page now serves as a governance-first SaaS funnel:
- **Hero:** value proposition + live simplex/governor simulation.
- **How it Works:** 3-step narrative for buyers (measure, intervene, prove).
- **Proof section:** governance and enterprise-readiness evidence points.
- **Pricing:** direct transition to `/app`, `/pricing`, and `/enterprise` for early sales conversion.

All runtime simplex math for the animated widget is centralized in `lib/simplex.ts` and covered by `tests/simplex.test.ts`.
