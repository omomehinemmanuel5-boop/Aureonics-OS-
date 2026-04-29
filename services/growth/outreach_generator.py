from services.growth.models import MessageBundle, ScoredLead


class OutreachGenerator:
    def generate(self, scored: ScoredLead, channel: str) -> MessageBundle:
        ctx = scored.lead.context.get("recent_post", "your recent AI product momentum")
        company = scored.lead.company
        opener = f"Hi {scored.lead.full_name.split()[0]} — saw {ctx}."
        problem = f"Teams like {company} often ship AI fast, then scramble on governance, auditability, and customer trust at enterprise review time."
        value = "Lex Aureon adds policy-aware guardrails, traceable interventions, and risk telemetry without slowing your release cycle."
        cta = "Want me to show you a 2-minute live demo?" if scored.intent == "HIGH INTENT" else "Open to a short note on how peers reduce AI compliance friction?"
        return MessageBundle(opener=opener, problem=problem, value=value, cta=cta)
