create table if not exists evidence_item (
  evidence_id uuid primary key,
  session_id uuid not null references security_session(session_id) on delete cascade,
  source_type text not null,
  source_ref text,
  observed_at timestamptz,
  title text not null,
  summary text not null,
  payload jsonb not null default '{}'::jsonb,
  freshness_score double precision not null default 0.0,
  confidence double precision not null default 0.0,
  created_at timestamptz not null default now()
);

create index if not exists idx_evidence_item_session_id
  on evidence_item (session_id);

create table if not exists agent_action (
  action_id uuid primary key,
  session_id uuid not null references security_session(session_id) on delete cascade,
  round_no integer not null,
  agent_name text not null,
  action_type text not null,
  rationale text not null,
  evidence_ids uuid[] not null default '{}',
  confidence double precision not null default 0.0,
  created_at timestamptz not null default now()
);

create index if not exists idx_agent_action_session_round
  on agent_action (session_id, round_no);

create table if not exists agent_claim (
  claim_id uuid primary key,
  session_id uuid not null references security_session(session_id) on delete cascade,
  round_no integer not null,
  side text not null,
  thesis text not null,
  confidence double precision not null default 0.0,
  evidence_ids uuid[] not null default '{}',
  status text not null default 'active',
  created_at timestamptz not null default now()
);

create index if not exists idx_agent_claim_session_round
  on agent_claim (session_id, round_no);

create table if not exists control_check (
  control_check_id uuid primary key,
  session_id uuid not null references security_session(session_id) on delete cascade,
  check_type text not null,
  status text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_control_check_session_id
  on control_check (session_id);