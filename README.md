# Lex API — Governed AI Responses

Lex API is a sellable SaaS surface for governed inference: paste a prompt, receive a stabilized final output, and scale usage by plan.

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
- API docs: `http://127.0.0.1:8000/docs`
