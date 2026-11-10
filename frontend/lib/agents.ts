/**
 * The two implementations the app compares. Labelled by implementation rather
 * than by vendor, because that is what is being compared: a hand-written loop
 * against the same loop handed to a framework.
 */
export const AGENTS = [
  { id: "custom", label: "Custom loop" },
  { id: "langchain", label: "LangChain" },
] as const;

export type AgentId = (typeof AGENTS)[number]["id"];

export const AGENT_IDS: readonly AgentId[] = AGENTS.map((agent) => agent.id);
