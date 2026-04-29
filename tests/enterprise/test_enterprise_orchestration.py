from services.enterprise_agent.models import DealContext, DealStage
from services.enterprise_agent.orchestrator import EnterpriseOrchestrator
from services.integrations.document_generator import generate_documents


def test_escalation_on_security_or_pricing():
    deal = DealContext(deal_id="D1", account_name="Acme", value_estimate=50000)
    orch = EnterpriseOrchestrator()
    result = orch.process_inbound(deal, "technical_buyer", "Need security details and pricing")
    assert result["approved"] is False
    assert result["escalation_reason"] is not None


def test_deal_progression_when_compliant():
    deal = DealContext(deal_id="D2", account_name="Acme", value_estimate=50000)
    orch = EnterpriseOrchestrator()
    result = orch.process_inbound(deal, "technical_buyer", "Can you share architecture guidance?")
    assert result["approved"] is True
    assert deal.stage == DealStage.STAKEHOLDER_MAPPING


def test_document_generation(tmp_path):
    files = generate_documents(str(tmp_path), "Acme")
    assert len(files) == 6
