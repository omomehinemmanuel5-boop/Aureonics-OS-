from packages.contracts.schemas import GovernanceRequestContract, GovernanceResponseContract, IngestRequestContract


if __name__ == "__main__":
    assert IngestRequestContract.schema()["title"]
    assert GovernanceRequestContract.schema()["title"]
    assert GovernanceResponseContract.schema()["title"]
    print("contract schemas validated")
