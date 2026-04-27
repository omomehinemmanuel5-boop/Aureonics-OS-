# Next Step Plan (Immediate)

## Recommended Next Step

**Implement Step 2 only:** introduce a clean package split (`landing`, `app`, `api`, `core`, `memory`) as a **non-breaking refactor**.

This is the highest-leverage move because it creates execution clarity without distracting into new features.

## Scope (1 sprint)

- Create target directories and module entrypoints.
- Move files incrementally with compatibility imports where needed.
- Keep endpoint behavior and schema unchanged.
- Keep current tests green after each move batch.

## Definition of Done

- `POST /lex/run` behavior unchanged.
- `POST /praxis/run` behavior unchanged.
- Existing UI still functions.
- Test suite for API contract/import safety passes.
- README and architecture docs reference new structure.

## Why this should be next

- De-risks future work by reducing structural ambiguity.
- Makes ownership obvious (growth, product, governance, memory).
- Supports faster onboarding and enterprise due diligence.
- Prevents overbuilding by forcing discipline around layer boundaries.
