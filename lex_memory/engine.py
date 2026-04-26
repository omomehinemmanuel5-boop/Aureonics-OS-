from __future__ import annotations

from dataclasses import asdict, dataclass

from lex_memory.embedder import EmbeddingModel, embed
from lex_memory.retrieve import construct_context, retrieve_similar
from lex_memory.schema import LexMemoryEvent
from lex_memory.store import store_memory


@dataclass(slots=True)
class MemoryPipelineResult:
    raw_output: str
    governed_output: str
    final_output: str
    intervention: bool
    intervention_reason: str
    semantic_diff_score: float
    memory_context: dict
    persisted_memory: dict | None


def run_memory_pipeline(
    *,
    prompt: str,
    raw_output: str,
    governed_output: str,
    final_output: str,
    intervention: bool,
    intervention_reason: str,
    semantic_diff_score: float,
    M: float,
    C: float,
    R: float,
    S: float,
    state_label: str,
    supabase,
    embedding_model: EmbeddingModel | None = None,
    model: str | None = None,
    version: str | None = None,
    session_id: str | None = None,
    top_k: int = 5,
) -> MemoryPipelineResult:
    prompt_embedding = embed(prompt, embedding_model)
    past_memories = retrieve_similar(prompt_embedding, supabase=supabase, top_k=top_k)
    memory_context = construct_context(prompt, past_memories)

    event = LexMemoryEvent(
        prompt=prompt,
        response_raw=raw_output,
        response_governed=governed_output,
        response_final=final_output,
        intervention=intervention,
        intervention_reason=intervention_reason,
        semantic_diff_score=semantic_diff_score,
        M=M,
        C=C,
        R=R,
        S=S,
        state_label=state_label,
        embedding=prompt_embedding,
        model=model,
        version=version,
        session_id=session_id,
    )
    persisted = store_memory(event, supabase=supabase)
    return MemoryPipelineResult(
        raw_output=raw_output,
        governed_output=governed_output,
        final_output=final_output,
        intervention=intervention,
        intervention_reason=intervention_reason,
        semantic_diff_score=semantic_diff_score,
        memory_context=memory_context,
        persisted_memory=persisted,
    )


def classify_state(intervention: bool, final_output: str) -> str:
    lowered = (final_output or "").lower()
    if "can’t assist" in lowered or "cannot assist" in lowered:
        return "REFUSED"
    if intervention:
        return "INTERVENED"
    return "STABLE"


def serialize_result(result: MemoryPipelineResult) -> dict:
    return asdict(result)
