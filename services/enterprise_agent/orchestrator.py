from services.enterprise_agent.audit_logger import AuditEvent, AuditLogger
from services.enterprise_agent.compliance_guard import ComplianceGuard
from services.enterprise_agent.conversation_engine import ConversationEngine
from services.enterprise_agent.deal_tracker import DealTracker
from services.enterprise_agent.escalation_engine import EscalationEngine
from services.enterprise_agent.intent_classifier import IntentClassifier
from services.enterprise_agent.models import DealContext
from services.enterprise_agent.policy_enforcer import PolicyEnforcer


class EnterpriseOrchestrator:
    def __init__(self) -> None:
        self.audit = AuditLogger()
        self.guard = ComplianceGuard()
        self.policy = PolicyEnforcer()
        self.intent = IntentClassifier()
        self.conv = ConversationEngine()
        self.tracker = DealTracker()
        self.escalation = EscalationEngine()

    def process_inbound(self, deal: DealContext, role: str, inbound: str, actor: str = "system") -> dict:
        intent = self.intent.classify(inbound)
        message = self.conv.craft(deal, role, inbound)
        policy = self.policy.evaluate(message)
        compliance = self.guard.validate(message)
        escalate, reason = self.escalation.should_escalate(intent, deal.value_estimate)
        approved = policy.allowed and compliance.approved and not escalate
        status = "sent" if approved else "blocked"
        event = self.audit.log(
            AuditEvent(
                deal_id=deal.deal_id,
                actor=actor,
                action="outbound_message",
                reason=reason or "automated_followup",
                compliance_status=status,
                metadata={"intent": intent, "violations": policy.violations + compliance.reasons},
            )
        )
        if approved:
            self.tracker.advance(deal)
        return {"approved": approved, "message": compliance.sanitized_message, "audit": event, "escalation_reason": reason}
