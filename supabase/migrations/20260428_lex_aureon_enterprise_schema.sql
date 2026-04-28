create extension if not exists "uuid-ossp";
create extension if not exists vector;

create table if not exists organizations (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  stripe_customer_id text,
  plan text not null default 'developer',
  created_at timestamptz not null default now()
);

create table if not exists users (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid not null references organizations(id) on delete cascade,
  email text not null unique,
  role text not null,
  password_hash text,
  created_at timestamptz not null default now()
);

create table if not exists policies (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid not null references organizations(id) on delete cascade,
  name text not null,
  description text,
  rule_type text not null,
  action text not null,
  severity text not null,
  enabled boolean not null default true,
  conditions jsonb not null default '{}'::jsonb,
  version integer not null default 1,
  created_by uuid references users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists ai_logs (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid not null references organizations(id) on delete cascade,
  user_id uuid references users(id),
  model_name text not null,
  prompt text,
  raw_output text not null,
  governed_output text,
  final_output text,
  risk_score numeric(5,4),
  risk_explanation text,
  immutable_hash text not null,
  prev_hash text,
  trace jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists governance_metrics (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid not null references organizations(id) on delete cascade,
  ai_log_id uuid references ai_logs(id) on delete cascade,
  risk_reduction_score numeric(6,4) not null,
  meaning_preserved_score numeric(6,4) not null,
  governance_effectiveness numeric(6,4) not null,
  created_at timestamptz not null default now()
);

create table if not exists vector_memory (
  id uuid primary key default uuid_generate_v4(),
  organization_id uuid not null references organizations(id) on delete cascade,
  ai_log_id uuid references ai_logs(id) on delete cascade,
  raw_output text not null,
  correction text,
  embedding vector(1536) not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_ai_logs_org_created on ai_logs(organization_id, created_at desc);
create index if not exists idx_policies_org_enabled on policies(organization_id, enabled);
create index if not exists idx_vector_memory_org on vector_memory(organization_id);

alter table organizations enable row level security;
alter table users enable row level security;
alter table policies enable row level security;
alter table ai_logs enable row level security;
alter table governance_metrics enable row level security;
alter table vector_memory enable row level security;

create policy organizations_isolation on organizations
  using (id::text = auth.jwt()->>'org_id');
create policy users_isolation on users
  using (organization_id::text = auth.jwt()->>'org_id')
  with check (organization_id::text = auth.jwt()->>'org_id');
create policy policies_isolation on policies
  using (organization_id::text = auth.jwt()->>'org_id')
  with check (organization_id::text = auth.jwt()->>'org_id');
create policy ai_logs_isolation on ai_logs
  using (organization_id::text = auth.jwt()->>'org_id')
  with check (organization_id::text = auth.jwt()->>'org_id');
create policy governance_metrics_isolation on governance_metrics
  using (organization_id::text = auth.jwt()->>'org_id')
  with check (organization_id::text = auth.jwt()->>'org_id');
create policy vector_memory_isolation on vector_memory
  using (organization_id::text = auth.jwt()->>'org_id')
  with check (organization_id::text = auth.jwt()->>'org_id');

create or replace function match_governance_memories(
  p_organization_id uuid,
  query_embedding vector(1536),
  match_count int default 5
)
returns table(
  id uuid,
  raw_output text,
  correction text,
  similarity float
)
language sql
as $$
  select vm.id, vm.raw_output, vm.correction, 1 - (vm.embedding <=> query_embedding) as similarity
  from vector_memory vm
  where vm.organization_id = p_organization_id
  order by vm.embedding <=> query_embedding
  limit match_count;
$$;
