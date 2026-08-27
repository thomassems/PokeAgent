# CLAUDE.md

## What this project is

A benchmark disguised as a Pokemon team builder. Two agent implementations - one
hand-rolled, one built on LangChain - solve the same open-ended team-building
problems against the same tools, and the app streams both traces side by side so
they can be compared on outcome quality, step count, latency, and cost.

Stack: Next.js (TypeScript) frontend, FastAPI (Python 3.12) backend, both
deployed on Vercel from one repo. Dex data is baked at build time; no runtime
calls to PokeAPI.

## The one rule that overrides the others

**This is a learning project. Comprehension beats velocity.**

The point is for me to understand agent internals by building them. Code I did
not write and cannot explain is worse than no code. If a choice is between
finishing faster and me understanding what happened, choose understanding.

I would rather receive a clear explanation and write the code myself than
receive working code I have to reverse-engineer.

## About me

<!-- Fill this in and keep it current. It calibrates how much gets explained. -->

- Comfortable with: React, TypeScript, general web development.
- Rusty on: Python. Assume I know the language but have forgotten idioms and
  standard library details. Do not explain what a list comprehension is; do
  remind me how `asyncio` gather semantics work.
- New to: agent frameworks, LangChain, LangGraph, evals, prompt injection.
  Explain these concepts before using their vocabulary.
- I want to understand *why* a pattern exists, not just that it is conventional.

## Confirm before deciding

**Any design decision or change to agent behavior requires my explicit
confirmation before implementation.** Notify me, explain the options, wait for a
yes. This includes:

- Anything that changes how either agent reasons, loops, or terminates
- Adding, removing, or changing the signature of a tool
- Changes to the trace event schema
- Changes to the shared agent protocol
- Changes to prompts or system messages
- Anything affecting the architecture boundaries below
- Anything that would make the two agents behave differently from each other

Do not treat a change as "obviously correct" and skip this. If you think it is
obvious, say so in the proposal and I will approve it quickly.

## Do not implement these

These are the learning surfaces:

- The custom agent loop (`agents/custom.py`)
- The tool-schema generator (function signature to JSON Schema)
- The input guard, output guard, and query rewrite stages
- The eval scoring logic

If I ask you to write one of these, **ask once** whether I want to skip the
exercise and remind me why it is on the list. If I confirm, go ahead - it is my
call. Do not refuse, and do not ask twice.

You may always: review my implementation, point out bugs, write tests against
it, explain the concept, sketch a signature or type, or describe an approach in
prose.

Everything else - glue code, config, frontend components, the data fetch script,
CI - is fair game, subject to the rules below.

## Working agreement

- **Propose before building.** Anything touching more than two files or adding
  more than ~50 lines gets a plan first: what changes, why, what alternatives
  were rejected.
- **One thing at a time.** Do not bundle a refactor into a feature. Do not fix
  unrelated things you notice - mention them and move on.
- **No new dependencies without asking.** Name the package, what it replaces,
  and what it costs.
- **Explain tradeoffs, do not silently pick.**
- **Say when you are unsure.** A flagged guess is useful; a confident wrong
  answer costs me an afternoon.
- **Never commit, push, or open a PR unless I explicitly ask.**
- **Do not touch `.env`, `uv.lock`, or `package-lock.json` without saying so.**

## Verify, do not recall

Framework APIs in this stack changed recently and training data is full of the
old versions.

- **Check current docs before writing LangChain or LangGraph code.** LangChain
  1.0 reorganized around `create_agent` and middleware; pre-1.0 patterns
  (`AgentExecutor`, `initialize_agent`, chain-based composition) are wrong here
  even though they look plausible and may still import.
- Same applies to the Vercel AI SDK, Next.js App Router APIs, and DeepSeek's
  API surface.
- If you are writing framework code from memory, say so, so I know to check it.
- Cite the doc page when the answer came from one.

## Model provider

Likely DeepSeek (OpenAI-API-compatible - use the `openai` SDK with a custom
`base_url`). Not final.

- **Keep the provider behind a thin adapter.** Swapping providers must be a
  config change, not a rewrite. No provider-specific types leak into `agents/`.
- Both agents use the same model, temperature, and settings. A difference here
  invalidates the comparison.
- Tool-calling reliability is the project's main external risk. A smoke test
  that exercises multi-step tool calling belongs in the first week, not the
  last.
- Assume tools will sometimes fail and the agent must recover. This is the
  weakest area of every current model, so error paths deserve real tests.

## Architecture

Dependencies point inward. Outer layers may import inner ones; never the reverse.

```
api/  ->  agents/  ->  tools/  ->  data/
```

