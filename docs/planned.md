# Planned work

**Nothing on this page is built.** Every directory, tool, and eval layer below is
design that has been agreed and written down, not shipped behaviour. No file
described here exists yet.

This page holds the detail so the architecture section in `CLAUDE.md` can stay
short. For what the code actually does today, read `CLAUDE.md` and the code.

Decisions already taken and their rejected alternatives live in
`docs/decisions.md`; this page is the forward-looking counterpart.

## Tools

### `llm/tools/` - model-facing tool registry

Every tool the agent can invoke is registered here, and only here. Each entry
is a thin wrapper: a schema describing the tool to the model, plus a call into
the layer that does the actual work. No business logic lives in this
directory.

Three tools are planned:

1. **Web search** - current metagame information: trending sets, recent tier
   shifts, forum discussion. Backed by `services/`. Exists because indexed
   data goes stale as the meta moves.

2. **Vector search over strategy prose** - set descriptions and written
   analysis explaining why a Pokémon runs a given item, spread or moveset,
   and what it counters. Answers semantic queries that stats cannot, e.g.
   "something bulky for rain." Backed by `services/`. Does **not** index stat
   tables.

3. **Stats lookup** - exact factual data: base stats, typing, abilities,
   movepools, type matchups. Backed by `tools/`, and therefore pure.

The split that matters: exact facts come from structured data, fuzzy
strategic advice comes from vector search. Routing is not hardcoded - the
model selects a tool from its description, so those descriptions are load-
bearing and should be written with care.

Purity is not uniform across this directory, and that is deliberate. Tool 3
is deterministic end to end and unit-testable with no mocking. Tools 1 and 2
cross the network and are mocked in tests. The registry hides this from the
model; it does not hide it from the test suite.

Stats lookup stays pure because base stats and type charts are static game
data, loaded from `data/` at startup. If it ever becomes a live database
query it moves to `services/` and wraps from there - do not "optimise" it
into a DB call while leaving it in `tools/`.

### Queries the tools have to support

Tool shapes are driven by the questions the agent actually gets asked. Three
representative ones, none of them a single-entity lookup:

- **"What is my team missing?"** Needs every team member's typing at once, and
  a defensive profile for each.

- **"Should my Garchomp learn Stone Edge?"** Needs the Pokemon record and the
  move record together, then a judgement about whether that move's type reaches
  anything the rest of the set does not already cover.

- **"I have this team and just ran into a Weavile. Worth swapping anything
  out?"** The wild encounter case. Needs six team records plus the candidate,
  compared in a single reasoning step: what the swap gains offensively against
  what it gives up defensively.

- **"Help me draft a team to beat Cynthia."** The hardest of the five, because
  none of the constraints are stated. Who Cynthia is and what she runs is web
  search, not the dex. The answer then has to be turned into a generation, and
  that is genuinely ambiguous: she is the Sinnoh Champion in Gen 4 and returns
  with a different team in Gen 5. Only once the generation is pinned does the
  dex become usable, because every candidate has to be legal in it. A team that
  counters her perfectly but names a Pokemon that did not exist yet is still a
  wrong answer.

- **"Build me a team of legendaries."** or "what is the best mythical". The dex
  stores name, typing, stats and moves. It has no field for *legendary* or
  *mythical*, so no amount of querying resolves the term. The data even
  contains Heatran and Zapdos without recording that either is legendary. The
  agent has to recognise the word as one its structured data does not encode,
  use search to find which Pokemon the category covers, then return to the dex
  for their stats.

Every one of these touches several Pokemon or several moves at once. That is
why the lookups take lists rather than single names. A seven Pokemon comparison
should not cost seven round trips, and step count is one of the things this
project exists to measure.

The Cynthia case adds a second requirement on top: constraints are frequently
implied rather than given. The agent has to infer a generation from a web
search result and then carry it through every subsequent dex call. Generation
is not a parameter the user supplies here, it is a conclusion the agent has to
reach and then respect.

The legendary case adds a third: the agent has to know where its own data stops.
Tiers, competitive formats, "legendary", "mythical", "pseudo-legendary",
"starter", anything about the current metagame - none of it is in the dex, and
the stats lookup cannot say so, because it can only report what it has.

The failure to design against is silent substitution. Asked for legendaries,
the model has every incentive to return six Pokemon with high base stat totals
and present them as the answer. Base stat total does correlate with the
category, nothing in the dex contradicts the choice, and the result reads as
confident and well reasoned. It is still wrong, and no amount of checking the
output text against the dex will catch it, because the dex was never asked the
question.

Terms the dex does not encode route to search. They do not route to whichever
field happens to correlate.

## Eval suite

**Planned, not built.** The scoring logic is on the do-not-implement list in
`CLAUDE.md` - it is a learning surface, so it gets written by hand.

The suite runs after any prompt change. Prompts break silently: a reworded
system message can degrade tool selection without raising an error, failing a
type check, or producing output that looks obviously wrong. Nothing else in the
repo catches that.

Three layers, in increasing order of how hard they are to trust.

### 1. Retrieval accuracy - deterministic

Fixed questions with known ground truth - base stats, type matchups - asserted
on exact values. Type math has exactly right answers, so these assertions are
exact rather than fuzzy.

Catches hallucination and retrieval regressions.

### 2. Tool selection - deterministic

Given a set of inputs, assert the agent called the expected tool. A stats
question should reach the structured lookup, not web search.

Checked by inspecting the tool call, not the output text. An agent can produce a
correct-looking answer through the wrong tool - answering a base-stat question
from web search prose, say - and only the call record exposes it. Grading the
text would score that as a pass.

### 3. Team quality - model-judged

Assert the generated team is coherent: broad type coverage, no glaring shared
weaknesses, and respect for any constraints the user gave. Scored by a separate
model against a written rubric, because there is no single correct answer.

Being model-judged makes this the least trustworthy layer, which is why it is
last. The existing rule in `CLAUDE.md` applies with most force here: report
distributions over N runs, never a single-run comparison.

> **Open:** "broad type coverage" needs qualifying before the rubric is written.
> The glossary in `CLAUDE.md` forbids saying *coverage* unqualified - it has to
> be defensive coverage, offensive coverage, or both scored separately. Left
> undecided rather than guessed.

### Failures become cases

Any failure seen in real use gets added to the suite as a new case. This is the
same rule `CLAUDE.md` already applies to bugs - a regression test comes first -
extended to agent behaviour, where "reproduce it" means pinning the input rather
than writing a unit test.

The suite is therefore expected to grow from use, not to be written once and
finished.
