export type RunMetrics = {
  steps: number;
  toolCalls: number;
  inputTokens: number;
  outputTokens: number;
};

export type AgentEvent =
  | {
      type: "status" | "tool" | "answer_delta" | "answer" | "error" | "done";
      message: string;
    }
  | { type: "metrics"; message: string; metrics: RunMetrics };

const PLAIN_TYPES = ["status", "tool", "answer_delta", "answer", "error", "done"];

function isTokenCount(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

/**
 * The server sends metrics in its own snake_case. Renaming happens here, at the
 * one place the wire format is read, so nothing downstream has to know about it.
 */
function parseMetrics(value: unknown): RunMetrics {
  if (typeof value !== "object" || value === null) {
    throw new Error("The server sent an invalid agent event.");
  }
  const raw = value as Record<string, unknown>;
  if (
    !isTokenCount(raw.steps) ||
    !isTokenCount(raw.tool_calls) ||
    !isTokenCount(raw.input_tokens) ||
    !isTokenCount(raw.output_tokens)
  ) {
    throw new Error("The server sent an invalid agent event.");
  }
  return {
    steps: raw.steps,
    toolCalls: raw.tool_calls,
    inputTokens: raw.input_tokens,
    outputTokens: raw.output_tokens,
  };
}

function parseFrame(frame: string): AgentEvent | null {
  const data = frame
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart())
    .join("\n");
  if (!data) return null;

  const value: unknown = JSON.parse(data);
  if (
    typeof value !== "object" ||
    value === null ||
    !("type" in value) ||
    !("message" in value) ||
    typeof value.message !== "string"
  ) {
    throw new Error("The server sent an invalid agent event.");
  }

  if (value.type === "metrics") {
    const metrics = parseMetrics("metrics" in value ? value.metrics : null);
    return { type: "metrics", message: value.message, metrics };
  }
  if (!PLAIN_TYPES.includes(String(value.type))) {
    throw new Error("The server sent an invalid agent event.");
  }
  return value as AgentEvent;
}

export async function readAgentStream(
  response: Response,
  onEvent: (event: AgentEvent) => void,
): Promise<void> {
  if (!response.body) throw new Error("The server did not send a stream.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let ended = false;

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      buffer = buffer.replace(/\r\n/g, "\n");

      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const event = parseFrame(buffer.slice(0, boundary));
        buffer = buffer.slice(boundary + 2);
        if (event) {
          onEvent(event);
          if (event.type === "done" || event.type === "error") ended = true;
        }
        boundary = buffer.indexOf("\n\n");
      }
    }
  } finally {
    reader.releaseLock();
  }

  if (!ended) throw new Error("The connection ended before the run finished.");
}
