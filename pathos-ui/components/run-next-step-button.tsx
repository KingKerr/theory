"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import clsx from "clsx";

import { stepSession } from "@/lib/api";
import styles from "./run-next-step-button.module.css";

type Props = {
  sessionId: string;
  maxEvidenceItems?: number;
};

export function RunNextStepButton({
  sessionId,
  maxEvidenceItems = 3,
}: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (isPending || isRunning) return;

    setError(null);
    setIsRunning(true);

    try {
      await stepSession(sessionId, maxEvidenceItems);

      startTransition(() => {
        router.refresh();
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run next step");
    } finally {
      setIsRunning(false);
    }
  }

  const busy = isPending || isRunning;

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        onClick={handleClick}
        disabled={busy}
        aria-busy={busy}
        className={clsx(styles.button, busy && styles.buttonPending)}
      >
        <span className={styles.buttonInner}>
          <span
            className={clsx(styles.signal, busy && styles.signalPending)}
            aria-hidden="true"
          />
          <span>{busy ? "Running next step..." : "Run next step"}</span>
        </span>
      </button>

      <div className={styles.feedbackRow} aria-live="polite">
        {error ? (
          <p className={styles.errorText}>{error}</p>
        ) : (
          <p className={styles.helperText}>
            Executes the next reasoning cycle and refreshes the session view.
          </p>
        )}
      </div>
    </div>
  );
}