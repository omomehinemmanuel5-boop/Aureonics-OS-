# Lex API SaaS Launch Notes

## Updated Repo Structure

- `app/main.py` — productized FastAPI API + quota + pricing + demo + billing stub
- `app/static/index.html` — marketing landing page
- `app/static/console.html` — minimal SaaS dashboard
- `app/static/firewall.css` — shared minimal visual system
- `app/static/firewall.js` — dashboard interactions and developer-mode trace toggle
- `README.md` — production deployment + monetization narrative

## API Endpoints

- `POST /lex/run` — governed inference contract
- `GET /health` — startup status and degraded signal
- `GET /pricing` — pricing and feature metadata
- `GET /demo` — deterministic intervention sample
- `POST /billing/checkout` — Stripe checkout placeholder

## Frontend UX Rules Applied

- Default UI shows only final output, intervention badge, and M score.
- Raw and governed outputs are hidden unless developer mode is enabled.
- Share card is concise and horizontal-friendly (not stacked research traces).

## Deployment Contract

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Startup is resilient through safe kernel boot.
- If kernel init fails, app still boots and `/health` reports degraded.
