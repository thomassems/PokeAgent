export type AgentEvent = {
  type: "status" | "tool" | "answer_delta" | "answer" | "error" | "done";
  message: string;
};

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
    typeof value.message !== "string" ||
    !["status", "tool", "answer_delta", "answer", "error", "done"].includes(String(value.type))
  ) {
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
