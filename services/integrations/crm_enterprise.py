class CRMEnterprise:
    def upsert_deal(self, payload: dict) -> dict:
        return {"provider": "abstraction", "status": "ok", "payload": payload}
