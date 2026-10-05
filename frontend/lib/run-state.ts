import type { AgentEvent } from "./agent-stream";
import type { Generation } from "./types";

export type RunState = {
  id: number;
  prompt: string;
  generation: Generation;
  status: "running" | "complete" | "error";
  currentActivity: string;
  answer: string;
  error: string | null;
  startedAt: number;
  finishedAt: number | null;
};

export function applyAgentEvent(run: RunState, event: AgentEvent): RunState {
  if (event.type === "status") return { ...run, currentActivity: event.message };
  if (event.type === "tool") {
    return { ...run, currentActivity: event.message, answer: "" };
  }
  if (event.type === "answer_delta") {
    return { ...run, currentActivity: "Writing answer", answer: run.answer + event.message };
  }
  if (event.type === "answer") return { ...run, answer: event.message };
  if (event.type === "error") {
    return { ...run, status: "error", error: event.message, finishedAt: Date.now() };
  }
  return { ...run, status: "complete", finishedAt: Date.now() };
}
