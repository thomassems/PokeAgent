"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

type AgentRunPanelProps = {
  id: number;
  prompt: string;
  status: "running" | "complete" | "error";
  currentActivity: string;
  answer: string;
  error: string | null;
  startedAt: number;
  finishedAt: number | null;
};

function elapsedLabel(startedAt: number, finishedAt: number | null, now: number): string {
  const seconds = Math.max(0, Math.floor(((finishedAt ?? now) - startedAt) / 1000));
  return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

export function AgentRunPanel({ id, prompt, status, currentActivity, answer, error, startedAt, finishedAt }: AgentRunPanelProps) {
  const [now, setNow] = useState(startedAt);

  useEffect(() => {
    if (status !== "running") return;
    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, [status]);

  return (
    <section id={`chat-turn-${id}`} className="chat-turn">
      <div className="chat-user-message"><p>{prompt}</p></div>
      <div className="chat-assistant-message">
        <div className="chat-assistant-mark" aria-hidden="true">P</div>
        <div className="chat-assistant-content">
          {answer && <div className="chat-answer"><ReactMarkdown skipHtml disallowedElements={["img"]}>{answer}</ReactMarkdown></div>}
          {status === "running" && (
            <div className="chat-activity" role="status" aria-live="polite">
              <span className="chat-activity-dot" aria-hidden="true" />
              <span className="chat-activity-label">{currentActivity}</span>
              <span className="chat-elapsed">{elapsedLabel(startedAt, finishedAt, now)}</span>
            </div>
          )}
          {status === "error" && <p className="chat-error" role="alert">{error}</p>}
          {status === "complete" && <span className="chat-finished">Answered in {elapsedLabel(startedAt, finishedAt, now)}</span>}
        </div>
      </div>
    </section>
  );
}
