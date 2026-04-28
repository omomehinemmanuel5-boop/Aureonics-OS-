from packages.contracts.schemas import GovernanceRequest, IngestRequest


def test_ingest_contract_fields():
    payload = IngestRequest(organization_id="org", user_id="user", model_name="gpt", raw_output="hello")
    assert payload.organization_id == "org"


def test_govern_contract_fields():
    payload = GovernanceRequest(log_id="log", organization_id="org")
    assert payload.log_id == "log"
