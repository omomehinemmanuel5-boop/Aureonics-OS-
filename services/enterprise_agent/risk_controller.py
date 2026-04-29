class RiskController:
    def score(self, objections: list[str], days_idle: int, deal_value: float) -> float:
        score = min(1.0, len(objections) * 0.15 + min(days_idle / 30.0, 0.4) + (0.2 if deal_value > 100000 else 0.0))
        return round(score, 2)
