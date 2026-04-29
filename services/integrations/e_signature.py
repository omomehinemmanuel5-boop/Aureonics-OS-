class ESignature:
    def create_envelope(self, deal_id: str, documents: list[str]) -> dict:
        return {"deal_id": deal_id, "documents": documents, "status": "draft"}
