from __future__ import annotations
from dataclasses import dataclass, field

from services.growth.analytics_engine import AnalyticsEngine
from services.growth.booking_engine import BookingEngine
from services.growth.dm_orchestrator import DMOrchestrator
from services.growth.funnel_optimizer import FunnelOptimizer
from services.growth.lead_discovery import LeadDiscovery
from services.growth.lead_scoring import LeadScorer
from services.growth.outreach_generator import OutreachGenerator
from services.growth.persona_classifier import PersonaClassifier
from services.growth.reply_classifier import ReplyClassifier
from services.integrations.calendar_scheduler import CalendarScheduler
from services.integrations.crm_sync import CRMSync


@dataclass
class GrowthEngine:
    discovery: LeadDiscovery = field(default_factory=LeadDiscovery)
    persona: PersonaClassifier = field(default_factory=PersonaClassifier)
    scorer: LeadScorer = field(default_factory=LeadScorer)
    outreach: OutreachGenerator = field(default_factory=OutreachGenerator)
    replies: ReplyClassifier = field(default_factory=ReplyClassifier)
    dm: DMOrchestrator = field(default_factory=DMOrchestrator)
    booking: BookingEngine = field(default_factory=lambda: BookingEngine(CalendarScheduler()))
    analytics: AnalyticsEngine = field(default_factory=AnalyticsEngine)
    optimizer: FunnelOptimizer = field(default_factory=FunnelOptimizer)
    crm: CRMSync = field(default_factory=CRMSync)

    def run_daily_cycle(self) -> dict:
        leads = self.discovery.discover()
        hook = "Govern AI before enterprise audits block deals"
        for lead in leads:
            persona = self.persona.classify(lead)
            scored = self.scorer.score(lead, persona)
            if scored.intent == "LOW INTENT":
                continue
            msg = self.outreach.generate(scored, channel=lead.channel)
            full = " ".join([msg.opener, msg.problem, msg.value, msg.cta])
            self.analytics.track("messages_sent")
            self.crm.upsert_lead(lead.lead_id, {"persona": persona, "intent": scored.intent, "message": full})
            # Simulated reply signal
            simulated_reply = "yes show demo" if scored.intent == "HIGH INTENT" else "send details"
            klass = self.replies.classify(simulated_reply)
            self.analytics.track("replies")
            if klass == "positive_interest":
                self.analytics.track("positive_replies")
                booking_msg = self.booking.booking_message(lead.lead_id)
                self.crm.upsert_lead(lead.lead_id, {"booking_message": booking_msg})
                self.analytics.track("demos_booked")
        snap = self.analytics.snapshot()
        snap["new_hook"] = self.optimizer.optimize(snap, hook)
        return snap


if __name__ == "__main__":
    engine = GrowthEngine()
    print(engine.run_daily_cycle())
