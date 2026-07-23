create table if not exists security_session (
  session_id uuid primary key,
  ticker text not null,
  as_of_date date,
  window_days integer not null default 180,
  mode text not null default 'debate',
  status text not null default 'created',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_security_session_ticker
  on security_session (ticker);

create table if not exists world_state_snapshot (
  snapshot_id uuid primary key,
  session_id uuid not null references security_session(session_id) on delete cascade,
  state_version text not null,
  market_state jsonb not null,
  fundamental_state jsonb not null,
  event_state jsonb not null,
  peer_state jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_world_state_snapshot_session_id
  on world_state_snapshot (session_id);