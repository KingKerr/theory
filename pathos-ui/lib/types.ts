export type SecurityRef = {
  ticker: string;
  as_of_date?: string | null;
};

export type QualityMetrics = {
  debate_quality_score: number;
  evidence_diversity_score: number;
  repetition_risk_score: number;
  judge_check_count: number;
}

export type SessionDetailResponse = {
  metadata: SessionMetadata;
  world_state: WorldState;
  evidence_items: EvidenceItem[];
  actions: AgentAction[];
  claims: Claim[];
  controls: Record<string, unknown>;
  memory_summary: Record<string, unknown>;
  quality_metrics: QualityMetrics;
};

export type WorldState = {
  security: SecurityRef;
  market_state: Record<string, unknown>;
  fundamental_state: Record<string, unknown>;
  event_state: Record<string, unknown>;
  peer_state: Record<string, unknown>;
  state_version: string;
};

export type SessionState = {
  session_id: string;
  world_state: WorldState;
  actions: unknown[];
  claims: unknown[];
  controls: Record<string, unknown>;
  memory_summary: Record<string, unknown>;
};

export type CreateSessionResponse = {
  session_id: string;
  status: string;
  session: SessionState;
};

export type StepSessionResponse = {
  session_id: string;
  step_status: string;
  action: AgentAction;
  claim?: Claim | null;
  controls: Record<string, unknown>;
  stepped_at: string;
};

export type AgentAction = {
  round_no?: number | null;
  agent_name: string;
  action_type: string;
  rationale: string;
  evidence_ids: string[];
  confidence: number;
};

export type Claim = {
  claim_id: string;
  round_no?: number | null;
  side: string;
  thesis: string;
  confidence: number;
  evidence_ids: string[];
  status: string;
};

export type MemoryEpisode = {
  episode_type: string;
  summary: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type MemorySummary = {
  total_episodes: number;
  by_type: Record<string, number>;
  episodes: MemoryEpisode[];
};

export type SessionListItem = {
  session_id: string;
  ticker: string;
  mode: string;
  updated_at?: string | null;
  total_actions: number;
  total_claims: number;
  total_episodes: number;
};