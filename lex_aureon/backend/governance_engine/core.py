from __future__ import annotations

from difflib import SequenceMatcher

RISKY_TERMS = ("bypass", "exploit", "malware", "credential", "jailbreak", "disable")


def risk_score(text: str) -> float:
    lowered = (text or "").lower()
    matches = sum(1 for term in RISKY_TERMS if term in lowered)
    length_bonus = 0.1 if len(text) > 600 else 0.0
    return min(1.0, round(matches * 0.18 + length_bonus, 4))


def governance_transform(text: str, policy: dict[str, str] | None = None) -> str:
    policy = policy or {}
    lowered = (text or "").lower()
    blocked = policy.get("action", "redact")
    if any(term in lowered for term in RISKY_TERMS):
        if blocked == "block":
            return "[BLOCKED BY LEX AUREON POLICY]"
        return "[REDACTED BY LEX AUREON] The output was transformed to satisfy enterprise safety policy."
    return text


def meaning_preserved(raw: str, governed: str) -> float:
    return round(SequenceMatcher(None, raw or "", governed or "").ratio(), 4)
