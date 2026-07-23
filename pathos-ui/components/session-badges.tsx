import clsx from "clsx";
import styles from "./session-badges.module.css";

function formatAgentName(agentName: string) {
  const normalized = agentName.toLowerCase();

  if (normalized === "planner") return "Planner";
  if (normalized === "risk_agent") return "Risk Agent";
  if (normalized === "judge_agent") return "Judge Agent";

  return agentName
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function RoundBadge({ roundNo }: { roundNo?: number | null }) {
  return (
    <span className={clsx(styles.badge, styles.round)}>
      {roundNo ? `Round ${roundNo}` : "No round"}
    </span>
  );
}

export function AgentBadge({ agentName }: { agentName: string }) {
  const normalized = agentName.toLowerCase();

  return (
    <span
      className={clsx(
        styles.badge,
        styles.agent,
        normalized === "planner" && styles.planner,
        normalized === "risk_agent" && styles.risk,
        normalized === "judge_agent" && styles.judge
      )}
    >
      {formatAgentName(agentName)}
    </span>
  );
}

export function ClaimSideBadge({ side }: { side: string }) {
  const normalized = side.toLowerCase();

  return (
    <span
      className={clsx(
        styles.badge,
        styles.side,
        normalized === "bull" && styles.bull,
        normalized === "bear" && styles.bear
      )}
    >
      {normalized === "bull" ? "Bull case" : normalized === "bear" ? "Bear case" : side}
    </span>
  );
}