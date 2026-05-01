# Deployment Readiness — Next Steps (April 30, 2026)

This checklist answers: **what still needs to be done before production deployment**.

## Current state snapshot

The repository already includes:
- CI workflows for backend tests, contract validation, frontend typecheck, and a Semgrep pass.
- Render deployment workflow and rollback workflow.
- Dockerfiles for multiple backend services and compose files for local environments.
- Existing tests for API routes, contracts, deployment smoke checks, governance logic, and auth/customer readiness.

## Critical path to production (must-complete)

### 1) Identity and auth hardening
- Replace mock/placeholder JWT parsing with full OIDC/JWKS verification.
- Enforce strict token audience (`aud`) and issuer (`iss`) checks.
- Add key-rotation-safe JWKS cache with expiry and fallback behavior.
- Add integration tests for invalid signatures, expired tokens, wrong audiences, and revoked users.

**Exit criteria:** no mock auth code paths remain in production runtime.

### 2) Persistence durability
- Replace in-memory repositories with PostgreSQL/Supabase adapters across gateway and services.
- Add migration verification in CI (apply + rollback checks in ephemeral DB).
- Verify multi-tenant isolation with row-level security test coverage.

**Exit criteria:** process restart does not lose customer, run, receipt, or audit state.

### 3) Eventing durability
- Replace in-process event bus with Redis/NATS-backed durable messaging.
- Add dead-letter and replay strategy for failed consumers.
- Add idempotency keys to all event consumers.

**Exit criteria:** no event loss on service crash/restart.

### 4) Secret and config management
- Move all secrets to Render/hosted secret manager (no defaults, no plaintext).
- Enforce startup-time validation for required env vars in all services.
- Add secret-scanning check (e.g., gitleaks/trufflehog) to CI.

**Exit criteria:** deployment fails fast if any required secret/config is missing.

### 5) Security gates in CI/CD
- Add dependency vulnerability scanning (Python + Node).
- Add container image scanning for all Dockerfiles.
- Add DAST smoke against staged deployment.

**Exit criteria:** release branch cannot deploy when security thresholds fail.

### 6) Observability and incident readiness
- Add centralized logs with trace IDs across gateway and services.
- Add metrics/alerts for error rate, p95 latency, queue lag, auth failures, and governance fallback rates.
- Publish runbooks for: auth outage, DB outage, event backlog, and degraded governance mode.

**Exit criteria:** on-call can detect and resolve top failure modes with documented playbooks.

## Launch-blocking operational checks

Before the first real customer rollout, run a controlled **staging gate**:
- Load test with representative payloads and target concurrency.
- Chaos checks: restart services while traffic is live.
- Backup/restore drill with real schema.
- Verify trust receipt generation/verification end-to-end with tamper tests.
- Verify billing/auth flow with production-like identities.

## Recommended sequence (fastest safe path)

1. Auth hardening (OIDC/JWKS)  
2. Durable PostgreSQL adapters + migration gate  
3. Durable event bus + idempotency  
4. Security scanning gates  
5. Observability + alerting + runbooks  
6. Staging gate + rollout plan

## Deployment decision rubric

Move to production only when all are true:
- ✅ No mock auth/runtime components in production code path.
- ✅ All critical state persisted durably in managed DB.
- ✅ Durable event transport with replay and idempotency.
- ✅ CI includes security + container scans and blocks on failures.
- ✅ Alerting + runbooks tested in staging.
- ✅ Staging gate passed (load, chaos, backup/restore, trust-receipt integrity).
