# Lex Aureon Frontend (Sell-Ready SaaS)

## Stack
- Next.js App Router
- Tailwind CSS
- Stripe Checkout
- Existing backend API: `POST /lex/run`

## Routes
- `/` Landing page (conversion-focused)
- `/demo` Demo funnel with share-card loop
- `/app` Product dashboard with no login/trial gate
- `/pricing` Pricing + checkout
- `/api/checkout` Stripe subscription checkout session creator

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
- `NEXT_PUBLIC_LEX_API_BASE_URL`: Backend origin for `/lex/run`
- `STRIPE_SECRET_KEY`
- `STRIPE_PRICE_ID_PRO`
- `STRIPE_PRICE_ID_ENTERPRISE`

## Troubleshooting
- If the **FINAL SOVEREIGN OUTPUT** panel appears blank, the UI now auto-falls back to `governed_output` and then `raw_output`.
- If runs are not executing, verify backend is reachable at `NEXT_PUBLIC_LEX_API_BASE_URL` and that `POST /lex/run` returns JSON.
