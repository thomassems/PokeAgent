"use client";

import { useEffect, useRef, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { ComparisonTurn } from "@/components/ComparisonTurn";
import { PromptPanel } from "@/components/PromptPanel";
import { AGENT_IDS, type AgentId } from "@/lib/agents";
import { readAgentStream } from "@/lib/agent-stream";
import { useSharedGame, type Game } from "@/lib/game";
import { useSharedGeneration } from "@/lib/generation";
import { applyAgentEvent, newRun, type RunState } from "@/lib/run-state";
import type { Generation } from "@/lib/types";

const EXAMPLE_PROMPTS = [
  "What makes a good fast Electric type?",
  "What does Body Slam do?",
  "How did Steel resist Ghost in Generation 4?",
];

const GO_EXAMPLE_PROMPTS = [
  "What raid bosses are in Pokemon GO right now?",
  "When is the next Community Day?",
  "What is this week's Spotlight Hour?",
];

/** One question, answered by every implementation. */
type Turn = {
  id: number;
  prompt: string;
  generation: Generation | null;
  game: Game;
  runs: Record<AgentId, RunState>;
};

export default function Home() {
  const [generation, setGeneration] = useSharedGeneration();
  const [game, setGame] = useSharedGame();
  const examples = game === "go" ? GO_EXAMPLE_PROMPTS : EXAMPLE_PROMPTS;
  const [prompt, setPrompt] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const activeRequest = useRef<AbortController | null>(null);
  const nextTurnId = useRef(0);
  // True while the reader is parked at the bottom. A running answer grows
  // downward; following it keeps the new lines above the sticky composer.
  // Scrolling up to read an earlier turn opts out until they return.
  const followStream = useRef(true);
  const scrollingSelf = useRef(false);
  const newestTurnId = turns.at(-1)?.id;
  const isRunning = turns.some((turn) =>
    AGENT_IDS.some((agent) => turn.runs[agent].status === "running"),
  );

  useEffect(() => () => activeRequest.current?.abort(), []);
  useEffect(() => {
    const onScroll = () => {
      if (scrollingSelf.current) return;
      const distance =
        document.documentElement.scrollHeight - window.scrollY - window.innerHeight;
      followStream.current = distance < 180;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  useEffect(() => {
    if (newestTurnId === undefined || !followStream.current) return;
    const running = turns.some(
      (turn) =>
        turn.id === newestTurnId &&
        AGENT_IDS.some((agent) => turn.runs[agent].status === "running"),
    );
    if (!running) return;
    const turn = document.getElementById(`chat-turn-${newestTurnId}`);
    if (!turn) return;
    scrollingSelf.current = true;
    turn.scrollIntoView({ block: "end" });
    requestAnimationFrame(() => {
      scrollingSelf.current = false;
    });
  }, [newestTurnId, turns]);

  const handleRun = async () => {
    const submittedPrompt = prompt.trim();
    if (!submittedPrompt || activeRequest.current) return;

    const id = nextTurnId.current++;
    const controller = new AbortController();
    activeRequest.current = controller;
    followStream.current = true;
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
          game: turn.game,
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
        game,
        runs: Object.fromEntries(
          AGENT_IDS.map((agent) => [
            agent,
            newRun(id, submittedPrompt, generation, game, startedAt),
          ]),
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
            game,
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
      <AppHeader activePage="chat" />
      <main className="chat-main mx-auto flex w-full max-w-[1200px] flex-1 flex-col px-4 sm:px-6">
        {turns.length === 0 ? (
          <div className="chat-welcome flex flex-1 flex-col items-center justify-center text-center">
            <div className="chat-mark" aria-hidden="true">P</div>
            <h2>Ask PokeAgent</h2>
            <p>
              {game === "go"
                ? "Raids, events, and what is happening in Pokémon GO."
                : "Explore Pokémon, moves, matchups, and strategy."}
            </p>
            {game === "go" && (
              <p>Event data from LeekDuck, via ScrapedDuck.</p>
            )}
            <div className="chat-examples" aria-label="Example prompts">
              {examples.map((example) => (
                <button key={example} type="button" onClick={() => setPrompt(example)}>
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-transcript flex-1" aria-label="Conversation">
            {turns.map((turn) => (
              <ComparisonTurn
                key={turn.id}
                id={turn.id}
                prompt={turn.prompt}
                game={turn.game}
                runs={turn.runs}
              />
            ))}
          </div>
        )}
        <div className="chat-composer-wrap sticky bottom-0">
            <PromptPanel
            prompt={prompt}
            isRunning={isRunning}
            game={game}
            generation={generation}
            onGameChange={setGame}
            onGenerationChange={setGeneration}
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
