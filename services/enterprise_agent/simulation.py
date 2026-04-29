from services.enterprise_agent.models import DealContext
from services.enterprise_agent.orchestrator import EnterpriseOrchestrator
from services.enterprise_agent.stakeholder_mapper import StakeholderMapper
from services.integrations.document_generator import generate_documents


def run_simulation() -> dict:
    deal = DealContext(deal_id="D-100", account_name="FortuneCo", value_estimate=300000)
    mapper = StakeholderMapper()
    st = mapper.create("Casey", "CTO", "casey@fortuneco.com")
    deal.stakeholders[st.email] = st
    orch = EnterpriseOrchestrator()
    result1 = orch.process_inbound(deal, st.role, "Can we review security and pricing?")
    result2 = orch.process_inbound(deal, st.role, "Please share architecture details")
    docs = generate_documents("/tmp/lex_aureon_docs", deal.account_name)
    return {"deal_stage": deal.stage.value, "results": [result1, result2], "docs": docs, "audit_events": orch.audit.events()}


if __name__ == "__main__":
    import json

    print(json.dumps(run_simulation(), indent=2))
