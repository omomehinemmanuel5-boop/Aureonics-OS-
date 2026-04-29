def generate_proposal(deal_id: str, account_name: str, objectives: list[str]) -> dict:
    return {
        "deal_id": deal_id,
        "account": account_name,
        "sections": [
            "Executive Summary",
            "Technical Architecture",
            "Security & Compliance",
            "Commercial Outline",
            "Implementation Plan",
        ],
        "objectives": objectives,
    }
