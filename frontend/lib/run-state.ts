import { stepLabel, THINKING, toolActivity } from "./activity";
import type { AgentEvent, RunMetrics } from "./agent-stream";
import type { Generation } from "./types";

export type RunState = {
  id: number;
  prompt: string;
  generation: Generation;
  status: "running" | "complete" | "error";
  currentActivity: string;
  /** "step 3 of 8", shown beside the activity. Null until the first step. */
  currentStep: string | null;
  answer: string;
  error: string | null;
  startedAt: number;
  finishedAt: number | null;
  /** Null until the run reports, which it does once, just after the answer. */
  metrics: RunMetrics | null;
};

export function applyAgentEvent(run: RunState, event: AgentEvent): RunState {
  if (event.type === "status") {
    return {
      ...run,
      currentActivity: THINKING,
      currentStep: stepLabel(event.message) ?? run.currentStep,
    };
  }
  if (event.type === "tool") {
    return { ...run, currentActivity: toolActivity(event.message), answer: "" };
  }
  if (event.type === "answer_delta") {
    return { ...run, currentActivity: "Writing answer", answer: run.answer + event.message };
  }
  if (event.type === "answer") return { ...run, answer: event.message };
  if (event.type === "metrics") return { ...run, metrics: event.metrics };
  if (event.type === "error") {
    return { ...run, status: "error", error: event.message, finishedAt: Date.now() };
  }
  return { ...run, status: "complete", finishedAt: Date.now() };
}

export function newRun(
  id: number,
  prompt: string,
  generation: Generation,
  startedAt: number,
): RunState {
  return {
    id,
    prompt,
    generation,
    status: "running",
    currentActivity: THINKING,
    currentStep: null,
    answer: "",
    error: null,
    startedAt,
    finishedAt: null,
    metrics: null,
  };
}
