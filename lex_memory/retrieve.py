from __future__ import annotations

from math import sqrt


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    limit = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(limit))
    mag_a = sqrt(sum(x * x for x in a[:limit]))
    mag_b = sqrt(sum(x * x for x in b[:limit]))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def adjusted_memory_score(current_embedding: list[float], past: dict) -> float:
    base = cosine_similarity(current_embedding, past.get("embedding") or [])
    if past.get("intervention"):
        base *= 1.2
    if float(past.get("M", 0.0)) > 0.15:
        base *= 1.1
    return round(base, 8)


def retrieve_similar(prompt_embedding: list[float], supabase, top_k: int = 5) -> list[dict]:
    result = supabase.rpc(
        "match_lex_memory",
        {
            "query_embedding": prompt_embedding,
            "match_count": top_k,
        },
    ).execute()
    rows = getattr(result, "data", None) or []
    rescored = []
    for row in rows:
        row = dict(row)
        row["adjusted_score"] = adjusted_memory_score(prompt_embedding, row)
        rescored.append(row)
    rescored.sort(key=lambda item: item["adjusted_score"], reverse=True)
    return rescored[:top_k]


def construct_context(prompt: str, retrieved_memories: list[dict]) -> dict:
    context = []
    for m in retrieved_memories:
        context.append(
            {
                "past_prompt": m.get("prompt", ""),
                "past_outcome": m.get("response_final", ""),
                "state": m.get("state_label", "UNSTABLE"),
                "M": float(m.get("M", 0.0)),
                "adjusted_score": float(m.get("adjusted_score", 0.0)),
            }
        )
    return {
        "current_prompt": prompt,
        "memory_context": context,
    }
