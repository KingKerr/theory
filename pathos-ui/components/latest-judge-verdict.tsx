import clsx from "clsx";
import { MemorySummary } from "@/lib/types";
import styles from "./latest-judge-verdict.module.css";

type JudgeCheck = {
  check_type?: string;
  status?: string;
};

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusClass(status: string) {
  if (status === "pass") return styles.pass;
  if (status === "warn") return styles.warn;
  if (status === "fail") return styles.fail;
  return styles.unknown;
}

function labelForCheckType(type: string) {
  if (type === "distinct_evidence") return "Distinct evidence";
  if (type === "contradiction_quality") return "Contradiction quality";
  if (type === "unsupported_repetition") return "Repetition drift";
  return type.replaceAll("_", " ");
}

function labelForStatus(status: string) {
  if (status === "pass") return "Pass";
  if (status === "warn") return "Watch";
  if (status === "fail") return "Fail";
  return "Unknown";
}

export function LatestJudgeVerdict({ memory }: { memory: MemorySummary }) {
  const latestJudgeEpisode = [...(memory.episodes ?? [])]
    .filter((episode) => episode.episode_type === "judge_summary")
    .sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )[0];

  if (!latestJudgeEpisode) {
    return (
      <section className={styles.empty}>
        <div className={styles.emptyHeader}>
          <p className={styles.eyebrow}>Latest Judge Verdict</p>
        </div>
        <p className={styles.emptyTitle}>No verdict recorded yet</p>
        <p className={styles.emptyText}>
          Run enough steps to reach the JudgeAgent turn in the three-agent loop.
        </p>
      </section>
    );
  }

  const judgeConfidence =
    typeof latestJudgeEpisode.payload?.judge_confidence === "number"
      ? (latestJudgeEpisode.payload.judge_confidence as number)
      : null;

  const judgeClaim =
    typeof latestJudgeEpisode.payload?.judge_claim === "string"
      ? (latestJudgeEpisode.payload.judge_claim as string)
      : latestJudgeEpisode.summary;

  const checks = Array.isArray(latestJudgeEpisode.payload?.checks)
    ? (latestJudgeEpisode.payload.checks as JudgeCheck[])
    : [];

  return (
    <section className={styles.card}>
      <div className={styles.header}>
        <div>
          <p className={styles.eyebrow}>Latest Judge Verdict</p>
          <p className={styles.timestamp}>
            {formatTimestamp(latestJudgeEpisode.created_at)}
          </p>
        </div>

        <div className={styles.scoreWrap}>
          <p className={styles.score}>
            {judgeConfidence !== null ? judgeConfidence.toFixed(2) : "N/A"}
          </p>
          <span className={styles.scoreLabel}>Judge confidence</span>
        </div>
      </div>

      <p className={styles.summary}>{judgeClaim}</p>

      <div className={styles.grid}>
        {checks.length === 0 ? (
          <div className={clsx(styles.metric, styles.metricNeutral)}>
            <p className={styles.metricLabel}>Checks</p>
            <p className={styles.metricValue}>No checks recorded</p>
          </div>
        ) : (
          checks.slice(0, 3).map((check, index) => {
            const type = String(check.check_type ?? "unknown");
            const status = String(check.status ?? "unknown");

            return (
              <div
                key={`${type}-${index}`}
                className={clsx(styles.metric, statusClass(status))}
              >
                <p className={styles.metricLabel}>{labelForCheckType(type)}</p>
                <p className={styles.metricValue}>{labelForStatus(status)}</p>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}