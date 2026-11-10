"use client";

import { useEffect, useRef, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { ComparisonTurn } from "@/components/ComparisonTurn";
import { PromptPanel } from "@/components/PromptPanel";
import { AGENT_IDS, type AgentId } from "@/lib/agents";
import { readAgentStream } from "@/lib/agent-stream";
import { applyAgentEvent, newRun, type RunState } from "@/lib/run-state";
import type { Generation } from "@/lib/types";

const EXAMPLE_PROMPTS = [
  "What makes a good fast Electric type?",
  "What does Body Slam do?",
  "How did Steel resist Ghost in Generation 4?",
];

/** One question, answered by every implementation. */
type Turn = {
  id: number;
  prompt: string;
  generation: Generation;
  runs: Record<AgentId, RunState>;
};

export default function Home() {
  const [generation, setGeneration] = useState<Generation>(4);
  const [prompt, setPrompt] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const activeRequest = useRef<AbortController | null>(null);
  const nextTurnId = useRef(0);
  const newestTurnId = turns.at(-1)?.id;
  const isRunning = turns.some((turn) =>
    AGENT_IDS.some((agent) => turn.runs[agent].status === "running"),
  );

  useEffect(() => () => activeRequest.current?.abort(), []);
  useEffect(() => {
    if (newestTurnId !== undefined) {
      document.getElementById(`chat-turn-${newestTurnId}`)?.scrollIntoView({ block: "start" });
    }
  }, [newestTurnId]);

  const handleRun = async () => {
    const submittedPrompt = prompt.trim();
    if (!submittedPrompt || activeRequest.current) return;

    const id = nextTurnId.current++;
    const controller = new AbortController();
    activeRequest.current = controller;
    const startedAt = Date.now();

    /**
     * Each implementation is fed its own answers and nobody else's. Sharing one
     * history would have each agent reading the other's reasoning as if it were
     * its own, which would destroy the comparison from the second turn onwards.
     */
    const historyFor = (agent: AgentId) =>
      turns
        .filter((turn) => turn.runs[agent].status === "complete" && turn.runs[agent].answer)
        .map((turn) => ({
          prompt: turn.prompt,
          answer: turn.runs[agent].answer,
          generation: turn.generation,
        }));

    const histories = Object.fromEntries(
      AGENT_IDS.map((agent) => [agent, historyFor(agent)]),
    ) as Record<AgentId, ReturnType<typeof historyFor>>;

    setPrompt("");
    setTurns((current) => [
      ...current,
      {
        id,
        prompt: submittedPrompt,
        generation,
        runs: Object.fromEntries(
          AGENT_IDS.map((agent) => [agent, newRun(id, submittedPrompt, generation, startedAt)]),
        ) as Record<AgentId, RunState>,
      },
    ]);

    const update = (agent: AgentId, change: (run: RunState) => RunState) => {
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id
            ? { ...turn, runs: { ...turn.runs, [agent]: change(turn.runs[agent]) } }
            : turn,
        ),
      );
    };

    /**
     * One request per implementation, in parallel. Separate connections mean one
     * agent failing or stalling leaves the other's stream intact, and the route
     * needs no multiplexing.
     */
    const runAgent = async (agent: AgentId) => {
      try {
        const response = await fetch("/api/runs", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
          body: JSON.stringify({
            prompt: submittedPrompt,
            generation,
            history: histories[agent],
            agent,
          }),
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("The agent request could not be started.");
        await readAgentStream(response, (event) => {
          update(agent, (run) => applyAgentEvent(run, event));
        });
      } catch (error) {
        if (controller.signal.aborted) return;
        update(agent, (run) => ({
          ...run,
          status: "error",
          error: error instanceof Error ? error.message : "The connection failed.",
          finishedAt: Date.now(),
        }));
      }
    };

    try {
      await Promise.all(AGENT_IDS.map(runAgent));
    } finally {
      if (activeRequest.current === controller) activeRequest.current = null;
    }
  };

  return (
    <div className="chat-page flex min-h-screen flex-col">
      <AppHeader activePage="chat" generation={generation} onGenerationChange={setGeneration} />
      <main className="chat-main mx-auto flex w-full max-w-[1200px] flex-1 flex-col px-4 sm:px-6">
        {turns.length === 0 ? (
          <div className="chat-welcome flex flex-1 flex-col items-center justify-center text-center">
            <div className="chat-mark" aria-hidden="true">P</div>
            <h2>Ask PokeAgent</h2>
            <p>Explore Pokémon, moves, matchups, and strategy.</p>
            <div className="chat-examples" aria-label="Example prompts">
              {EXAMPLE_PROMPTS.map((example) => (
                <button key={example} type="button" onClick={() => setPrompt(example)}>
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-transcript flex-1" aria-label="Conversation">
            {turns.map((turn) => (
              <ComparisonTurn key={turn.id} id={turn.id} prompt={turn.prompt} runs={turn.runs} />
            ))}
          </div>
        )}
        <div className="chat-composer-wrap sticky bottom-0">
          <PromptPanel
            prompt={prompt}
            isRunning={isRunning}
            onPromptChange={setPrompt}
            onSubmit={handleRun}
          />
          {/*
            Said plainly next to the numbers, because two panels of metrics look
            like a result. One run each is an anecdote; the distributions that
            would settle anything live in evals/.
          */}
          <p className="chat-disclaimer">
            One run per implementation. Useful for watching them work, not evidence - a
            benchmark needs many runs.
          </p>
        </div>
      </main>
    </div>
  );
}
