from __future__ import annotations

from typing import Iterable

RISKY_TERMS = ("bypass", "exploit", "malware", "credential", "jailbreak", "disable")


def risk_score(text: str) -> float:
    lowered = text.lower()
    hits = sum(1 for term in RISKY_TERMS if term in lowered)
    size_penalty = 0.1 if len(text) > 600 else 0.0
    return min(1.0, round(hits * 0.18 + size_penalty, 4))


def governance_transform(text: str, policy_terms: Iterable[str] | None = None) -> tuple[str, list[str]]:
    terms = tuple(policy_terms) if policy_terms is not None else RISKY_TERMS
    matched = [term for term in terms if term in text.lower()]
    if not matched:
        return text, []
    return "[REDACTED BY LEX AUREON] The output was transformed to satisfy enterprise safety policy.", matched