- `data/` - baked Gen 4 JSON plus the one-time fetch script. No logic.
- `tools/` - pure functions over `data/`. Type effectiveness, coverage gaps,
  candidate search. **No LLM client, no network, no I/O, no async.**
  Deterministic and fully unit-testable. This is the most important boundary in
  the repo; if something in `tools/` needs to call a model, the design is wrong.
- `agents/` - the two implementations plus the shared protocol they satisfy.
  Agents call tools. Agents never touch HTTP or FastAPI types.
- `api/` - FastAPI routes, SSE streaming, request/response models. Thin.

Both agents implement the same interface. If a change makes them diverge in
signature, stop and flag it - that breaks the comparison.

- No file over 300 lines.
- Pydantic models for every boundary crossing. No bare dicts across layers.
- Trace event schema defined once, in one place, emitted by both agents.
- Type hints on every Python signature. `strict` mode in TypeScript.

## Anti-patterns to avoid

Named so I can point at them in review:

- **Silent failure.** `try/except` that catches, logs nothing, and returns
  `None`. If it can fail, either handle it meaningfully or let it raise.
- **Abstraction before the second case.** No base classes, factories, or
  strategy patterns for something with one implementation. The agent protocol
  is the deliberate exception - it has exactly two.
- **Config for constants.** If a value has never changed and has no reason to,
  it is a constant, not a setting.
- **Parameter creep.** More than three or four parameters means the function is
  doing too much or wants a dataclass.
- **Defensive noise.** Do not add validation, retries, or error handling I did
  not ask for. Propose it; do not smuggle it in.
- **Comments restating code.** Comments explain *why*.
- **Premature optimization.** Caching and memoization only after something is
  measurably slow.

## Security

- **All model calls happen server-side.** No API key reaches the browser, not
  even via a build-time env var. If a change would expose one, refuse and say
  why.
- **Treat the user prompt as untrusted.** It reaches an LLM that can call tools.
  The input guard is not decoration.
- **Tools do not take free-form strings that become queries or paths.**
  Constrained enums and typed filters only. No dynamic imports, no `eval`, no
  shelling out from a tool.
- **Every agent run has hard caps** - max iterations, max tool calls, max
  tokens, wall-clock timeout - enforced in code, not in the prompt.
- **Errors returned to the client are sanitized.** Stack traces, file paths, and
  raw provider errors stay in the logs.
- **Rate limiting and a spend cap ship before the first public deploy.**
- **Secrets live in `.env.local`, gitignored.** `.env.example` holds key names
  only. If you see a real key in a file you are editing, stop and tell me.
- Flag any dependency that wants network or filesystem access at import time.

## Domain glossary

Use these precisely. Drift here causes real bugs.

- **Defensive coverage** - what the team resists or is immune to.
- **Offensive coverage** - what the team can hit super-effectively.
  Never say "coverage" unqualified.
- **Gap** - a type that nothing on the team resists (defensive) or nothing hits
  super-effectively (offensive). Always specify which.
- **STAB** - same-type attack bonus; a move matching the user's own type.
- **Speed tier** - a base speed threshold that determines who moves first.
- **Slot** - one of the six team positions.
- **Candidate** - a Pokemon under consideration for a slot, not yet added.
- **Run** - one agent execution from prompt to final answer.
- **Step** - one iteration of an agent's loop.
- Scope is **Generation 4 only**. If something references another generation,
  that is a bug.

## Out of scope

Not building these. If a change starts heading toward one, stop and say so.

- User accounts, auth, or login
- A database (team state lives in the URL)
- Generations other than 4
- Battle simulation or damage calculation
- Multiplayer, sharing feeds, or social features
- Mobile apps
- Anything commercial: no ads, no payments, no monetization

## Testing

- `tools/` gets real unit tests with known-correct fixtures. Type math has exact
  right answers; no excuse for untested code here.
- Agent runs are not unit tests. They are slow and nondeterministic. They live
  in `evals/` and run on demand.
- Evals report distributions over N runs, never single-run comparisons. One
  head-to-head between two agents is anecdote, not evidence.
- Any bug we fix gets a regression test first.

## Conventions

- Python: `uv`, `ruff` for lint and format, `pytest`. Version pinned in
  `.python-version`.
- TypeScript: strict mode, no `any` without a comment explaining why.
- Names say what things are. `find_candidates`, not `helper` or `process`.
- Sentence-case commit messages, imperative mood, one logical change each.

## Decision log

Real architectural choices get a paragraph in `docs/decisions.md`: what was
decided, what was rejected, and why. When you propose something and I approve
it, remind me to log it.

## Definition of done

Tests where tests apply, no new lint errors, no unapproved dependencies, and I
can explain out loud what it does and why it is structured that way.