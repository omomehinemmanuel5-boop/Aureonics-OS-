# Aureonics One-Go Sales Operating System

## Objective
Close first paid pilots fast by packaging Lex Aureon as a **manual-invoice trust governance pilot** with a concrete technical proof loop.

---

## 1) Product Packaging (what to sell)

### Offer name
**Trust Visibility Pilot (TVP)**

### Pilot definition
- Duration: 14–28 days
- Scope: one workflow, one team, one environment
- Commercial model: monthly pilot fee via manual invoice
- Success artifact: intervention trace report + executive trust summary

### Plan mechanics for immediate sales
- **Pro**: fixed monthly amount, seat-based multiplier
- **Enterprise**: custom scoping call, invoice generated after scope lock

---

## 2) Sales Narrative (what to say)

1. **Risk statement:** raw model behavior is opaque under stress.
2. **Proof step:** run the same prompt through governed pipeline.
3. **Evidence:** show intervention badge + stability margin + rationale.
4. **Commercial close:** start pilot via manual invoice today.

Use this sentence:
> “We don’t ask you to trust AI outputs blindly; we provide auditable correction evidence per run.”

---

## 3) Buyer Journey (one-call close structure)

### Discovery (10 min)
- Current AI workflow and failure cost.
- Policy/compliance constraints.
- Stakeholders required for pilot approval.

### Live demo (12 min)
- Show boundary prompt.
- Show intervention and corrected output.
- Show pricing and pilot scope.

### Commercial close (8 min)
- Capture buyer email/company/seats.
- Trigger `POST /billing/checkout`.
- Send invoice + kickoff date + success criteria.

---

## 4) Operational Architecture

### Core
- API endpoint: `/lex/run`
- Trust evidence: intervention flag + reason + semantic diff + M score
- Pricing metadata: `/pricing`
- Payment initiation: `/billing/checkout` (manual invoice mode)

### Sales ops handshake
- CRM record includes: use case, owner, pilot duration, seats, invoice id, due date.
- Delivery includes weekly trust review and remediation decisions.

---

## 5) “First Sales Today” checklist

1. Prepare 3 demo prompts mapped to one target vertical.
2. Run live demo and capture screenshots of intervention evidence.
3. Quote pilot package and send manual invoice payload in-call.
4. Confirm payment terms and kickoff date before call end.
5. Send same-day recap with goals, artifacts, and implementation timeline.

---

## 6) Hard gates before scaling after first pilot

- Replace mock auth with OIDC/JWKS.
- Move repository to persistent database + tenant controls.
- Add durable event streaming and signed audit bundle exports.
- Add security scanning gates for release path.

These are scale-stage gates; they should not block first pilot sales in manual mode.
