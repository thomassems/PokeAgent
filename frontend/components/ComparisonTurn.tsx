"use client";

import { useState } from "react";
import { AGENTS, type AgentId } from "@/lib/agents";
import type { RunState } from "@/lib/run-state";
import { AgentRunPanel } from "./AgentRunPanel";

type ComparisonTurnProps = {
  id: number;
  prompt: string;
  runs: Record<AgentId, RunState>;
};

export function ComparisonTurn({ id, prompt, runs }: ComparisonTurnProps) {
  const [visibleAgent, setVisibleAgent] = useState<AgentId>(AGENTS[0].id);

  return (
    <section id={`chat-turn-${id}`} className="chat-turn">
      {/* The prompt is shown once. Both panels answered this same question. */}
      <div className="chat-user-message">
        <p>{prompt}</p>
      </div>

      {/*
        Tabs exist only below the panels breakpoint. Above it both panels are
        visible, where tab semantics would be a lie - so these are plain toggle
        buttons with aria-pressed rather than a full ARIA tablist, and the
        inactive panel is display:none so it leaves the accessibility tree too.
      */}
      <div className="chat-agent-tabs">
        {AGENTS.map(({ id: agentId, label }) => (
          <button
            key={agentId}
            type="button"
            onClick={() => setVisibleAgent(agentId)}
            aria-pressed={visibleAgent === agentId}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="chat-agent-grid">
        {AGENTS.map(({ id: agentId, label }) => (
          <div
            key={agentId}
            className={`chat-agent-slot${visibleAgent === agentId ? " is-visible" : ""}`}
          >
            <AgentRunPanel label={label} run={runs[agentId]} />
          </div>
        ))}
      </div>
    </section>
  );
}
