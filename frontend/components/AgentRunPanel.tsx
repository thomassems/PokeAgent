"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { RunState } from "@/lib/run-state";

type AgentRunPanelProps = {
  /** Which implementation produced this, shown so the two can be told apart. */
  label: string;
  run: RunState;
};

function elapsedLabel(startedAt: number, finishedAt: number | null, now: number): string {
  const seconds = Math.max(0, Math.floor(((finishedAt ?? now) - startedAt) / 1000));
  return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="chat-metric">
      <span className="chat-metric-label">{label}</span>
      <span className="chat-metric-value">{value}</span>
    </div>
  );
}

export function AgentRunPanel({ label, run }: AgentRunPanelProps) {
  const { status, currentActivity, answer, error, startedAt, finishedAt, metrics } = run;
  const [now, setNow] = useState(startedAt);

  useEffect(() => {
    if (status !== "running") return;
    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, [status]);

  const elapsed = elapsedLabel(startedAt, finishedAt, now);

  return (
    <section className="chat-agent-panel" aria-label={label}>
      <header className="chat-agent-header">
        <span aria-hidden="true" className="chat-agent-dot" />
        <h3>{label}</h3>
      </header>

      <div className="chat-assistant-message">
        <div className="chat-assistant-content">
          {answer && (
            <div className="chat-answer">
              <ReactMarkdown
                skipHtml
                disallowedElements={["img"]}
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ children }) => (
                    <div className="chat-table-scroll" role="region" aria-label="Response table" tabIndex={0}>
                      <table>{children}</table>
                    </div>
                  ),
                }}
              >
                {answer}
              </ReactMarkdown>
            </div>
          )}
          {status === "running" && (
            <div className="chat-activity" role="status" aria-live="polite">
              <span className="chat-activity-dot" aria-hidden="true" />
              <span className="chat-activity-label">{currentActivity}</span>
              <span className="chat-elapsed">{elapsed}</span>
            </div>
          )}
          {status === "error" && <p className="chat-error" role="alert">{error}</p>}
        </div>
      </div>

      {/*
        Elapsed is measured in the browser, so it is there even when a run fails
        before reporting. Everything else comes from the run's metrics event, so
        the footer stays partial rather than showing zeros for unknowns.
      */}
      {status !== "running" && (
        <footer className="chat-agent-metrics">
          <Metric label="Elapsed" value={elapsed} />
          {metrics && (
            <>
              <Metric label="Steps" value={String(metrics.steps)} />
              <Metric label="Tools" value={String(metrics.toolCalls)} />
              <Metric
                label="Tokens"
                value={`${metrics.inputTokens.toLocaleString()} in / ${metrics.outputTokens.toLocaleString()} out`}
              />
            </>
          )}
        </footer>
      )}
    </section>
  );
}
