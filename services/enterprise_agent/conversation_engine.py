from services.enterprise_agent.models import DealContext


class ConversationEngine:
    role_templates = {
        "technical_buyer": "Sharing architecture and integration details tailored to your stack.",
        "economic_buyer": "Focusing on ROI, deployment timeline, and risk-adjusted value.",
        "security_reviewer": "Providing SOC2 controls, data flow, and security posture evidence.",
        "end_user_champion": "Emphasizing usability, rollout support, and team outcomes.",
        "unknown": "Providing a concise enterprise overview and next recommended action.",
    }

    def craft(self, deal: DealContext, stakeholder_role: str, user_question: str) -> str:
        framing = self.role_templates.get(stakeholder_role, self.role_templates["unknown"])
        return (
            f"For {deal.account_name} at stage {deal.stage.value}: {framing} "
            f"Answer: {user_question}. Next step: schedule aligned follow-up."
        )
