import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import ts from "typescript";

test("answer chunks reach the UI before the stream completes", async (t) => {
  const temporaryDirectory = await mkdtemp(join(process.cwd(), "node_modules", ".stream-test-"));
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  const source = await readFile(join(process.cwd(), "lib", "agent-stream.ts"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const modulePath = join(temporaryDirectory, "agent-stream.mjs");
  await writeFile(modulePath, compiled);
  const { readAgentStream } = await import(pathToFileURL(modulePath).href);

  let controller;
  const stream = new ReadableStream({ start(value) { controller = value; } });
  const encoder = new TextEncoder();
  const received = [];
  let resolveFirstChunk;
  const firstChunk = new Promise((resolve) => { resolveFirstChunk = resolve; });
  const reading = readAgentStream(new Response(stream), (event) => {
    received.push(event);
    if (event.type === "answer_delta") resolveFirstChunk();
  });

  controller.enqueue(encoder.encode('data: {"type":"answer_delta","message":"Try "}\n\n'));
  await Promise.race([firstChunk, reading]);
  assert.deepEqual(received, [{ type: "answer_delta", message: "Try " }]);

  controller.enqueue(encoder.encode('data: {"type":"answer","message":"Try Jolteon."}\n\ndata: {"type":"done","message":""}\n\n'));
  controller.close();
  await reading;
  assert.deepEqual(received.map((event) => event.type), ["answer_delta", "answer", "done"]);
});
