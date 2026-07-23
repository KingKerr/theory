"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./ticker-launch-form.module.css";

const SUGGESTIONS = ["NVDA", "MSFT", "AMZN", "META", "NFLX"];

function normalizeTicker(value: string) {
  return value.trim().toUpperCase().replace(/[^A-Z.\-]/g, "");
}

export function TickerLaunchForm() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");

  const normalized = useMemo(() => normalizeTicker(ticker), [ticker]);
  const canLaunch = normalized.length > 0;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canLaunch) return;
    router.push(`/client-workspace/security/${normalized}`);
  }

  function handleSuggestionClick(value: string) {
    router.push(`/client-workspace/security/${value}`);
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <label htmlFor="ticker" className={styles.label}>
        Launch security workspace
      </label>

      <div className={styles.controlRow}>
        <input
          id="ticker"
          name="ticker"
          type="text"
          inputMode="text"
          autoCapitalize="characters"
          autoCorrect="off"
          spellCheck={false}
          placeholder="Enter ticker, e.g. NVDA"
          value={ticker}
          onChange={(event) => setTicker(event.target.value)}
          className={styles.input}
        />

        <button type="submit" className={styles.button} disabled={!canLaunch}>
          Launch workspace
        </button>
      </div>

      <div className={styles.suggestions}>
        {SUGGESTIONS.map((value) => (
          <button
            key={value}
            type="button"
            className={styles.suggestion}
            onClick={() => handleSuggestionClick(value)}
          >
            {value}
          </button>
        ))}
      </div>
    </form>
  );
}