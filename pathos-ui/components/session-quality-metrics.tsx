import clsx from "clsx";
import { QualityMetrics } from "@/lib/types";
import styles from "./session-quality-metrics.module.css";

function toneForScore(score: number, inverse = false) {
  if (!inverse) {
    if (score >= 0.75) return styles.good;
    if (score >= 0.45) return styles.warn;
    return styles.bad;
  }

  if (score <= 0.25) return styles.good;
  if (score <= 0.55) return styles.warn;
  return styles.bad;
}

function toneLabel(score: number, inverse = false) {
  if (!inverse) {
    if (score >= 0.75) return "Strong";
    if (score >= 0.45) return "Watch";
    return "Weak";
  }

  if (score <= 0.25) return "Contained";
  if (score <= 0.55) return "Watch";
  return "Elevated";
}

function MetricCard({
  label,
  value,
  meta,
  inverse = false,
}: {
  label: string;
  value: number;
  meta: string;
  inverse?: boolean;
}) {
  const toneClass = toneForScore(value, inverse);
  const toneText = toneLabel(value, inverse);

  return (
    <article className={clsx(styles.card, toneClass)}>
      <div className={styles.cardTop}>
        <p className={styles.label}>{label}</p>
        <span className={styles.status}>
          <span className={styles.statusDot} aria-hidden="true" />
          {toneText}
        </span>
      </div>

      <p className={styles.value}>{value.toFixed(2)}</p>
      <p className={styles.meta}>{meta}</p>
    </article>
  );
}

function CountCard({ label, value, meta }: { label: string; value: number; meta: string }) {
  return (
    <article className={clsx(styles.card, styles.neutral)}>
      <div className={styles.cardTop}>
        <p className={styles.label}>{label}</p>
        <span className={styles.status}>
          <span className={styles.statusDot} aria-hidden="true" />
          Recorded
        </span>
      </div>

      <p className={styles.value}>{value}</p>
      <p className={styles.meta}>{meta}</p>
    </article>
  );
}

export function SessionQualityMetrics({
  metrics,
}: {
  metrics?: QualityMetrics | null;
}) {
  if (!metrics) {
    return null;
  }

  return (
    <section className={styles.grid} aria-label="Session quality metrics">
      <MetricCard
        label="Debate quality"
        value={metrics.debate_quality_score ?? 0}
        meta="Higher is better."
      />
      <MetricCard
        label="Evidence diversity"
        value={metrics.evidence_diversity_score ?? 0}
        meta="Higher means bull and bear rely on more distinct evidence."
      />
      <MetricCard
        label="Repetition risk"
        value={metrics.repetition_risk_score ?? 0}
        meta="Lower is better."
        inverse
      />
      <CountCard
        label="Judge checks"
        value={metrics.judge_check_count ?? 0}
        meta="Persisted evaluation checks written so far."
      />
    </section>
  );
}