import clsx from "clsx";
import { getSession } from "@/lib/api";
import { RunNextStepButton } from "@/components/run-next-step-button";
import { AgentBadge, ClaimSideBadge, RoundBadge } from "@/components/session-badges";
import { SessionQualityMetrics } from "@/components/session-quality-metrics";
import { SessionMemoryTimeline } from "@/components/session-memory-timeline";
import { LatestJudgeVerdict } from "@/components/latest-judge-verdict";
import styles from "./session-page.module.css";

type Props = {
  params: Promise<{ sessionId: string }>;
};

function countKeys(value: Record<string, unknown> | null | undefined) {
  return value ? Object.keys(value).length : 0;
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

function WorldStateSummary({
  worldState,
}: {
  worldState: Record<string, any>;
}) {
  const security = worldState.security ?? {};

  const rows = [
    { label: "Ticker", value: security.ticker ?? "Unknown" },
    { label: "As of date", value: security.as_of_date ?? "Latest available context" },
    { label: "State version", value: String(worldState.state_version ?? "N/A") },
    { label: "Market state", value: `${countKeys(worldState.market_state)} fields` },
    { label: "Fundamental state", value: `${countKeys(worldState.fundamental_state)} fields` },
    { label: "Event state", value: `${countKeys(worldState.event_state)} fields` },
    { label: "Peer state", value: `${countKeys(worldState.peer_state)} fields` },
  ];

  return (
    <div className={styles.summaryGrid}>
      {rows.map((row) => (
        <div key={row.label} className={styles.summaryCard}>
          <p className={styles.summaryLabel}>{row.label}</p>
          <p className={styles.summaryValue}>{row.value}</p>
        </div>
      ))}
    </div>
  );
}

function ControlsSummary({
  controls,
}: {
  controls: Record<string, any>;
}) {
  const rows = Object.entries(controls ?? {}).map(([key, value]) => {
    let rendered = "Not available";

    if (typeof value === "boolean") rendered = value ? "Yes" : "No";
    else if (typeof value === "string" || typeof value === "number") rendered = String(value);
    else if (Array.isArray(value)) rendered = `${value.length} items`;
    else if (value && typeof value === "object") rendered = `${Object.keys(value).length} keys`;

    return {
      label: formatLabel(key),
      value: rendered,
    };
  });

  return (
    <div className={styles.summaryGrid}>
      {rows.length === 0 ? (
        <p className={styles.empty}>No control values available.</p>
      ) : (
        rows.map((row) => (
          <div key={row.label} className={styles.summaryCard}>
            <p className={styles.summaryLabel}>{row.label}</p>
            <p className={styles.summaryValue}>{row.value}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default async function SessionPage({ params }: Props) {
  const { sessionId } = await params;
  const data = await getSession(sessionId);

  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className={styles.eyebrow}>Persisted session</p>
          <div className={styles.titleRow}>
            <h1 className={styles.title}>{data.metadata.ticker}</h1>
            <div className={styles.modePill}>{data.metadata.mode}</div>
          </div>
          <p className={styles.sessionId}>Session {data.metadata.session_id}</p>
        </div>

        <div className={styles.heroActions}>
          <RunNextStepButton sessionId={data.metadata.session_id} />
        </div>
      </section>

      <section className={styles.metricsSection}>
        <SessionQualityMetrics metrics={data.quality_metrics} />
      </section>

      <section className={styles.layout}>
        <div className={styles.primaryColumn}>
          <div className={clsx(styles.panel, styles.panelTechnical)}>
            <div className={styles.panelHeader}>
              <h2 className={styles.panelTitle}>World state</h2>
              <span className={styles.panelMeta}>Grounded security snapshot</span>
            </div>

            <WorldStateSummary worldState={data.world_state} />

            <details className={styles.devDetails}>
              <summary className={styles.devSummary}>Developer view</summary>
              <pre className={styles.codeBlock}>
                {JSON.stringify(data.world_state, null, 2)}
              </pre>
            </details>
          </div>

          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <h2 className={styles.panelTitle}>Actions</h2>
              <span className={styles.panelMeta}>{data.actions.length} total</span>
            </div>

            <div className={styles.stack}>
              {data.actions.length === 0 ? (
                <p className={styles.empty}>No actions yet.</p>
              ) : (
                data.actions.map((action, idx) => {
                  const isPlanner = action.agent_name.toLowerCase() === "planner";

                  return (
                    <article
                      key={`${action.agent_name}-${action.round_no ?? idx}-${idx}`}
                      className={clsx(
                        styles.card,
                        isPlanner ? styles.cardPlanner : styles.cardRisk
                      )}
                    >
                      <div className={styles.cardTop}>
                        <div className={styles.cardBadges}>
                          <RoundBadge roundNo={action.round_no} />
                          <AgentBadge agentName={action.agent_name} />
                        </div>
                        <span className={styles.cardStatus}>{action.action_type}</span>
                      </div>

                      <p className={styles.bodyText}>{action.rationale}</p>

                      <div className={styles.metaRow}>
                        <span className={styles.metaText}>
                          Confidence {action.confidence.toFixed(2)}
                        </span>
                      </div>
                    </article>
                  );
                })
              )}
            </div>
          </div>

          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <h2 className={styles.panelTitle}>Claims</h2>
              <span className={styles.panelMeta}>{data.claims.length} total</span>
            </div>

            <div className={styles.stack}>
              {data.claims.length === 0 ? (
                <p className={styles.empty}>No claims yet.</p>
              ) : (
                data.claims.map((claim) => {
                  const isBull = claim.side.toLowerCase() === "bull";

                  return (
                    <article
                      key={claim.claim_id}
                      className={clsx(
                        styles.card,
                        isBull ? styles.cardBull : styles.cardBear
                      )}
                    >
                      <div className={styles.cardTop}>
                        <div className={styles.cardBadges}>
                          <RoundBadge roundNo={claim.round_no} />
                          <ClaimSideBadge side={claim.side} />
                        </div>
                        <span className={styles.cardStatus}>{claim.status}</span>
                      </div>

                      <p className={styles.bodyText}>{claim.thesis}</p>

                      <div className={styles.metaRow}>
                        <span className={styles.metaText}>
                          Confidence {claim.confidence.toFixed(2)}
                        </span>
                      </div>
                    </article>
                  );
                })
              )}
            </div>
          </div>
        </div>

        <aside className={styles.secondaryColumn}>
          <LatestJudgeVerdict memory={data.memory_summary} />

          <div className={clsx(styles.panel, styles.panelTechnical)}>
            <div className={styles.panelHeader}>
              <h2 className={styles.panelTitle}>Controls</h2>
              <span className={styles.panelMeta}>Runtime configuration</span>
            </div>

            <ControlsSummary controls={data.controls} />

            <details className={styles.devDetails}>
              <summary className={styles.devSummary}>Developer view</summary>
              <pre className={styles.codeBlock}>
                {JSON.stringify(data.controls, null, 2)}
              </pre>
            </details>
          </div>

          <div className={styles.panel}>
            <SessionMemoryTimeline memory={data.memory_summary} />
          </div>
        </aside>
      </section>
    </main>
  );
}