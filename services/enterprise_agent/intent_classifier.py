class IntentClassifier:
    mapping = {
        "demo": "book_demo",
        "security": "security_review",
        "price": "pricing",
        "contract": "legal",
        "roi": "business_case",
    }

    def classify(self, text: str) -> str:
        lowered = text.lower()
        for k, v in self.mapping.items():
            if k in lowered:
                return v
        return "general_question"
