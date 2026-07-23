import Link from "next/link";
import styles from "./workspace-home.module.css";
import { TickerLaunchForm } from "@/components/ticker-launch-form";
import { getSessions } from "@/lib/api";

const demoTickers = ["NVDA", "MSFT", "AMZN", "META", "NFLX"];

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatSessionId(value: string) {
  if (value.length <= 14) return value;
  return `${value.slice(0, 8)}…${value.slice(-4)}`;
}

export default async function WorkspaceHomePage() {
  const sessions = await getSessions();

  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroCopy}>
            <p className={styles.eyebrow}>Theory: Agentic market reasoning</p>
            <h1 className={styles.title}>
              Structured world state, memory, planning, and evaluation
            </h1>
            <p className={styles.description}>
              Explore a security as a real-world environment and inspect how thesis,
              risk, and judge agents reason over grounded evidence.
            </p>

            <div className={styles.actions}>
              <TickerLaunchForm />
              <div className={styles.inlineMeta}>
                <span className={styles.metaDot} />
                Massive-backed evidence
              </div>
            </div>
          </div>

          <aside className={styles.signalPanel} aria-label="Workspace summary">
            <div className={styles.signalRow}>
              <span className={styles.signalLabel}>Agents</span>
              <span className={styles.signalValue}>3 active</span>
            </div>
            <div className={styles.signalRow}>
              <span className={styles.signalLabel}>Loop</span>
              <span className={styles.signalValue}>Plan / Risk / Judge</span>
            </div>
            <div className={styles.signalRow}>
              <span className={styles.signalLabel}>Evidence</span>
              <span className={styles.signalValue}>News + Fundamentals</span>
            </div>
          </aside>
        </div>
      </section>

      <section className={styles.sessionsSection}>
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.sectionKicker}>Session history</p>
            <h2 className={styles.sectionTitle}>Recent sessions</h2>
          </div>
          <p className={styles.sectionNote}>
            Reopen prior debates, inspect memory, and continue the reasoning loop.
          </p>
        </div>

        {sessions.length === 0 ? (
          <p className={styles.sessionsEmpty}>No previous sessions yet.</p>
        ) : (
          <div className={styles.sessionsList}>
            {sessions.slice(0, 8).map((session) => (
              <Link
                key={session.session_id}
                href={`/client-workspace/sessions/${session.session_id}`}
                className={styles.sessionRow}
              >
                <div className={styles.sessionRowMain}>
                  <div className={styles.sessionIdentity}>
                    <div className={styles.sessionTickerWrap}>
                      <span className={styles.sessionTicker}>{session.ticker}</span>
                      <span className={styles.sessionMode}>{session.mode}</span>
                      <span className={styles.sessionStatus}>{session.status}</span>
                    </div>

                    <p className={styles.sessionSubtle}>
                      Session {formatSessionId(session.session_id)}
                    </p>
                  </div>

                  <div className={styles.sessionMetrics}>
                    <span>{session.total_actions} actions</span>
                    <span>{session.total_claims} claims</span>
                    <span>{session.total_episodes} episodes</span>
                  </div>
                </div>

                <div className={styles.sessionRowMeta}>
                  <span className={styles.sessionUpdated}>
                    {session.updated_at ? formatTimestamp(session.updated_at) : "Recently created"}
                  </span>
                  <span className={styles.sessionChevron}>Open ↗</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className={styles.gridSection}>
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.sectionKicker}>Demo securities</p>
            <h2 className={styles.sectionTitle}>Open a workspace</h2>
          </div>
          <p className={styles.sectionNote}>
            Start with a large-cap name and inspect the debate loop in motion.
          </p>
        </div>

        <div className={styles.tickerGrid}>
          {demoTickers.map((ticker, index) => (
            <Link
              key={ticker}
              href={`/client-workspace/security/${ticker}`}
              className={styles.securityCard}
            >
              <div className={styles.cardTop}>
                <span className={styles.cardLabel}>Open security</span>
                <span className={styles.cardIndex}>0{index + 1}</span>
              </div>

              <div className={styles.cardBody}>
                <div className={styles.ticker}>{ticker}</div>
                <p className={styles.cardText}>
                  Enter the workspace and inspect the bull, bear, and judge flow.
                </p>
              </div>

              <div className={styles.cardFooter}>
                <span className={styles.cardPill}>Live reasoning surface</span>
                <span className={styles.cardArrow}>↗</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}