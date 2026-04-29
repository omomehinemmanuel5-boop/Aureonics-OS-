class ReplyClassifier:
    def classify(self, reply: str) -> str:
        text = reply.lower()
        if any(x in text for x in ["yes", "book", "demo", "interested"]):
            return "positive_interest"
        if any(x in text for x in ["how", "what", "details", "question"]):
            return "technical_question"
        if any(x in text for x in ["not now", "budget", "already have"]):
            return "objection"
        if any(x in text for x in ["no", "stop", "unsubscribe"]):
            return "rejection"
        return "neutral_curiosity"
