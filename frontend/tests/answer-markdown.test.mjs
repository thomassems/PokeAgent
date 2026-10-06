import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

test("agent answers render Markdown as headings, emphasis, and lists", async (t) => {
  const temporaryDirectory = await mkdtemp(join(process.cwd(), "node_modules", ".answer-test-"));
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));

  const source = await readFile(join(process.cwd(), "components", "AgentRunPanel.tsx"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const modulePath = join(temporaryDirectory, "AgentRunPanel.mjs");
  await writeFile(modulePath, compiled);
  const { AgentRunPanel } = await import(pathToFileURL(modulePath).href);

  const answer = "Assuming you mean **Lickilicky**.\n\n## The moveset\n\n**Bulky attacker**\n- Body Slam (STAB)\n- Earthquake\n\n<script>alert(1)</script>\n\n![tracking](https://example.com/pixel)";
  const html = renderToStaticMarkup(createElement(AgentRunPanel, {
    id: 0,
    prompt: "Tell me about Lickilicky",
    status: "complete",
    currentActivity: "",
    answer,
    error: null,
    startedAt: 0,
    finishedAt: 1000,
  }));

  assert.match(html, /<strong>Lickilicky<\/strong>/);
  assert.match(html, /<h2>The moveset<\/h2>/);
  assert.match(html, /<li>Body Slam \(STAB\)<\/li>/);
  assert.doesNotMatch(html, /## The moveset|\*\*Bulky attacker\*\*/);
  assert.doesNotMatch(html, /<script|<img/);
});

test("a streaming answer places activity below the text without another bubble", async (t) => {
  const temporaryDirectory = await mkdtemp(join(process.cwd(), "node_modules", ".activity-test-"));
  t.after(() => rm(temporaryDirectory, { recursive: true, force: true }));
  const source = await readFile(join(process.cwd(), "components", "AgentRunPanel.tsx"), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const modulePath = join(temporaryDirectory, "AgentRunPanel.mjs");
  await writeFile(modulePath, compiled);
  const { AgentRunPanel } = await import(pathToFileURL(modulePath).href);
  const html = renderToStaticMarkup(createElement(AgentRunPanel, {
    id: 0, prompt: "Suggest a team", status: "running", currentActivity: "Writing answer",
    answer: "Try **Jolteon**.", error: null, startedAt: 0, finishedAt: null,
  }));

  assert.ok(html.indexOf('class="chat-answer"') < html.indexOf('class="chat-activity"'));
  assert.doesNotMatch(html, /chat-loading-bubble/);
  assert.match(html, /chat-activity-dot/);
});
