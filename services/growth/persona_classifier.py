from services.growth.models import Lead


class PersonaClassifier:
    def classify(self, lead: Lead) -> str:
        title = lead.title.lower()
        company = lead.company.lower()
        if "founder" in title:
            return "ai_saas_founder"
        if "cto" in title and 10 <= lead.company_size <= 500:
            return "mid_market_cto"
        if "agency" in company:
            return "ai_automation_agency"
        if "fin" in company or "legal" in company:
            return "regulated_ai_startup"
        return "llm_wrapper_startup"
