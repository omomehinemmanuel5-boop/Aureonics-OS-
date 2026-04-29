from dataclasses import dataclass


@dataclass
class PolicyResult:
    allowed: bool
    violations: list[str]


class PolicyEnforcer:
    blocked_terms = (
        "guaranteed roi",
        "sign on your behalf",
        "unlimited indemnity",
    )

    def evaluate(self, message: str) -> PolicyResult:
        violations = [f"blocked_term:{term}" for term in self.blocked_terms if term in message.lower()]
        return PolicyResult(allowed=not violations, violations=violations)
