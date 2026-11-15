import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";

async function loadGame(directory) {
  const source = await readFile(join(process.cwd(), "lib", "game.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const modulePath = join(directory, "game.mjs");
  await writeFile(modulePath, compiled);
  return import(pathToFileURL(modulePath).href);
}

test("a missing or unknown game stays on the main series", async (t) => {
  const directory = await mkdtemp(join(process.cwd(), "node_modules", ".game-test-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const { parseStoredGame } = await loadGame(directory);

  assert.equal(parseStoredGame(null), "main");
  assert.equal(parseStoredGame(""), "main");
  assert.equal(parseStoredGame("main"), "main");
  assert.equal(parseStoredGame("tcg"), "main");
  assert.equal(parseStoredGame("go"), "go");
});
