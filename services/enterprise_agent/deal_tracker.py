from services.enterprise_agent.models import DealContext, DealStage


STAGE_ORDER = [
    DealStage.LEAD_IDENTIFICATION,
    DealStage.STAKEHOLDER_MAPPING,
    DealStage.TECHNICAL_QUALIFICATION,
    DealStage.BUSINESS_CASE_ALIGNMENT,
    DealStage.SECURITY_COMPLIANCE_REVIEW,
    DealStage.PROCUREMENT_PREPARATION,
    DealStage.NEGOTIATION_SUPPORT,
    DealStage.CLOSE,
    DealStage.POST_CLOSE_HANDOFF,
]


class DealTracker:
    def advance(self, deal: DealContext) -> DealStage:
        idx = STAGE_ORDER.index(deal.stage)
        if idx < len(STAGE_ORDER) - 1:
            deal.stage = STAGE_ORDER[idx + 1]
        deal.add_history("stage_advanced", {"stage": deal.stage.value})
        return deal.stage
