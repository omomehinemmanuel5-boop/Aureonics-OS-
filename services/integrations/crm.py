from __future__ import annotations


class IntegrationStub:
    def send(self, payload: dict) -> dict:
        return {"status": "ok", "payload": payload}


client = IntegrationStub()
