from lex_aureon.backend.common.models import GovernanceRequest, IngestRequest
from packages.contracts.schemas import GovernanceRequestContract, IngestRequestContract


def test_ingest_contract_compatibility():
    payload = {"organization_id": "org-1", "user_id": "user-1", "model_name": "gpt", "raw_output": "x"}
    assert IngestRequest(**payload).dict().keys() == IngestRequestContract(**payload).dict().keys()


def test_govern_contract_compatibility():
    payload = {"log_id": "abc", "organization_id": "org-1"}
    assert GovernanceRequest(**payload).dict().keys() == GovernanceRequestContract(**payload).dict().keys()
