from services.sales_agent import LeadProfile, SalesAgentOrchestrator


if __name__ == "__main__":
    orch = SalesAgentOrchestrator()
    lead = LeadProfile(lead_id="acme-1", name="Dana", company="Acme", urgency_score=0.8, budget_hint=0.7, technical_depth=0.8, compliance_interest=0.6, response_speed=0.9)
    history = []
    for msg in [
        "We already use another tool",
        "Okay, maybe show ROI",
        "Can we start today with trial?",
    ]:
        out = orch.process(msg, lead, history)
        history.append({"role": "lead", "content": msg})
        history.append({"role": "agent", "content": out["response_message"]})
        print(out)
