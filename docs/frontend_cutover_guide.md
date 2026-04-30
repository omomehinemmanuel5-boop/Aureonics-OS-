# Frontend Cutover Guide — Show the New High-Quality Frontend on Your Website

This guide makes your website show the new Next.js frontend instead of legacy embedded static pages.

## What controls which frontend users see

Backend behavior is controlled by `LEX_FRONTEND_BASE_URL`:

- **Unset** → backend serves legacy static pages from FastAPI.
- **Set** (e.g. `https://your-frontend-domain.com`) → backend redirects:
  - `/` → `https://your-frontend-domain.com/`
  - `/dashboard` → `https://your-frontend-domain.com/app`

## Production cutover steps

1. Deploy your Next.js frontend and copy its public URL.
2. In your backend host (Render service for `lex-aureon`), set env var:
   - `LEX_FRONTEND_BASE_URL=https://your-frontend-domain.com`
3. Redeploy backend service.
4. Verify routing with the checker script:
   ```bash
   python scripts/check_frontend_connection.py https://your-backend-domain.com
   ```
5. Confirm browser behavior:
   - Open `https://your-backend-domain.com/` (should redirect to frontend root)
   - Open `https://your-backend-domain.com/dashboard` (should redirect to frontend `/app`)

## Common misconfigurations

- Setting `LEX_FRONTEND_BASE_URL` on the wrong service.
- Forgetting to redeploy after setting env vars.
- Using a frontend URL with the wrong protocol (must match deployed `https://...`).
- Pointing to a frontend URL that does not expose `/` and `/app` routes.

## Rollback

If needed, remove `LEX_FRONTEND_BASE_URL` and redeploy. Backend will resume serving embedded static pages.
