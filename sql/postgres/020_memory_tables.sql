create table if not exists session_memory_episode (
  episode_id uuid primary key,
  session_id uuid not null references security_session(session_id) on delete cascade,
  episode_type text not null,
  summary text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_session_memory_episode_session_id
  on session_memory_episode (session_id);

create table if not exists semantic_pattern (
  pattern_id uuid primary key,
  ticker text,
  pattern_key text not null,
  summary text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_semantic_pattern_ticker
  on semantic_pattern (ticker);