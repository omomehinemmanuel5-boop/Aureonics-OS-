from services.growth.models import Lead, ScoredLead


class LeadScorer:
    WEIGHTS = {
        "ai_usage": 0.25,
        "production_readiness": 0.2,
        "company_size_match": 0.15,
        "urgency": 0.2,
        "buying_probability": 0.2,
    }

    def score(self, lead: Lead, persona: str) -> ScoredLead:
        size_match = 1.0 if 10 <= lead.company_size <= 500 else 0.35
        readiness = min(1.0, (lead.signals.get("ai_usage", 0.0) * 0.6) + (lead.signals.get("urgency", 0.0) * 0.4))
        buying = 0.85 if persona in {"ai_saas_founder", "mid_market_cto", "regulated_ai_startup"} else 0.62
        components = {
            "ai_usage": lead.signals.get("ai_usage", 0.0),
            "production_readiness": readiness,
            "company_size_match": size_match,
            "urgency": lead.signals.get("urgency", 0.0),
            "buying_probability": buying,
        }
        total = sum(components[k] * self.WEIGHTS[k] for k in components)
        intent = "HIGH INTENT" if total >= 0.75 else "MEDIUM INTENT" if total >= 0.5 else "LOW INTENT"
        return ScoredLead(lead=lead, component_scores=components, total_score=round(total, 4), intent=intent, persona=persona)
