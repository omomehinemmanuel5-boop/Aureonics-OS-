from __future__ import annotations


def _semantic_diff_score(raw_output: str, governed_output: str) -> float:
    raw_words = set((raw_output or "").lower().split())
    governed_words = set((governed_output or "").lower().split())
    union_words = raw_words | governed_words
    if not union_words:
        return 0.0
    overlap = len(raw_words & governed_words) / len(union_words)
    return round(float(1.0 - overlap), 6)


def to_lex_response(raw: str, governed: str, final: str, intervention: bool, reason: str, M: float, diff: float) -> dict:
    return {
        "raw_output": raw,
        "governed_output": governed,
        "final_output": final,
        "intervention": bool(intervention),
        "intervention_reason": reason,
        "M": round(float(M), 6),
        "semantic_diff_score": round(float(diff), 6),
    }


def from_kernel_result(raw_output: str, governed_output: str, M: float) -> dict:
    intervention = raw_output.strip() != governed_output.strip()
    intervention_reason = (
        "Lex Aureon modified the output to stabilize behavior."
        if intervention
        else "No intervention required; raw output already stable."
    )
    return to_lex_response(
        raw=raw_output,
        governed=governed_output,
        final=governed_output,
        intervention=intervention,
        reason=intervention_reason,
        M=M,
        diff=_semantic_diff_score(raw_output, governed_output),
    )
