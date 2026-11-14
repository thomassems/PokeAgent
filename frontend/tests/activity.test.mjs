import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";

async function loadActivity(directory) {
  const source = await readFile(join(process.cwd(), "lib", "activity.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const modulePath = join(directory, "activity.mjs");
  await writeFile(modulePath, compiled);
  return import(pathToFileURL(modulePath).href);
}

test("tool events read as what the agent is doing", async (t) => {
  const directory = await mkdtemp(join(process.cwd(), "node_modules", ".activity-test-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const { toolActivity, stepLabel } = await loadActivity(directory);

  assert.equal(toolActivity("Using web_search"), "Searching the web");
  assert.equal(toolActivity("Using get_type_matchups"), "Checking type matchups");

  // The returned half of the pair means the model is about to run again.
  assert.equal(toolActivity("web_search returned"), "Thinking");

  // A tool added to the registry without a label still names itself.
  assert.equal(toolActivity("Using count_berries"), "count_berries");

  assert.equal(stepLabel("Step 3 of 8"), "step 3 of 8");
  assert.equal(stepLabel("Reticulating splines"), null);
});
