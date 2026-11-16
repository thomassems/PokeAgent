import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";

async function loadAccent(directory) {
  const source = await readFile(join(process.cwd(), "lib", "go-accent.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const modulePath = join(directory, "go-accent.mjs");
  await writeFile(modulePath, compiled);
  return import(pathToFileURL(modulePath).href);
}

test("a missing or unknown accent stays neutral", async (t) => {
  const directory = await mkdtemp(join(process.cwd(), "node_modules", ".accent-test-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const { parseStoredAccent } = await loadAccent(directory);

  assert.equal(parseStoredAccent(null), "neutral");
  assert.equal(parseStoredAccent(""), "neutral");
  assert.equal(parseStoredAccent("mystic"), "neutral");
  assert.equal(parseStoredAccent("neutral"), "neutral");
  assert.equal(parseStoredAccent("blue"), "blue");
  assert.equal(parseStoredAccent("red"), "red");
  assert.equal(parseStoredAccent("yellow"), "yellow");
});
