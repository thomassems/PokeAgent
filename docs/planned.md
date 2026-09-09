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

Tool shapes are driven by the questions the agent actually gets asked. Five
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

- **"Build me a team of legendaries."** The dex now carries `is_legendary` and
  `is_mythical` per species, straight from PokeAPI, so this is a filter rather
  than a research question. It stays on this list because the same shape of
  question still exists for categories the dex does *not* encode: tiers,
  competitive formats, "pseudo-legendary", "starter". Those still route to
  search. The point is that the agent has to know which side of that line a term
  falls on.

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
Legendary and mythical are now fields in the dex, but tiers, competitive
formats, "pseudo-legendary", "starter" and anything about the current metagame
are not, and the stats lookup cannot report that they are missing. It can only
return what it has.

The failure to design against is silent substitution. Asked for a category the
dex does not hold, the model has every incentive to return six Pokemon with high
base stat totals and present them as the answer. Base stat total correlates with
most of these categories, nothing in the dex contradicts the choice, and the
result reads as confident and well reasoned. It is still wrong, and no amount of
checking the output text against the dex will catch it, because the dex was
never asked the question.

Terms the dex does not encode route to search. They do not route to whichever
field happens to correlate.

### Offensive coverage comes from moves, not typing

A defensive profile follows from a Pokemon's typing. An offensive one does not.

Garchomp is Dragon/Ground. Computed from typing it looks unable to touch Steel,
but it runs Fire Blast, so it hits Steel for 2x. Offensive coverage comes from
moves, not from what the Pokemon is. A types-based attacking profile only ever
shows STAB, and it will report offensive gaps the team does not actually have.

That matters because the glossary in `CLAUDE.md` defines offensive coverage as
what the team can hit super-effectively, which is a statement about movesets.

So the attacking direction of a matchup tool has to read each Pokemon's
damaging moves and use their types, not the Pokemon's own. Both halves of that
are already in `data/`: `POKEMON[id]["moves"]` gives the move ids and
`MOVES[id]["type"]` gives their types. Status moves are filtered out, since
Swords Dance covers nothing.

If a tool computes the attacking direction from typing alone, it should be
named for what it actually returns. Calling STAB-only output "offensive
coverage" is exactly the vocabulary drift the glossary exists to prevent, and
it is the kind that produces a confident wrong answer rather than an error.
## Tool ideas, not scoped

Named so they are not forgotten, and explicitly not designed. None of these has
a signature, a data source, or a decision behind it yet. Do not build from this
section; it is a list of things to scope later.

### Challenge-format tools

**Nuzlocke support.** Answering "what can I catch on this route" or "my only
Water type just fainted, what are my options" needs route encounter tables,
which is an entire data axis the dex does not have. Encounters vary by game
within a generation, by time of day, by method (grass, surfing, fishing), and by
version exclusivity. That is a much larger and messier dataset than stats and
moves, and it is the reason this is a project rather than a tool.

It also changes what a good answer is. A Nuzlocke run is constrained by what you
actually caught, not by what exists, so team building becomes optimisation over
a fixed and often bad roster. The team quality rubric would need to know that.

**IRONMON and similar randomiser rulesets.** These impose rules the dex knows
nothing about: forced starters, level caps, banned items, permadeath variants.
Encoding a ruleset is the hard part, and rulesets differ between communities and
change over time, which points at search or a maintained config rather than
baked data.

### What to settle before scoping either

- Which games, not just which generations. Encounter data is per-version.
- Whether the rules are baked, fetched, or supplied by the user per run.
- Whether these are new tools or constraints threaded through existing ones. A
  Nuzlocke is arguably a filter on candidate search rather than a tool of its
  own.
- What the eval layers do with them, since a correct answer under Nuzlocke rules
  is wrong under standard ones.

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
