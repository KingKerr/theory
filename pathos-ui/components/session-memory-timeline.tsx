import clsx from "clsx";
import { MemoryEpisode, MemorySummary } from "@/lib/types";
import styles from "./session-memory-timeline.module.css";

function formatEpisodeType(type: string) {
  if (type === "world_state") return "World state";
  if (type === "judge_summary") return "Judge summary";
  if (type === "ingestion") return "Ingestion";
  return type.replaceAll("_", " ");
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function itemClassForType(type: string) {
  if (type === "ingestion") return styles.ingestion;
  if (type === "world_state") return styles.worldState;
  if (type === "judge_summary") return styles.judgeSummary;
  return styles.defaultType;
}

function badgeClassForType(type: string) {
  if (type === "ingestion") return styles.badgeIngestion;
  if (type === "world_state") return styles.badgeWorldState;
  if (type === "judge_summary") return styles.badgeJudgeSummary;
  return styles.badgeDefault;
}

function renderPayload(episode: MemoryEpisode) {
  if (episode.episode_type === "judge_summary") {
    const judgeConfidence =
      typeof episode.payload?.judge_confidence === "number"
        ? (episode.payload.judge_confidence as number)
        : null;

    const judgeClaim =
      typeof episode.payload?.judge_claim === "string"
        ? (episode.payload.judge_claim as string)
        : null;

    const checks = Array.isArray(episode.payload?.checks)
      ? (episode.payload.checks as Array<Record<string, unknown>>)
      : [];

    return (
      <div className={styles.payloadGrid}>
        <div className={styles.payloadCard}>
          <p className={styles.payloadLabel}>Judge confidence</p>
          <p className={styles.payloadValue}>
            {judgeConfidence !== null ? judgeConfidence.toFixed(2) : "N/A"}
          </p>
        </div>

        <div className={styles.payloadCard}>
          <p className={styles.payloadLabel}>Judge claim</p>
          <p className={styles.payloadValue}>{judgeClaim ?? "No judge claim."}</p>
        </div>

        <div className={styles.payloadCard}>
          <p className={styles.payloadLabel}>Checks</p>
          <div className={styles.checkList}>
            {checks.length === 0 ? (
              <p className={styles.payloadValue}>No checks recorded.</p>
            ) : (
              checks.map((check, index) => {
                const status = String(check.status ?? "unknown");
                const type = String(check.check_type ?? "unknown").replaceAll("_", " ");

                return (
                  <div key={`${type}-${index}`} className={styles.checkItem}>
                    <span className={styles.checkType}>{type}</span>
                    <span
                      className={clsx(
                        styles.checkStatus,
                        status === "pass" && styles.statusPass,
                        status === "warn" && styles.statusWarn,
                        status === "fail" && styles.statusFail,
                        status !== "pass" &&
                          status !== "warn" &&
                          status !== "fail" &&
                          styles.statusUnknown
                      )}
                    >
                      {status}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <pre className={styles.code}>
      {JSON.stringify(episode.payload ?? {}, null, 2)}
    </pre>
  );
}

export function SessionMemoryTimeline({ memory }: { memory: MemorySummary }) {
  const episodes = [...(memory.episodes ?? [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <section className={styles.wrapper}>
      <div className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Session memory</p>
          <h2 className={styles.title}>Memory timeline</h2>
        </div>
        <span className={styles.meta}>{memory.total_episodes} total episodes</span>
      </div>

      {episodes.length === 0 ? (
        <p className={styles.empty}>No memory episodes yet.</p>
      ) : (
        <div className={styles.timeline}>
          {episodes.map((episode, index) => (
            <article
              key={`${episode.episode_type}-${episode.created_at}-${index}`}
              className={clsx(styles.item, itemClassForType(episode.episode_type))}
            >
              <div className={styles.rail} aria-hidden="true">
                <span className={styles.dot} />
                {index < episodes.length - 1 ? <span className={styles.line} /> : null}
              </div>

              <div className={styles.content}>
                <div className={styles.topRow}>
                  <span
                    className={clsx(
                      styles.badge,
                      badgeClassForType(episode.episode_type)
                    )}
                  >
                    {formatEpisodeType(episode.episode_type)}
                  </span>

                  <span className={styles.timestamp}>
                    {formatTimestamp(episode.created_at)}
                  </span>
                </div>

                <p className={styles.summary}>{episode.summary}</p>
                {renderPayload(episode)}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}