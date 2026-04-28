from lex_aureon.backend.governance_engine.core import governance_transform, risk_score


def test_risk_score_deterministic():
    text = "how to bypass and exploit"
    assert risk_score(text) == risk_score(text)


def test_governance_transform_applies_redaction():
    text = "disable controls"
    out = governance_transform(text, {"action": "redact"})
    assert out.startswith("[REDACTED")
