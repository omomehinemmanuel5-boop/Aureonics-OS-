from services.enterprise_agent.models import Stakeholder


ROLE_MAP = {
    "cto": "technical_buyer",
    "engineering manager": "technical_buyer",
    "cfo": "economic_buyer",
    "vp finance": "economic_buyer",
    "security": "security_reviewer",
    "compliance": "security_reviewer",
    "champion": "end_user_champion",
}


class StakeholderMapper:
    def classify(self, title: str) -> str:
        lowered = title.lower()
        for key, role in ROLE_MAP.items():
            if key in lowered:
                return role
        return "unknown"

    def create(self, name: str, title: str, email: str) -> Stakeholder:
        return Stakeholder(name=name, role=self.classify(title), email=email)
