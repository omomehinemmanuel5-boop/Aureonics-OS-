# Frontend Cutover Guide — `lexaureon.com` Live Now (Backend + Frontend)

This is the exact production setup so users see the high-quality Next.js frontend at `https://lexaureon.com` while backend APIs stay online.

## Target architecture (recommended)

- **Frontend (Next.js Render service):** `https://lexaureon.com`
- **Backend (FastAPI Render service):** `https://api.lexaureon.com`

Why this is correct:
- You cannot attach the same exact host (`lexaureon.com`) to two different Render services.
- Frontend should own the apex domain for UX and SEO.
- Backend should run on an API subdomain and be called by frontend server/API routes.

## Prerequisites

- Root `render.yaml` from this repo deployed as a Render Blueprint (contains both services).
- DNS access at your registrar / DNS provider for `lexaureon.com`.

## 1) Render service ownership and env vars

### Frontend service: `lex-aureon-frontend`
Set in Render **Environment**:
- `LEX_API_BASE_URL=https://api.lexaureon.com`
- `NEXT_PUBLIC_LEX_API_BASE_URL=https://api.lexaureon.com`
- (optional) `SALES_CONTACT_EMAIL`, `SALES_PHONE_E164`

### Backend service: `lex-aureon`
Set in Render **Environment**:
- `LEX_FRONTEND_BASE_URL=https://lexaureon.com`

Redeploy both services after env updates.

## 2) Custom domains in Render

### Attach domain to frontend service
On `lex-aureon-frontend`:
- Add custom domains:
  - `lexaureon.com`
  - `www.lexaureon.com` (optional but recommended)

### Attach domain to backend service
On `lex-aureon`:
- Add custom domain:
  - `api.lexaureon.com`

## 3) DNS records you need to create

In your DNS provider, create exactly the records Render asks for in each service dashboard.
Typical shape (final values must match Render’s generated targets):

- `A` or `ALIAS` for apex `@` → Render frontend target
- `CNAME` for `www` → frontend Render hostname
- `CNAME` for `api` → backend Render hostname

Do **not** point `@` and `api` to the same service target.

## 4) Cutover verification (copy/paste)

After DNS propagates and SSL is issued:

```bash
python scripts/check_frontend_connection.py https://api.lexaureon.com
```

Expected result:
- JSON includes `"mode": "external_nextjs"`
- route probes show backend redirects are configured

Then verify endpoints in browser:
- `https://lexaureon.com` loads new Next.js frontend.
- `https://lexaureon.com/app` loads product app page.
- `https://api.lexaureon.com/health` returns healthy backend response.

## 5) Zero-downtime switchover order

1. Deploy backend + frontend services in Render.
2. Set all env vars.
3. Configure custom domains in Render (frontend + backend).
4. Create DNS records.
5. Wait for SSL issuance and DNS propagation.
6. Verify with checker script + browser tests.
7. Announce launch.

## 6) Common failure cases and exact fixes

- **Site still shows legacy static pages**
  - Fix: set `LEX_FRONTEND_BASE_URL=https://lexaureon.com` on backend and redeploy.
- **Frontend calls fail / timeout**
  - Fix: set `LEX_API_BASE_URL=https://api.lexaureon.com` on frontend and redeploy.
- **Mixed content / HTTPS issues**
  - Fix: ensure both domains are HTTPS and env vars use `https://`.
- **Wrong service owns apex**
  - Fix: `lexaureon.com` must be attached to frontend service, not backend.

## 7) Rollback

If immediate rollback is needed:
- Remove backend `LEX_FRONTEND_BASE_URL` and redeploy backend.
- Backend will serve embedded static pages again until frontend cutover is retried.
