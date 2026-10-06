"use client";

import { useEffect, useRef, useState } from "react";
import { AgentRunPanel } from "@/components/AgentRunPanel";
import { AppHeader } from "@/components/AppHeader";
import { PromptPanel } from "@/components/PromptPanel";
import { readAgentStream } from "@/lib/agent-stream";
import { applyAgentEvent, type RunState } from "@/lib/run-state";
import type { Generation } from "@/lib/types";

const EXAMPLE_PROMPTS = [
  "What makes a good fast Electric type?",
  "What does Body Slam do?",
  "How did Steel resist Ghost in Generation 4?",
];

export default function Home() {
  const [generation, setGeneration] = useState<Generation>(4);
  const [prompt, setPrompt] = useState("");
  const [runs, setRuns] = useState<RunState[]>([]);
  const activeRequest = useRef<AbortController | null>(null);
  const nextRunId = useRef(0);
  const newestRunId = runs.at(-1)?.id;
  const isRunning = runs.some((run) => run.status === "running");

  useEffect(() => () => activeRequest.current?.abort(), []);
  useEffect(() => {
    if (newestRunId !== undefined) {
      document.getElementById(`chat-turn-${newestRunId}`)?.scrollIntoView({ block: "start" });
    }
  }, [newestRunId]);

  const handleRun = async () => {
    const submittedPrompt = prompt.trim();
    if (!submittedPrompt || activeRequest.current) return;

    const id = nextRunId.current++;
    const controller = new AbortController();
    activeRequest.current = controller;
    const history = runs
      .filter((run) => run.status === "complete" && run.answer)
      .map(({ prompt, answer, generation }) => ({ prompt, answer, generation }));
    setPrompt("");
    setRuns((current) => [...current, {
      id,
      prompt: submittedPrompt,
      generation,
      status: "running",
      currentActivity: "Thinking…",
      answer: "",
      error: null,
      startedAt: Date.now(),
      finishedAt: null,
    }]);

    try {
      const response = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ prompt: submittedPrompt, generation, history }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("The agent request could not be started.");
      await readAgentStream(response, (event) => {
        setRuns((current) => current.map((run) => run.id === id ? applyAgentEvent(run, event) : run));
      });
    } catch (error) {
      if (controller.signal.aborted) return;
      setRuns((current) => current.map((run) => run.id === id ? {
        ...run,
        status: "error",
        error: error instanceof Error ? error.message : "The connection failed.",
        finishedAt: Date.now(),
      } : run));
    } finally {
      if (activeRequest.current === controller) activeRequest.current = null;
    }
  };

  return (
    <div className="chat-page flex min-h-screen flex-col">
      <AppHeader activePage="chat" generation={generation} onGenerationChange={setGeneration} />
      <main className="chat-main mx-auto flex w-full max-w-[900px] flex-1 flex-col px-4 sm:px-6">
        {runs.length === 0 ? (
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
            {runs.map((run) => <AgentRunPanel key={run.id} {...run} />)}
          </div>
        )}
        <div className="chat-composer-wrap sticky bottom-0">
          <PromptPanel
            prompt={prompt}
            isRunning={isRunning}
            onPromptChange={setPrompt}
            onSubmit={handleRun}
          />
        </div>
      </main>
    </div>
  );
}
