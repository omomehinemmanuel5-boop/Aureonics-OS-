# Lex Aureon Autonomous Sales Agent

## Architecture
- `services/sales_agent/orchestrator.py`: core intelligence loop.
- `services/sales_agent/conversation_state.py`: state + intent models.
- `services/sales_agent/intent_classifier.py`: HOT/WARM/COLD/DEAD logic.
- `services/sales_agent/reasoning_engine.py`: transitions + next-best-action.
- `services/sales_agent/objection_handler.py`: objection playbook.
- `services/sales_agent/closing_engine.py`: conversion-first close motions.
- `services/sales_agent/recovery_engine.py`: self-healing failure recovery.
- `services/sales_agent/message_generator.py`: intent-aware templates.
- `services/integrations/*.py`: stubs for x/email/crm/calendar/billing.

## Core loop
Input: message + lead profile + history
1. classify intent
2. update state
3. select action
4. generate response
5. evaluate outcome

Output: response, state transition, confidence.

## Example conversation
Run:
```bash
python services/sales_agent/example_flow.py
```

## Docker
```bash
docker-compose up --build
```

## Safety
- no fake claims
- no spam loops
- human override path via `handoff`
- no impersonation
