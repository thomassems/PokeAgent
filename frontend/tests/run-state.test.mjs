import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";

test("text chunks accumulate and tool use clears provisional text", async (t) => {
  const temporaryDirectory = await mkdtemp(join(process.cwd(), "node_modules", ".run-test-"));
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  const source = await readFile(join(process.cwd(), "lib", "run-state.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const modulePath = join(temporaryDirectory, "run-state.mjs");
  await writeFile(modulePath, compiled);
  const { applyAgentEvent } = await import(pathToFileURL(modulePath).href);

  const initial = {
    id: 0, prompt: "Suggest a fast Electric type", generation: 4,
    status: "running", currentActivity: "Thinking", answer: "", error: null,
    startedAt: 0, finishedAt: null,
  };
  const provisional = applyAgentEvent(initial, { type: "answer_delta", message: "Let me check." });
  assert.equal(provisional.answer, "Let me check.");
  const usingTool = applyAgentEvent(provisional, { type: "tool", message: "Using get_move" });
  assert.equal(usingTool.answer, "");
  const firstChunk = applyAgentEvent(usingTool, { type: "answer_delta", message: "Try " });
  const secondChunk = applyAgentEvent(firstChunk, { type: "answer_delta", message: "Jolteon." });
  assert.equal(secondChunk.answer, "Try Jolteon.");
  const complete = applyAgentEvent(secondChunk, { type: "answer", message: "Try Jolteon." });
  assert.equal(complete.answer, "Try Jolteon.");
});
