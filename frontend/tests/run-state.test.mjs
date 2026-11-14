import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";

/**
 * run-state.ts imports its sibling, so compiling one file is not enough. Each
 * named module is transpiled into the same directory and its relative imports
 * are pointed at the .mjs that lands beside it.
 */
async function compileLib(directory, names) {
  for (const name of names) {
    const source = await readFile(join(process.cwd(), "lib", `${name}.ts`), "utf8");
    const compiled = ts
      .transpileModule(source, {
        compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
      })
      .outputText.replace(/from "\.\/([\w-]+)"/g, 'from "./$1.mjs"');
    await writeFile(join(directory, `${name}.mjs`), compiled);
  }
}

test("text chunks accumulate and tool use clears provisional text", async (t) => {
  const temporaryDirectory = await mkdtemp(join(process.cwd(), "node_modules", ".run-test-"));
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  await compileLib(temporaryDirectory, ["activity", "run-state"]);
  const modulePath = join(temporaryDirectory, "run-state.mjs");
  const { applyAgentEvent } = await import(pathToFileURL(modulePath).href);

  const initial = {
    id: 0, prompt: "Suggest a fast Electric type", generation: 4,
    status: "running", currentActivity: "Thinking", currentStep: null, answer: "", error: null,
    startedAt: 0, finishedAt: null,
  };
  const provisional = applyAgentEvent(initial, { type: "answer_delta", message: "Let me check." });
  assert.equal(provisional.answer, "Let me check.");
  const usingTool = applyAgentEvent(provisional, { type: "tool", message: "Using get_move" });
  assert.equal(usingTool.answer, "");
  assert.equal(usingTool.currentActivity, "Looking up a move");

  // A tool that has returned is not a tool still running: the model is next.
  const toolDone = applyAgentEvent(usingTool, { type: "tool", message: "get_move returned" });
  assert.equal(toolDone.currentActivity, "Thinking");

  const stepped = applyAgentEvent(toolDone, { type: "status", message: "Step 3 of 8" });
  assert.equal(stepped.currentActivity, "Thinking");
  assert.equal(stepped.currentStep, "step 3 of 8");
  const firstChunk = applyAgentEvent(usingTool, { type: "answer_delta", message: "Try " });
  const secondChunk = applyAgentEvent(firstChunk, { type: "answer_delta", message: "Jolteon." });
  assert.equal(secondChunk.answer, "Try Jolteon.");
  const complete = applyAgentEvent(secondChunk, { type: "answer", message: "Try Jolteon." });
  assert.equal(complete.answer, "Try Jolteon.");
});
