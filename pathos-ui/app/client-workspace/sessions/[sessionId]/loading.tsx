import styles from "./session-loading.module.css";

export default function LoadingSessionPage() {
  return (
    <main className={styles.page} aria-busy="true" aria-live="polite">
      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <div className={styles.eyebrow} />
          <div className={styles.title} />
          <div className={styles.sessionId} />
        </div>

        <div className={styles.heroAction} />
      </section>

      <section className={styles.metricsRow}>
        <div className={styles.metricCard} />
        <div className={styles.metricCard} />
        <div className={styles.metricCard} />
        <div className={styles.metricCard} />
      </section>

      <section className={styles.layout}>
        <div className={styles.primaryColumn}>
          <div className={styles.panelLg}>
            <div className={styles.panelHeader}>
              <div className={styles.panelTitle} />
              <div className={styles.panelMeta} />
            </div>
            <div className={styles.codeBlock} />
          </div>

          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <div className={styles.panelTitle} />
              <div className={styles.panelMeta} />
            </div>

            <div className={styles.stack}>
              <div className={styles.card} />
              <div className={styles.card} />
              <div className={styles.card} />
            </div>
          </div>

          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <div className={styles.panelTitle} />
              <div className={styles.panelMeta} />
            </div>

            <div className={styles.stack}>
              <div className={styles.card} />
              <div className={styles.card} />
            </div>
          </div>
        </div>

        <aside className={styles.secondaryColumn}>
          <div className={styles.panelSm} />
          <div className={styles.panel}>
            <div className={styles.panelHeader}>
              <div className={styles.panelTitle} />
              <div className={styles.panelMeta} />
            </div>
            <div className={styles.codeBlockShort} />
          </div>
          <div className={styles.panelTall} />
        </aside>
      </section>
    </main>
  );
}