# Frontend Go-Live Playbook (Render backend + Next.js frontend)

Last updated: April 30, 2026.

This guide ensures your **high-quality Next.js frontend** is what users see when they visit your website.

## What must be true

Your backend (`app/main.py`) only redirects to the external frontend when `LEX_FRONTEND_BASE_URL` is set.
Without that env var, it serves legacy static pages.

- `/` redirects to `<LEX_FRONTEND_BASE_URL>/`
- `/dashboard` redirects to `<LEX_FRONTEND_BASE_URL>/app`
- `/frontend/status` reports mode `external_nextjs` when connected

## Step 1 — Deploy the Next.js frontend

Deploy `frontend/` to Vercel (or equivalent), then capture the production URL.
Example:
- `https://ui.yourdomain.com`

If you have a custom root domain, point it to the frontend deployment.

## Step 2 — Wire backend to frontend

In your backend host (Render service that runs `uvicorn app.main:app`):

Set environment variable:

```bash
LEX_FRONTEND_BASE_URL=https://ui.yourdomain.com
```

Then redeploy backend.

## Step 3 — Verify redirect behavior

### Option A: API status check

```bash
curl -s https://api.yourdomain.com/frontend/status | jq
```

Expected:
- `mode: "external_nextjs"`
- `frontend_base_url: "https://ui.yourdomain.com"`

### Option B: Built-in checker script

```bash
python scripts/check_frontend_connection.py https://api.yourdomain.com
```

Expected terminal output includes:
- `CONNECTED: external Next.js frontend is active.`

### Option C: Header checks

```bash
curl -I https://api.yourdomain.com/
curl -I https://api.yourdomain.com/dashboard
```

Expected:
- `307` from `/` with `Location: https://ui.yourdomain.com/`
- `307` from `/dashboard` with `Location: https://ui.yourdomain.com/app`

## Step 4 — Domain strategy (recommended)

Use split subdomains:
- Frontend: `https://www.yourdomain.com` or `https://ui.yourdomain.com`
- API: `https://api.yourdomain.com`

Then set:
- `LEX_FRONTEND_BASE_URL` on API service to frontend URL.

## Step 5 — CORS and cookies sanity check

Current code allows all origins (`allow_origins=["*"]`) which is acceptable for token-header auth but not ideal for stricter production posture.
If moving to cookie auth later, lock CORS to your frontend origin.

## Step 6 — Production acceptance checklist

Mark go-live complete only when all pass:
- [ ] `/frontend/status` returns `external_nextjs`.
- [ ] `/` and `/dashboard` redirect to frontend URL.
- [ ] Frontend pages load over HTTPS with valid cert.
- [ ] Login + `/lex/run` flow works from browser.
- [ ] No mixed-content or CORS errors in browser console.
- [ ] Synthetic uptime checks validate both frontend and API endpoints.

## Troubleshooting

### Symptom: Still seeing old static page
- Cause: `LEX_FRONTEND_BASE_URL` missing or typo.
- Fix: Set exact `https://...` URL and redeploy backend.

### Symptom: Redirect loop
- Cause: `LEX_FRONTEND_BASE_URL` points back to backend domain.
- Fix: Ensure it points to Next.js site domain, not API domain.

### Symptom: `/frontend/status` says `embedded_fastapi_static`
- Cause: Env var not present in runtime.
- Fix: Check service environment settings and restart deployment.
