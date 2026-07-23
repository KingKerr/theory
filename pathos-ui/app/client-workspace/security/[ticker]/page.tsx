import { createSession } from "@/lib/api";
import Link from "next/link";
import type { CreateSessionResponse } from "@/lib/types";
import styles from "./page.module.css";

type Props = {
  params: Promise<{ ticker: string }>;
};

function pretty(value: string) {
  return value.replace(/_/g, " ");
}

function countKeys(value: Record<string, unknown> | undefined) {
  return value ? Object.keys(value).length : 0;
}

export default async function SecurityPage({ params }: Props) {
  const { ticker } = await params;
  const normalizedTicker = ticker.toUpperCase();

  try {
    const data: CreateSessionResponse = await createSession(normalizedTicker);
    const session = data.session;
    const worldState = session.world_state;

    return (
      <main className={styles.page}>
        <section className={styles.hero}>
          <div className={styles.heroEyebrow}>Security workspace</div>

          <div className={styles.heroGrid}>
            <div className={styles.heroCopy}>
              <h1 className={styles.title}>{worldState.security.ticker}</h1>
              <p className={styles.subtitle}>
                Session bootstrap completed. The security context, world state, and
                workspace scaffolding are now available for the next analysis layer.
              </p>
            </div>

            <aside className={styles.statusCard}>
              <div className={styles.statusHeader}>
                <span className={styles.statusDot} />
                <span className={styles.statusText}>{data.status}</span>
              </div>

              <dl className={styles.metaList}>
                <div className={styles.metaRow}>
                  <dt>Session ID</dt>
                  <dd className={styles.metaMono}>{data.session_id}</dd>
                </div>
                <div className={styles.metaRow}>
                  <dt>As of date</dt>
                  <dd>{worldState.security.as_of_date ?? "Live / latest"}</dd>
                </div>
                <div className={styles.metaRow}>
                  <dt>State version</dt>
                  <dd>{worldState.state_version}</dd>
                </div>
              </dl>
              <div className={styles.heroActions}>
                <Link href={`/client-workspace/sessions/${data.session_id}`} className={styles.primaryAction}>
                  Proceed to debate
                </Link>
              </div>
            </aside>
          </div>
        </section>

        <section className={styles.metricStrip}>
          <article className={styles.metricCard}>
            <span className={styles.metricLabel}>Actions</span>
            <strong className={styles.metricValue}>{session.actions.length}</strong>
          </article>

          <article className={styles.metricCard}>
            <span className={styles.metricLabel}>Claims</span>
            <strong className={styles.metricValue}>{session.claims.length}</strong>
          </article>

          <article className={styles.metricCard}>
            <span className={styles.metricLabel}>Controls</span>
            <strong className={styles.metricValue}>{countKeys(session.controls)}</strong>
          </article>

          <article className={styles.metricCard}>
            <span className={styles.metricLabel}>Memory signals</span>
            <strong className={styles.metricValue}>{countKeys(session.memory_summary)}</strong>
          </article>
        </section>

        <section className={styles.panelGrid}>
          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <p className={styles.panelEyebrow}>Security context</p>
              <h2 className={styles.panelTitle}>World state</h2>
            </div>

            <div className={styles.kvList}>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Ticker</div>
                <div className={styles.kvValue}>{worldState.security.ticker}</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>As of date</div>
                <div className={styles.kvValue}>
                  {worldState.security.as_of_date ?? "Latest available context"}
                </div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Market state</div>
                <div className={styles.kvValue}>{countKeys(worldState.market_state)} fields</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Fundamental state</div>
                <div className={styles.kvValue}>{countKeys(worldState.fundamental_state)} fields</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Event state</div>
                <div className={styles.kvValue}>{countKeys(worldState.event_state)} fields</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Peer state</div>
                <div className={styles.kvValue}>{countKeys(worldState.peer_state)} fields</div>
              </div>
            </div>
          </article>

          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <p className={styles.panelEyebrow}>Session internals</p>
              <h2 className={styles.panelTitle}>Workspace contents</h2>
            </div>

            <div className={styles.kvList}>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Session status</div>
                <div className={styles.kvValue}>{data.status}</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Action objects</div>
                <div className={styles.kvValue}>{session.actions.length} loaded</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Claim objects</div>
                <div className={styles.kvValue}>{session.claims.length} loaded</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Controls payload</div>
                <div className={styles.kvValue}>{countKeys(session.controls)} keys</div>
              </div>
              <div className={styles.kvRow}>
                <div className={styles.kvKey}>Memory summary</div>
                <div className={styles.kvValue}>{countKeys(session.memory_summary)} keys</div>
              </div>
            </div>
          </article>
        </section>

        <section className={styles.detailGrid}>
          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <p className={styles.panelEyebrow}>Controls</p>
              <h2 className={styles.panelTitle}>Control payload</h2>
            </div>
            <pre className={styles.codeBlock}>
              {JSON.stringify(session.controls, null, 2)}
            </pre>
          </article>

          <article className={styles.panel}>
            <div className={styles.panelHeader}>
              <p className={styles.panelEyebrow}>Memory</p>
              <h2 className={styles.panelTitle}>Summary payload</h2>
            </div>
            <pre className={styles.codeBlock}>
              {JSON.stringify(session.memory_summary, null, 2)}
            </pre>
          </article>
        </section>

        <section className={styles.rawSection}>
          <div className={styles.panelHeader}>
            <p className={styles.panelEyebrow}>Developer view</p>
            <h2 className={styles.panelTitle}>Raw response</h2>
          </div>
          <pre className={styles.rawBlock}>{JSON.stringify(data, null, 2)}</pre>
        </section>
      </main>
    );
  } catch (error) {
    return (
      <main className={styles.page}>
        <section className={styles.errorHero}>
          <div className={styles.errorBadge}>Launch failed</div>
          <h1 className={styles.title}>{normalizedTicker}</h1>
          <p className={styles.subtitle}>
            The workspace request did not complete successfully, so the route is
            rendering the server-side error for inspection.
          </p>

          <div className={styles.errorPanel}>
            <p className={styles.errorLabel}>Server error</p>
            <pre className={styles.rawBlock}>{String(error)}</pre>
          </div>
        </section>
      </main>
    );
  }
}