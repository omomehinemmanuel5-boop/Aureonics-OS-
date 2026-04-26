from lex_memory.embedder import DeterministicEmbedder, embed
from lex_memory.retrieve import adjusted_memory_score, construct_context
from lex_memory.schema import LexMemoryEvent


def test_embedder_deterministic_shape():
    vec = embed("hello world", model=DeterministicEmbedder())
    assert len(vec) == 1536
    assert vec == embed("hello world", model=DeterministicEmbedder())


def test_adjusted_score_applies_governance_biases():
    current = [1.0, 0.0]
    past = {"embedding": [1.0, 0.0], "intervention": True, "M": 0.2}
    score = adjusted_memory_score(current, past)
    assert score == 1.32


def test_construct_context_shape():
    out = construct_context(
        "new prompt",
        [
            {
                "prompt": "old prompt",
                "response_final": "old result",
                "state_label": "INTERVENED",
                "M": 0.2,
                "adjusted_score": 0.9,
            }
        ],
    )
    assert out["current_prompt"] == "new prompt"
    assert out["memory_context"][0]["past_prompt"] == "old prompt"


def test_memory_event_record_contains_append_only_fields():
    event = LexMemoryEvent(
        prompt="p",
        response_raw="r",
        response_governed="g",
        response_final="f",
        intervention=False,
        intervention_reason="none",
        semantic_diff_score=0.0,
        M=0.2,
        C=0.3,
        R=0.3,
        S=0.4,
        state_label="STABLE",
        embedding=[0.1, 0.2],
    )
    row = event.to_record()
    assert row["prompt"] == "p"
    assert row["state_label"] == "STABLE"
