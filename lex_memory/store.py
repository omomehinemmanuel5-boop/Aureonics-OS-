from __future__ import annotations

from lex_memory.schema import LexMemoryEvent


def store_memory(event: LexMemoryEvent, supabase) -> dict | None:
    """Append-only insert into authoritative memory table and vector index."""
    payload = event.to_record()
    inserted = supabase.table("lex_memory_events").insert(payload).execute()

    data = getattr(inserted, "data", None) or []
    if not data:
        return None

    memory_id = data[0].get("id")
    if memory_id:
        supabase.table("lex_memory_index").insert(
            {"memory_id": memory_id, "embedding": event.embedding}
        ).execute()
    return data[0]
