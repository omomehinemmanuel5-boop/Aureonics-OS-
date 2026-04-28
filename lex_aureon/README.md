# Lex Aureon (Enterprise SaaS Scaffold)

## Updated monorepo structure

- `packages/contracts/`
  - `schemas.py` (shared Pydantic contract layer)
  - `openapi.yaml` (cross-service API contract)
- `lex_aureon/backend/common/`
  - `config.py` (env validation)
  - `observability.py` (JSON logs + request_id/trace_id propagation)
  - `tenant.py` (org isolation enforcement)
  - `event_bus.py` (event-driven abstraction)
  - `circuit_breaker.py` (degradation/fallback guard)
  - `repository.py` (append-only hash-chained audit persistence)
- `lex_aureon/backend/*_service/`
  - FastAPI microservices with org middleware and structured telemetry
- `lex_aureon/backend/governance_engine/core.py`
  - deterministic pure functions: `risk_score`, `governance_transform`
- `lex_aureon/deploy/docker-compose.yml`
  - full local stack deployment
- `lex_aureon/deploy/render/render.yaml`
  - production Render blueprint

## Guarantees implemented

- Multi-tenant isolation via service-level org checks + Supabase RLS.
- Event emission: `AI_INGESTED`, `AI_GOVERNED`, `POLICY_TRIGGERED`, `AUDIT_LOGGED`, degradation event.
- Audit immutability through append-only records with hash chaining (`prev_hash -> immutable_hash`).
- Circuit breaker fallback mode: `PASS_THROUGH_SAFE`.
- Enterprise API gateway with auth validation, policy hook, org rate limiting, request logging.
- CI/CD upgraded with schema checks, contract validation, security linting, deploy rollback workflow.
