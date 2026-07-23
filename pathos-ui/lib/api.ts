import {
  CreateSessionResponse,
  SessionDetailResponse,
  SessionListItem,
  StepSessionResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000/api/v1";

export async function createSession(ticker: string): Promise<CreateSessionResponse> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ticker,
      window_days: 180,
      mode: "debate",
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to create session: ${res.status}`);
  }

  return res.json();
}

export async function getSessions(): Promise<SessionListItem[]> {
  const res = await fetch(`${API_BASE}/sessions`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch sessions: ${res.status}`);
  }

  const data = await res.json();
  const sessions = Array.isArray(data.sessions) ? data.sessions : [];

  return sessions
    .map((session) => ({
      session_id: String(session.session_id),
      ticker: String(session.ticker),
      mode: String(session.mode ?? "debate"),
      status: String(session.status ?? "unknown"),
      created_at: String(session.created_at ?? ""),
      updated_at: session.updated_at ? String(session.updated_at) : null,
      total_actions: Number(session.total_actions ?? 0),
      total_claims: Number(session.total_claims ?? 0),
      total_episodes: Number(session.total_episodes ?? 0),
    }))
    .sort((a, b) => {
      const aTime = new Date(a.updated_at ?? a.created_at).getTime();
      const bTime = new Date(b.updated_at ?? b.created_at).getTime();
      return bTime - aTime;
    });
}

export async function getSession(sessionId: string): Promise<SessionDetailResponse> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch session: ${res.status}`);
  }

  return res.json();
}

export async function stepSession(
  sessionId: string,
  maxEvidenceItems = 3
): Promise<StepSessionResponse> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/step`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      requested_by: "planner",
      max_evidence_items: maxEvidenceItems,
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Failed to step session: ${res.status}`);
  }

  return res.json();
}