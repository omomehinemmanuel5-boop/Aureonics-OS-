-- Lex Memory Engine schema (append-only governance memory)
create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists public.lex_memory_events (
  id uuid primary key default gen_random_uuid(),
  created_at timestamp with time zone default now(),
  prompt text not null,
  response_raw text,
  response_governed text,
  response_final text,
  intervention boolean default false,
  intervention_reason text,
  semantic_diff_score double precision,
  m double precision,
  c double precision,
  r double precision,
  s double precision,
  state_label text,
  embedding vector(1536),
  model text,
  version text,
  session_id text
);

create table if not exists public.lex_memory_index (
  id uuid primary key default gen_random_uuid(),
  memory_id uuid references public.lex_memory_events(id),
  embedding vector(1536),
  created_at timestamp with time zone default now()
);

create index if not exists lex_memory_index_embedding_idx
  on public.lex_memory_index using ivfflat (embedding vector_cosine_ops);

-- immutable, append-only controls
create or replace function public.prevent_lex_memory_mutation()
returns trigger
language plpgsql
as $$
begin
  raise exception 'lex memory tables are append-only';
end;
$$;

drop trigger if exists lex_memory_events_no_update on public.lex_memory_events;
create trigger lex_memory_events_no_update
before update or delete on public.lex_memory_events
for each row execute function public.prevent_lex_memory_mutation();

drop trigger if exists lex_memory_index_no_update on public.lex_memory_index;
create trigger lex_memory_index_no_update
before update or delete on public.lex_memory_index
for each row execute function public.prevent_lex_memory_mutation();

create or replace function public.match_lex_memory(
  query_embedding vector(1536),
  match_count int default 5
)
returns table (
  id uuid,
  prompt text,
  response_final text,
  state_label text,
  intervention boolean,
  m double precision,
  embedding vector(1536),
  similarity double precision
)
language sql
stable
as $$
  select
    e.id,
    e.prompt,
    e.response_final,
    e.state_label,
    e.intervention,
    e.m,
    e.embedding,
    1 - (i.embedding <=> query_embedding) as similarity
  from public.lex_memory_index i
  join public.lex_memory_events e on e.id = i.memory_id
  order by i.embedding <=> query_embedding
  limit greatest(match_count, 1);
$$;
