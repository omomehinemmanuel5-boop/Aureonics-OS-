from services.sales_agent import LeadProfile, SalesAgentOrchestrator


def test_hot_lead_closing_attempt() -> None:
    orch = SalesAgentOrchestrator()
    lead = LeadProfile(lead_id="1", urgency_score=0.9, budget_hint=0.9, technical_depth=0.7, compliance_interest=0.7, response_speed=0.8)
    out = orch.process("We want to start today and sign contract", lead, [])
    assert out["intent"] == "hot"
    assert out["state_transition"] == "closing_attempt"


def test_objection_route() -> None:
    orch = SalesAgentOrchestrator()
    lead = LeadProfile(lead_id="2")
    out = orch.process("too expensive", lead, [])
    assert out["state_transition"] == "objection_handling"


def test_self_heal_updates_memory() -> None:
    orch = SalesAgentOrchestrator()
    result = orch.self_heal("x", "no_reply")
    assert result["strategy_shift"] == "shorten_and_personalize"
