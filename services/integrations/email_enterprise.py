class EmailEnterprise:
    def send(self, to: str, subject: str, body: str) -> dict:
        return {"to": to, "subject": subject, "status": "queued", "body": body}
