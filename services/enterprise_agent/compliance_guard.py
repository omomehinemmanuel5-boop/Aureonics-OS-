from dataclasses import dataclass

from services.compliance.pii_redaction import redact_pii


@dataclass
class ComplianceResult:
    approved: bool
    reasons: list[str]
    sanitized_message: str


class ComplianceGuard:
    forbidden_patterns = {
        "false_claim": "industry-leading guarantee",
        "pricing_hallucination": "$0 for enterprise forever",
        "contract_commitment": "we are legally bound",
        "unsupported_guarantee": "100% breach proof",
    }

    def validate(self, message: str) -> ComplianceResult:
        reasons = []
        for code, pattern in self.forbidden_patterns.items():
            if pattern in message.lower():
                reasons.append(code)
        sanitized = redact_pii(message)
        if sanitized != message:
            reasons.append("pii_redacted")
        return ComplianceResult(approved=not any(r for r in reasons if r != "pii_redacted"), reasons=reasons, sanitized_message=sanitized)
