import { AGENTS, type AgentId } from "@/lib/agents";
import type { Game } from "@/lib/game";
import type { RunState } from "@/lib/run-state";
import { AgentRunPanel } from "./AgentRunPanel";

type ComparisonTurnProps = {
  id: number;
  prompt: string;
  game: Game;
  runs: Record<AgentId, RunState>;
};

export function ComparisonTurn({ id, prompt, game, runs }: ComparisonTurnProps) {
  return (
    <section id={`chat-turn-${id}`} className="chat-turn">
      {/* The prompt is shown once. Both panels answered this same question. */}
      <div className="chat-user-message">
        <p>
          {game === "go" && <span className="chat-user-game">Pokémon GO</span>}
          {prompt}
        </p>
      </div>

      {/* One column on a phone, two columns from the panels breakpoint up. */}
      <div className="chat-agent-grid">
        {AGENTS.map(({ id: agentId, label }) => (
          <div key={agentId} className="chat-agent-slot">
            <AgentRunPanel label={label} run={runs[agentId]} />
          </div>
        ))}
      </div>
    </section>
  );
}
