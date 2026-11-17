# Pokemon GO mode

Status: **phase 2 complete**. Thomas accepted this plan on 15 November 2026
and approved the research, egg, and Rocket filters on 16 November 2026.
Decision 17 records the decisions. Phase 1 is the game selector, the shared
prompt and tool list, and the events and raids tools. Phase 2 is the GO
guides namespace, the type helper, and `get_research_rewards`,
`get_egg_pool`, and `get_rocket_lineups`. Themed UI (phase 5) is
implemented. Decision 18 records the defaults that were chosen.
Phase 3 is `get_go_pokemon` and `get_pvp_rankings`, approved on 17
November 2026. Decision 20 records the PvPoke license note. A pinned
GO dashboard is proposed as phase 6 and is not approved to code.
Decision 21 records that proposal. Phase 4's happening-now cards are
absorbed into that proposal and are not a separate build.

Checked against the repo and the upstream sources on 15 November 2026.

## What this is for

The app should be a reasonable place to ask about Pokemon, not only about a
main-series team. Main series stays the default. Pokemon GO is a second game
the user can select. While it is selected, both agents share one GO prompt
section and one GO tool list, the same way they already share one system
prompt and one `TOOLS` list.

The comparison stays valid only if a given run asks both agents the same
question, with the same prompt text and the same tools. A GO mode that
existed in one loop would measure the prompt, which is the failure decision
15 already recorded for news.

## What stays as it is

- Main series remains the default when nothing is stored and when `game` is
  omitted. Old clients keep today's behaviour.
- The trace event schema stays as it is. Generation is request context, not
  a `TraceEvent` field (`backend/agents/events.py`). Game follows that. A
  new event type is a separate decision.
- `tools/` stays pure: no network, no clock, no cache. The fetch lives in
  `services/`, and `llm/tools/` stays a schema plus a call, which is the
  boundary in `CLAUDE.md` and decision 6.
- Battle simulation and damage calculation stay out of scope. A later
  rankings lookup reports someone else's simulated results. It does not
  grow a simulator.
- The team builder stays a main-series preview. Its slots are still not sent
  to the chat agent (`frontend/app/team/page.tsx`).
- No new package. `httpx2` is already the HTTP client (decision 7).
- No database and no Redis. The cache is process memory.

## How the code is shaped today

Both agents import `SYSTEM_PROMPT` from `backend/agents/prompts.py`.
`backend/tests/test_prompts.py` asserts the two modules hold that same
object. `format_user_message` in `backend/agents/conversation.py` is the
only place a selected generation is prefixed, and only when one was
selected (decision 16).

`Agent` is a `Protocol` with two implementations, `agents/custom.py` and
`agents/framework.py`. The signature is `(user_message, generation, history)`.
`RunRequest` in `backend/api/main.py` carries `prompt`, `generation`,
`history`, and `agent`. `AGENTS` is typed as that protocol, so a signature
drift fails in one place.

`TOOLS` in `backend/llm/tools/registry.py` is one list. The custom loop
passes it to the provider. The LangChain agent builds `StructuredTool`s
from the same list and wraps matchup calls with `apply_selected_generation`.
That helper fills a selected generation into `get_type_matchups` and
`get_type_effectiveness` when the model omits it. `find_pokemon`'s
generation argument means "debuted in" and is left alone.

`web_search` (`backend/services/search.py`) calls Brave and returns a dict
with either `results` or `error`. It does not raise, so a failed search is
something the model can recover from. `search_strategy` queries the
Pinecone index `pokeagent-strategy`, namespace `strategy-v1`, and is
generation- and format-specific main-series advice (decision 10).

The chat page and `/team` share generation through `pokeagent.generation`
in localStorage (`frontend/lib/generation.ts`). Missing or invalid means
no generation, which the chip shows as "Generation: Any". The chip sits in
`PromptPanel` on the chat composer and again inside `TeamBuilder`.

Pokemon news is in scope and goes to `web_search`, and the answer names
the sources. News that is not about Pokemon is declined with no search
(decision 15, and the matching lines in `SYSTEM_PROMPT`).

## 1. UX

### Game selector

Add a game chip beside the generation chip in the chat composer: **Main
series** (default) and **Pokemon GO**. Same menu pattern as
`GenerationChip`: a button, a listbox, Escape and outside-click to close.

Store it under a new key, `pokeagent.game`, in its own small module next
to `frontend/lib/generation.ts`. Missing or invalid stores as Main series.
Do not reuse `pokeagent.generation` for this. The two choices mean
different things and one of them is optional.

### Generation chip

While Main series is selected, the generation chip behaves exactly as it
does now, including "Any".

While Pokemon GO is selected, do not render the generation chip. Leave the
stored generation in place. Switching back to Main series shows the chip
on the value the user last chose, including Any. GO has no generation axis:
typing, CP, and moves do not follow the main-series generation charts, and
a hidden Gen 4 selection must not leak into a GO answer (see the tool
defaults below).

### Team builder

`/team` does not read `pokeagent.game`. It keeps the generation chip and
the main-series type list. The header link stays. A person can be in GO
mode on the chat page, open the team builder, and still edit a main-series
team. Returning to chat restores GO.

There is no GO team builder in this plan. A GO battle team is a different
product: leagues, cups, IV spreads, and a simulator. The simulator is out
of scope, and the current team page is an explicit preview whose slots are
not sent to either agent. Building a GO equivalent would pretend those
slots had a battle meaning they do not have.

### Chat empty state

Phase 1 replaces the three example prompts while GO is selected, so the
empty chat does not keep offering a Generation 4 Steel question with the
generation chip hidden. Proposed examples:

- What raid bosses are in Pokemon GO right now?
- When is the next Community Day?
- What is this week's Spotlight Hour?

Main-series examples stay as they are when Main series is selected.

### Persistence and follow-ups

Each chat turn records the game that was selected when it was sent, the
same way it already records generation (`Turn` in `frontend/app/page.tsx`,
`ConversationTurn`, and the history built per agent). A follow-up replays
that turn under the game it was asked in. The two agents still do not see
each other's answers.

Refreshing the page still clears the in-memory transcript (decision 12).
The game chip survives, because it is localStorage, same as generation.

`RunState` gains a `game` field so a past turn can be labelled. That is
display state. It is not a new trace event.

### Happening now (later)

Phase 4, chat page only, and only when GO is selected and there are no
turns yet. A short row of cards above the example prompts:

- Raid bosses currently listed in the raids feed.
- Community Day (`eventType` `community-day`).
- Spotlight Hour (`eventType` `pokemon-spotlight-hour`, bonus from
  `extraData.spotlight` when present).
- A "Happening now" group for events whose window contains the clock.

Clicking a card submits a fixed prompt ("What should I know about the
current Community Day?") through the existing send path, so both agents
answer it. The cards are not a second product surface.

The cards and the agent have to read the same cache. The browser asks a
thin `GET /api/go/snapshot` that returns the already-trimmed events and
raids. It does not fetch LeekDuck or ScrapedDuck on its own.

Timestamps need care. The ScrapedDuck events wiki says a trailing `Z`
means one global instant, and a timestamp without `Z` is the player's
local time. The server must not decide that a local-time event is "on
now" by comparing it with UTC. The browser does that comparison for the
cards. The agent tools return the strings and a note about the rule, and
the prompt tells the model to say which kind of timestamp it is looking
at.

Card content is text plus the LeekDuck event link from the feed. Image
URLs in the feed point at LeekDuck's CDN. Hotlinking those is not covered
by the written reuse terms below, so phase 4 does not put them in the UI.
Sprites for a main-series Pokedex card are a separate future idea and
already go through PokeAPI.

## 2. Data sources

### LeekDuck, via ScrapedDuck

[LeekDuck](https://leekduck.com/) is the primary source for current GO
events, raid bosses, research tasks, egg pools, and Team Rocket lineups.
This app does not scrape LeekDuck. It reads the JSON mirror published by
[bigfoott/ScrapedDuck](https://github.com/bigfoott/ScrapedDuck).

The README on `master` says ScrapedDuck scrapes LeekDuck with permission
and pushes the result to the [`data` branch](https://github.com/bigfoott/ScrapedDuck/tree/data).
The scrape workflow runs every 10 minutes and force-pushes an orphan
`data` commit. There is no commit history worth pinning. Fetch the branch
tip URLs.

The wiki calls these "endpoints". They are files on that branch. Verified
raw URLs:

| Feed | URL |
| --- | --- |
| Events | `https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/events.min.json` |
| Raids | `https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/raids.min.json` |
| Research | `https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/research.min.json` |
| Eggs | `https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/eggs.min.json` |
| Rocket lineups | `https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data/rocketLineups.min.json` |

Each feed also has a pretty-printed twin (`events.json`, and so on). Use
the `.min.json` files. Formatted and minimized carried the same records
in the snapshot below. The minimized files are what a cache should store.

The [`data` branch listing](https://github.com/bigfoott/ScrapedDuck/tree/data)
on 15 November 2026 also has `calendars/*.ics` (community day, spotlight
hour, raids, research, season, and others). Those calendars repeat the
events feed. Phase 1 does not parse ICS.

Wiki pages that exist: [Endpoints](https://github.com/bigfoott/ScrapedDuck/wiki/Endpoints),
[Events](https://github.com/bigfoott/ScrapedDuck/wiki/Events),
[Raids](https://github.com/bigfoott/ScrapedDuck/wiki/Raids),
[Research](https://github.com/bigfoott/ScrapedDuck/wiki/Research),
[Eggs](https://github.com/bigfoott/ScrapedDuck/wiki/Eggs),
[Rate limits](https://github.com/bigfoott/ScrapedDuck/wiki/Rate-Limits).
The Endpoints page lists events, raids, research, and eggs. It does not
list Rocket lineups. The file is on the branch anyway. There is no Rocket
wiki page. The shape below is from the file, not from a doc.

Rate limits, from that wiki page: the files are GitHub raw files, so
GitHub's limit applies (the wiki cites 5000 requests per hour per IP), and
GitHub caches a raw file for about 5 minutes. A multi-hour cache on our
side is inside both limits. Polling faster than 5 minutes does not see
new data.

#### Snapshot of the live files

Fetched 15 November 2026. Counts will move. Field names are the contract
to code against, and they already disagree with the wiki in the places
marked here. Parsers should keep unknown fields out of the model payload
and should not crash when a documented field is missing.

**Raids.** A list of 13 objects. Keys: `name`, `tier`, `canBeShiny`,
`types`, `combatPower`, `boostedWeather`, `image`. `combatPower` is
`{normal: {min, max}, boosted: {min, max}}`. `types` and `boostedWeather`
are `{name, image}` objects. The wiki's example tier is `"Tier 3"` and it
mentions `Mega`. The live tiers that day were `1-Star Raids` (4),
`3-Star Raids` (4), and `5-Star Raids` (5). No Mega row in `raids.json`
that day. Mega and Shadow bosses were on the events feed instead: see
below.

**Events.** A list of 44 objects. Keys match the wiki: `eventID`, `name`,
`eventType`, `heading`, `link`, `image`, `start`, `end`, `extraData`.
`extraData.generic` (`hasSpawns`, `hasFieldResearchTasks`) was on every
row. Other top-level `extraData` keys present that day: `raidbattles`
(5), `spotlight` (2), `communityday` (1), `promocodes` (1). There was no
top-level `breakthrough` key in this snapshot. The wiki's `breakthrough`
example is a different event shape. Community Day `specialresearch` is
nested inside `extraData.communityday`, and it was present.

That Community Day object (`Pawniard Community Day`) had `spawns`,
`bonuses`, `bonusDisclaimers`, `shinies`, and `specialresearch` (three
steps, each with `name`, `step`, `tasks`, `rewards`). The wiki's picture
of that object matches. A Spotlight Hour can name more than one Pokemon:
`extraData.spotlight` had `name`, `bonus`, and a `list` of further
Pokemon. The wiki example does not show `list`.

`raidbattles` entries are how Mega and Shadow bosses showed up. Five
`raid-battles` events included Cresselia and Darkrai, Mega Banette,
Shadow Tornadus, Deoxys formes, and Mega Metagross, each with
`bosses` (`name`, `image`, `canBeShiny`) and `shinies`. None of those
Mega or Shadow bosses were rows in `raids.json`. A tool that only reads
the raids file will miss them.

`eventType` values present included `community-day`,
`pokemon-spotlight-hour`, `raid-battles`, `raid-hour`, `raid-day`,
`go-battle-league`, `max-battles`, `max-mondays`, `season`,
`timed-research`, and `event`. The wiki's type table is longer than any
one snapshot.

**Research.** A list of 46 objects. Wiki keys are `text`, `type`, and
`rewards`. In the minimized file, `type` was missing on some rows. Reward
keys: `name`, `image`, `canBeShiny`, `combatPower` as `{min, max}`. Task
text contains HTML (`<span>`).

**Eggs.** A list of 78 objects. Wiki keys: `name`, `eggType`,
`isAdventureSync`, `image`, `canBeShiny`, `combatPower`. The live file
also has `isRegional`, `isGiftExchange`, and `rarity`. `eggType` values
that day: `1 km` (27), `2 km` (7), `5 km` (14), `7 km` (12), `10 km` (12),
`12 km` (6). The wiki's allowed list omits `1 km`.

**Rocket lineups.** A list of 26 objects. Keys: `name`, `title`, `type`,
`firstPokemon`, `secondPokemon`, `thirdPokemon`. Leaders: Giovanni, Cliff,
Arlo, Sierra. The rest are grunts, including a decoy. `type` is a type
name or `""` for leaders and the untyped grunts. Each slot is a list of
possible Pokemon, not one object. A slot entry has `name`, `image`,
`types` (a list of strings, unlike raid types), `isEncounter`, and
`canBeShiny`.

### Terms, attribution, and the license conflict

LeekDuck's site has a [privacy policy](https://leekduck.com/privacy-policy/)
dated 30 March 2021 and an [about page](https://leekduck.com/about/).
`https://leekduck.com/terms` returned 404. No terms-of-use page turned up
on the site. The permission to reuse the data is the claim in ScrapedDuck's
README, not a LeekDuck document we can cite.

ScrapedDuck's README "For Developers" section is the written reuse rule:

- Applications of the APIs cannot be hidden behind a paywall.
- Applications of the APIs cannot be monetized with advertisements.
- Credit ScrapedDuck and LeekDuck.

PokeAgent already rules out ads and payments. That matches the first two
lines. Credit has to be visible: the GO prompt tells the model to name
LeekDuck, and to say the feed is the ScrapedDuck mirror, whenever an
answer uses a GO tool. The LeekDuck `link` on an event is the right URL
to show. A one-line credit in the GO empty state ("Event data from
LeekDuck, via ScrapedDuck") covers the cards later.

The license files do not agree with each other:

- `package.json` on `master` says `"license": "MIT"`.
- The full tree of `master` and of `data` contains no `LICENSE` or
  `COPYING` file. `GET /repos/bigfoott/ScrapedDuck/license` returned 404.
- The repository metadata object returned `license.spdx_id` of
  `AGPL-3.0`.

Thomas accepted this as a note, not a blocker. PokeAgent is not monetized.
Phase 1 may fetch the published JSON. Still do not vendor ScrapedDuck's
scraper or copy its source into this repo. The disagreement stays written
down here so a later decision to sell or advertise has to look at it again.

### Cache and staleness

One module, `backend/services/go_feed.py`, fetches the five minimized
files. Phase 1 only needs events and raids. The cache is a dict in the
process: feed name to `(fetched_at, payload)`.

Constants, not settings. Thomas set the two intervals by how fast the
data moves:

- Events and raids refresh every 3 hours. These are the live feeds.
- Research, eggs, and Rocket lineups refresh every 24 hours. Those feeds
  change more slowly and are not part of phase 1.
- If a refresh fails and a previous payload is in memory, return it with
  `stale: true` and the original `fetched_at`. The prompt tells the model
  to say so, and to use `web_search` when the question needs to be current.
- If there is no payload, return an `error` string the model can read.
  Log the exception. Do not put the upstream body, status line, or a stack
  into that string. Same pattern as `web_search`.

The 24 hour figure is the TTL for the slower feeds. It is not a second
deadline after which a failed live refresh must be thrown away.

Vercel isolates do not share this dict, and a cold start fetches again.
That is acceptable at these TTLs. A shared store would be a new
dependency and a database-shaped service. Both are out.

Every tool result includes `source` (`LeekDuck via ScrapedDuck`),
`source_url` (the raw file URL), `fetched_at`, and `stale`. The prompt
uses those so the model can say when the snapshot was taken.

Before the payload reaches the model, drop `image` fields, strip HTML
from text, and drop `extraData` branches the tool does not need. The
events file was about 28 KB minimized. That is acceptable once per
question and too large to paste back unchanged on every step, which is
why the trim happens in the service, not in the prompt.

### Fallback

`web_search` stays on the GO tool list. The GO prompt uses it when:

- the GO tool returns `error`, or `stale: true` and the question needs
  to be current,
- the question is Pokemon GO news the feeds do not hold: a blog post, an
  announcement, a spawn change, a shiny rate the feed does not list.

The answer then names the search sources, which is decision 15. It also
says the structured feed was unavailable or stale when that is why search
ran. It does not invent a raid boss from a search snippet when the feed
returned a fresh list.

### Battle stats: PvPoke and the game master

Phase 3. Thomas accepted the license note on 17 November 2026. Decision
20 records it. Not part of the phase 1 tool list.

GO combat power, moves, and PvP rankings are not in the baked dex.
`get_pokemon` returns main-series base stats. Those numbers are the wrong
answer for a GO CP question. Hiding that tool in GO mode is the point of
a separate toolset.

Two real sources were checked.

**[PokeMiners/game_masters](https://github.com/PokeMiners/game_masters)**
publishes `latest/latest.json`, the game's own game master. The README
says the repo is for educational use, that the content is the property of
The Pokemon Company and Niantic, and that obfuscated field names change.
There is no license that grants an application the right to serve that
file. Do not fetch it at runtime and do not commit a copy.

**[pvpoke/pvpoke](https://github.com/pvpoke/pvpoke)** is MIT-licensed
(`LICENSE` on `master`, copyright 2019 pvpoke). It is a battle simulator,
rankings, and team builder. There is no public API. The maintainer has
said the simulator is client-side JavaScript and has no endpoint
([issue 166](https://github.com/pvpoke/pvpoke/issues/166)). The maintainer
builds `gamemaster` data from the PokeMiners file with `src/data/parse.php`,
then curates it by hand
([issue 269](https://github.com/pvpoke/pvpoke/issues/269)).

Files that exist on `master` and are the ones to use if this phase is
approved:

- Species and moves: `src/data/gamemaster/pokemon.json` (about 1.4 MB)
  and `src/data/gamemaster.min.json` (about 0.9 MB). A species entry has
  `speciesId`, `speciesName`, `baseStats` (`atk`, `def`, `hp`), `types`,
  `fastMoves`, `chargedMoves`, `tags`, `defaultIVs` keyed by CP cap,
  `level25CP`, and sometimes `eliteMoves`. Those `baseStats` are GO
  stats. They are not the main-series six.
- Rankings: `src/data/rankings/<cup>/<category>/rankings-<cp>.json`.
  The open Great League file is
  `src/data/rankings/all/overall/rankings-1500.json` (about 1.2 MB, 1154
  rows on that day). Sibling files: `rankings-2500.json` (Ultra),
  `rankings-10000.json` (Master), `rankings-500.json` (Little).
  Categories under `all/` include `overall`, `leads`, `closers`,
  `switches`, `chargers`, `attackers`, `consistency`. A row has
  `speciesId`, `speciesName`, `rating`, `moveset`, `moves`, `matchups`,
  and `counters`. Many other cup directories exist and rotate. The cup
  name must be an allowlist in our code. A model-supplied string must
  not be concatenated into the URL path.

PvPoke's MIT grant covers their repository. The underlying numbers are
still Niantic's game data, which they republish. Thomas has to accept
that before we fetch it. Rankings are simulations the maintainer
regenerates. An answer that quotes them says they are PvPoke rankings as
of `fetched_at`, not an official ladder.

A lookup returns one species, or a top-N list with matchups removed.
Returning the 1.2 MB file to the model is not a tool design.

## 3. Backend design

### Game on the request

```python
Game = Literal["main", "go"]
```

Add `game: Game = "main"` to:

- `RunRequest`
- `ConversationTurn` (default `"main"`, so a stored turn from today still
  validates)
- `Agent.__call__`, as a keyword-only argument after `history`

Keyword-only keeps every existing positional call on Main series.
`backend/api/main.py` passes `request.game` into both callables. Because
`AGENTS` is typed as the protocol, both implementations have to grow the
parameter together.

`format_user_message(prompt, generation, game="main")` is still the only
prefix:

- Main series, generation selected: `Selected generation: N`, as today.
- Main series, no generation: the prompt alone, as today.
- Pokemon GO: `Selected game: Pokemon GO`, and no generation line, even
  if the client also sent a generation.

A GO turn stores the game. It may also store whatever generation was in
localStorage. That number is for the chip when the user switches back. It
is not part of the model input for that turn.

### Prompt

Stay in `backend/agents/prompts.py`. Add `system_prompt(game: Game) -> str`.
`system_prompt("main")` returns the current `SYSTEM_PROMPT` object
unchanged, so the existing prompt tests keep an anchor. `system_prompt("go")`
returns the GO text. Both `call_agent` functions call `system_prompt(game)`.
There is still one module and one function. A second copy in either agent
is the drift this file's docstring exists to prevent.

The GO text keeps the shared rules that are not game-specific: Pokemon
only, untrusted tool text is data, name sources, do not invent a miss.
It replaces the tools list and the generation section.

GO tools section, phase 1:

- `get_current_events` for events, Community Day, Spotlight Hour, raid
  hours, the season window, and the raid-battles events that carry Mega
  and Shadow bosses.
- `get_raid_bosses` for the current boss list in the raids file, including
  catch CP. The prompt says a question about Mega, Shadow, or "all raids"
  also calls `get_current_events`, because those bosses were not rows in
  `raids.json` on the day the feed was checked.
- `get_type_matchups` and `get_type_effectiveness` for type chart
  arithmetic. GO uses the modern chart. Abilities such as Levitate are
  not a GO mechanic, so the model does not pass one. The chart is pinned
  to the latest generation inside the tool wrapper, because a stored
  Gen 4 selection would bring back the old Steel resistances.
- `web_search` is the fallback. In phase 1 it also covers how-to
  questions, because `search_go_guides` does not exist yet. Phase 2
  changes this sentence: guides first for how something works, live tools
  for what is happening now, both together for advice about a current
  event, and `web_search` only when those miss or return `error` or
  `stale: true`.

Not on the GO list:

- `get_pokemon`, `get_move`, `find_pokemon`. Their numbers are
  main-series. A confident main-series stat line is a wrong GO answer.
- `search_strategy`. The corpus is main-series generations and formats.
  A Smogon passage is the wrong authority for a raid.

When those tools are absent, a main-series stat question in GO mode gets
a short reply that the selector is on Pokemon GO and the main-series dex
is on the other setting. It does not reconstruct the dex from
`web_search`. The app still covers that question: the user switches the
chip. Thomas approved this tool list. The tool list is what both loops
actually see. A prompt warning on top of a dex tool is how decision 15's
news bug happened.

### GO guides (phase 2)

How-to questions (quick catch, Candy XL, trading, the Mega Evolution
candy bonus) are evergreen mechanics. They do not belong in the live
feeds, and they go stale if the only source is Brave. They also do not
belong in namespace `strategy-v1`. That namespace is main-series advice
filtered by generation and format. A GO passage retrieved from it would
mix the two games.

Phase 2 adds a second corpus in the same Pinecone index the strategy
tool already uses, `pokeagent-strategy`, under a new namespace
`go-guides-v1`. Decision 10 still holds: the source of truth is versioned
JSONL in the repo, and Pinecone is a rebuildable index. The records are
their own model. `StrategyRecord` requires a main-series generation and a
singles or doubles format, which a GO guide does not have.

Shape, mirroring `backend/data/strategy.py` and
`backend/scripts/index_strategy.py`:

- JSONL under something like `backend/data/go_guides/guides.jsonl`.
- Fields worth filtering on: `id`, `chunk_text`, `title`, `topic`
  (catching, candy, trading, mega, items, and so on), `pokemon` when the
  passage is about one species, `source_kind`, `source_name`,
  `source_url`, `source_updated_at`, `dataset_version` (`go-guides-v1`).
  Licensing metadata stays in the repo record and is not uploaded, same
  as the strategy corpus.
- An ingestion script, modeled on `backend/scripts/index_strategy.py`,
  dry-runs by default and upserts into `go-guides-v1` with `--apply`.
  Same index, same embedding field (`chunk_text`). It must not write
  `strategy-v1`.
- Refresh is occasional: re-run the script when the JSONL changes. This
  is not the 3 hour live cache and not a scrape. Queries hit Pinecone on
  the call, the same way `search_strategy` does.

`search_go_guides` is registered only on the GO tool list. Both agents
get it from `tools_for("go")`. It takes a query and an optional topic
enum. It does not take a generation. The wrapper lives in `services/`,
next to `strategy_search.py`, because it crosses the network.

The GO prompt, once this tool exists, routes like this:

- How something works: `search_go_guides` first. Do not answer a mechanic
  from memory.
- What is happening now: `get_current_events` and `get_raid_bosses`.
- Advice about a current event: call the live tool and the guides tool,
  then combine them. The Pawniard question below is this case.
- `web_search` only when the guides and the live tools miss, error, or
  come back `stale` and the question needs to be current. Name those
  sources. Do not start at the web for a question the other tools hold.

This waits until phase 2. Putting the namespace, the corpus, and the
prompt change into phase 1 would bundle a new knowledge base into the
protocol change. Phase 1 how-to questions use `web_search` and say so.
The phase 2 prompt edit removes that.

### Type effectiveness and Mega candy

`get_type_matchups` and `get_type_effectiveness` stay on the GO list in
phase 1, pinned to the latest chart. They answer "what hits Dark/Steel
super effectively." That is the right tool for a raid counter question.

"Which Mega should I evolve for the most candy" is a different question.
The Mega catch-candy bonus follows the Mega Pokemon's type matching the
catch, not which attack is super effective. Pawniard is Dark/Steel. A
chart lookup suggests Fighting, Ground, Bug, Fairy, and Fire. The candy
bonus wants a Dark or Steel Mega. Using the chart alone gives the wrong
recommendation.

A new helper is worth having, and it fits phase 2 beside the guides, not
phase 1. Phase 1's tool list is already approved, and the helper is only
useful once the candy rule is somewhere the model is told to read. The
helper is a pure function in `tools/`: given the caught species' types,
return the types that share a type with it (the candy bonus) and, from
the latest chart, the types that are super effective (the raid counter).
No network. The prompt tells the model to use the guide for the rule and
the helper for the types, and the live event tool for which species is
featured today. It does not compute damage.

Generation section in the GO prompt: there is no selected generation.
Type matchups use the modern chart. Say so in one or two sentences. Do
not tell the model to infer a main-series generation from a GO question.

### News rule

Decision 15 still holds. The GO prompt specialises it the same way the
main prompt already specialises exact dex facts:

- Current raids, events, Community Day, and Spotlight Hour come from the
  GO tools, not from memory. Name LeekDuck and the `fetched_at` the tool
  returned.
- Other Pokemon GO news goes to `web_search`, and the answer names those
  sources.
- A fresh GO tool result wins over a search snippet about the same raid
  or event. Search is the fallback when the tool returns `error`, and a
  second look when it returns `stale: true`.
- News that is not about Pokemon is declined, with no search and no GO
  tool call.

### Tool schemas

Schemas live in the registry, next to the existing ones. Property names
match the function parameters. Both agents receive whatever
`tools_for(game)` returns, so they cannot diverge.

Filters are enums or are matched against values already in the payload.
None of them are interpolated into a URL. The fetch URLs are constants.

`get_current_events`

- `event_type`: optional enum of the wiki's `eventType` strings
  (`community-day`, `pokemon-spotlight-hour`, `raid-hour`, and the rest
  of that table). Omitted returns the whole current feed.
- No `now` argument. The server does not classify local-time events as
  current. Each row includes `start`, `end`, and `timing`, which is
  `utc` when the string ends in `Z` and `local` otherwise.
- Rows are trimmed: no images, no HTML. `extraData` keeps the parts a
  question actually needs, and drops the rest. Spotlight keeps `name`,
  `bonus`, and the names in `list`. Community Day keeps spawn names,
  bonus text, disclaimer text, shiny names, and special-research step
  titles plus task text. Raid-battles events keep boss names, shiny
  flag, and shiny names. Unknown `extraData` keys are dropped rather
  than forwarded raw. Field research that is not attached to one event
  waits for `get_research_rewards` in phase 2.

`get_raid_bosses`

- `tier`: optional. The allowlist starts as the labels in the live
  raids file: `1-Star Raids`, `3-Star Raids`, `5-Star Raids`. `Mega` is
  included because the wiki names it, even though that snapshot had no
  Mega row in `raids.json`. Mega and Shadow bosses came back on
  `raid-battles` events, which this tool does not read. An unknown live
  tier still appears when `tier` is omitted. If the feed grows a label
  the enum does not have, the unfiltered call is the supported path
  until the enum is updated on purpose.
- Each boss returns `name`, `tier`, `types` (names only), `canBeShiny`,
  `combatPower`, and `boostedWeather` (names only).

Phase 2, same cache, same result envelope:

`get_research_rewards`

- `task_type`: optional enum from the wiki (`catch`, `throw`, `battle`,
  `explore`, `training`, `rocket`, `buddy`, `ar`, `sponsored`, `event`).
  Rows with no `type` are included only in the unfiltered call.
- No free-text search parameter. HTML in `text` is stripped.

`get_egg_pool`

- `distance`: optional enum `1 km`, `2 km`, `5 km`, `7 km`, `10 km`,
  `12 km`. `1 km` is in the enum because it is in the live file and
  missing from the wiki.

`get_rocket_lineups`

- `group`: optional enum `leader` or `grunt`. Leaders are the four named
  bosses. Everyone else is a grunt, including the decoy.
- A slot stays a list, so the model can see that a grunt slot has
  alternatives. `isEncounter` is how the catch reward is marked.

Phase 3:

`get_go_pokemon`

- `pokemon`: a list of names, same list shape as `get_pokemon`. Lookup
  against the cached PvPoke species file. A miss is reported as a miss.
  Return GO `baseStats`, types, fast and charged moves, elite moves when
  present, `level25CP`, and `defaultIVs`. Do not return the whole file.

`get_pvp_rankings`

- `league`: enum `little`, `great`, `ultra`, `master`, mapped to the
  `all/overall` files at 500, 1500, 2500, and 10000.
- `pokemon`: optional species id. When set, return that row's `rating`,
  `moveset`, and at most three matchups and three counters.
- `limit`: optional, default 10, max 25, used when `pokemon` is omitted.
  List rows omit matchups.
- The result says the numbers are PvPoke simulations.

Cup-specific formats (Remix, a rotating GBL cup, and the many directories
under `src/data/rankings/`) wait until a cup allowlist is worth
maintaining. `web_search` covers "what is the current cup?" until then.

### Where the code sits

| Piece | Place |
| --- | --- |
| Fetch, TTL, stale fallback, image and HTML trim | `backend/services/go_feed.py` |
| Phase 3 PvPoke fetch, same cache rules, species and ranking trim | `backend/services/go_stats.py` |
| Schemas and `tools_for(game)` | `backend/llm/tools/registry.py` |
| Prompt text | `backend/agents/prompts.py` |
| Prefix | `backend/agents/conversation.py` |
| Both loops pass `game` and bind `tools_for(game)` | `custom.py`, `framework.py` |
| Request field | `backend/api/main.py` |
| Chip, storage, request body, history | `frontend/lib/game.ts`, `PromptPanel`, `page.tsx`, `run-state.ts` |
| Activity labels for the new tool names | `frontend/lib/activity.ts` |
| Phase 4 read | `GET /api/go/snapshot` in `backend/api/main.py` |

`apply_selected_generation` stays on the Main series path. On the GO
path the type-chart wrappers fill the latest generation and ignore the
request's generation. An explicit generation on the tool call is still
kept for Main series, because the question may have named one. On the GO
path an explicit generation from the model is overwritten with the latest
chart. GO must not answer with a historical chart the user can no longer
see.

## 4. Testing

Backend tests stay in `backend/tests/` and run with `uv run pytest` from
`backend/`. They do not call GitHub, Brave, Pinecone, or a model. HTTP is
stubbed the way `test_strategy_search.py` stubs Pinecone. Fixtures are
small checked-in JSON snippets copied from the shapes above, including a
row that omits an optional field (`type` on research, `extraData` keys)
so a wiki-shaped parser cannot be the only one that passes.

`test_go_feed.py`

- A fresh cache returns the trimmed payload and `stale: false`.
- A second events or raids call inside 3 hours does not fetch again.
- A slower feed, once those tools exist, does not fetch again inside
  24 hours.
- A failed refresh with a previous payload returns `stale: true` and the
  old `fetched_at`.
- A failed refresh with nothing cached returns `error` and does not raise.
- Images are removed and a `<span>` in research text is stripped.
- A local timestamp is marked `local`. A timestamp ending in `Z` is
  marked `utc`.

`test_registry.py` grows:

- `tools_for("main")` is the current tool set.
- `tools_for("go")` is the phase 1 set, and it does not contain
  `get_pokemon`, `get_move`, `find_pokemon`, or `search_strategy`.
- Every GO schema still matches its function signature, which is the
  check this file already does for the main list.
- A tier or `event_type` outside the enum is rejected the same way an
  unknown dex sort key is rejected.

`test_prompts.py` grows:

- `system_prompt("main")` is `SYSTEM_PROMPT`.
- Both agents call that function rather than holding a private string.
  The identity assertion on the constant stays for Main series.
- The GO string tells the model to use the GO tools for current raids
  and events, to use `web_search` for other Pokemon GO news, and to
  decline news that is not about Pokemon without searching.

`test_generation_context.py` grows a GO case beside the existing pair:
both agents, same history, `game="go"`, and a stored generation on the
new turn. The user text in both loops is `Selected game: Pokemon GO`
plus the prompt. The generation prefix is absent. A type-matchup call
the model left blank is filled with the latest generation, not the
stored one.

`test_agent_stream.py` grows one API case: an omitted `game` is Main
series, and `game: "go"` is what the agent function receives. Invalid
`game` is a 422 from the existing Pydantic model.

Frontend tests stay as `node` tests under `frontend/tests/`, the style of
`activity.test.mjs`. A pure helper that reads and writes the game value
can be tested without a browser. The chip's open and close behaviour is
the same component pattern as the generation chip. There is no browser
suite in the repo today. When the chip is built, the manual check is:
select GO, see the generation chip disappear and the examples change,
reload and see GO stick, open `/team` and see the generation chip still
there, return to chat and see GO restored, switch to Main series and see
the previous generation.

### Evals

Agent runs stay in `backend/evals/`. They are not part of `uv run pytest`,
except the deterministic fixture check that already loads
`retrieval.yaml`. GO questions do not have a dex oracle, so they do not
go in `retrieval.yaml`.

Add `backend/evals/fixtures/go_tool_selection.yaml`, and a `game` field
on the loader's tool-selection case so a GO case is not run against the
main tool list. Scoring which call was made is the existing layer 2 rule:
assert the tool call, not the prose. The scoring implementation is a
learning surface in `CLAUDE.md`. This plan only names the cases. Report
distributions over N runs for both agents. One GO chat in the UI is an
anecdote, which the chat disclaimer already says.

Proposed cases:

| id | prompt | game | expect | forbid |
| --- | --- | --- | --- | --- |
| `go-raids-use-raid-tool` | What are the current 5-star raid bosses? | go | `get_raid_bosses` | `web_search`, `get_pokemon` |
| `go-community-day-uses-events` | When is the next Community Day, and which Pokemon is featured? | go | `get_current_events` | `web_search`, `get_pokemon` |
| `go-spotlight-hour-uses-events` | What is this week's Spotlight Hour bonus? | go | `get_current_events` | `web_search` |
| `go-blog-news-uses-search` | What did the official Pokemon GO blog announce that is not a listed event? | go | `web_search` | `get_raid_bosses`, `get_current_events` |
| `go-non-pokemon-news-is-declined` | What is the stock price of Nintendo? | go | no tool | `web_search`, `get_current_events` |
| `go-main-series-stats-are-not-the-dex` | What are Garchomp's base stats in the main series? | go | no `get_pokemon` | `get_pokemon` |
| `main-raid-question-still-searches` | What raid bosses are in Pokemon GO right now? | main | `web_search` | `get_raid_bosses` |

The last row keeps today's news rule on the Main series tool list. The
GO tools are not registered there, so a main-series run cannot call
them. The Garchomp row locks the approved choice to keep `get_pokemon`
off the GO list.

A Mega or Shadow raid question is a two-tool case: `get_raid_bosses`
for the raids file, and `get_current_events` because that snapshot kept
Mega and Shadow bosses on `raid-battles` events only. Add that row when
the phase 1 prompt text for it is settled, so the expected call list
matches the prompt rather than the other way around.

Phase 2 adds these rows with `search_go_guides`. They are not phase 1
cases: the tool is not registered yet, and a phase 1 run that is graded
against it would fail for that reason.

| id | prompt | game | expect | forbid |
| --- | --- | --- | --- | --- |
| `go-quick-catch-uses-guides` | How do I quick catch? | go | `search_go_guides` | `web_search`, `get_current_events` |
| `go-candy-xl-uses-guides` | How can I get more Candy XL? | go | `search_go_guides` | `web_search`, `get_raid_bosses` |
| `go-community-day-mega-candy` | For today's Pawniard Community Day, which Pokemon should I Mega Evolve to get the most candy? | go | `get_current_events` and `search_go_guides` | `web_search` |

The third row is the combine case. The event tool says what is featured
today. The guide holds the Mega candy rule. `web_search` is a fallback
only if one of those returns nothing useful. The type helper, if it is
built, may also be called. It is not required for the row to pass as
long as the two sources above are both used. Grading this row on the
answer text would hide a run that guessed the Mega from memory.

The research, egg, and Rocket rows are in the same fixture:
`go-egg-pool-uses-eggs`, `go-research-shiny-uses-research`, and
`go-giovanni-uses-rockets`. A Great League row waits for phase 3.
A prompt change, including landing the GO string, is a reason to run
the suite. The project already says prompts break silently.

## 5. Phased rollout

### Phase 1

Game chip, localStorage, `game` on the request and on history, shared
`system_prompt` and `tools_for`, the feed cache, `get_current_events`,
`get_raid_bosses`, GO example prompts, activity labels, and the tests
above.

This is the invasive phase because it crosses the protocol: both agents,
the API model, the chat request, and the prompt. The tools themselves
are filters over one cache. The team page does not change.

### Phase 2

The guides namespace first. That is the next slice after events and
raids, because the how-to questions are the gap phase 1 fills with Brave,
and because the corpus is a new dataset rather than three more filters
on the feed cache.

- Authored JSONL, `search_go_guides`, ingestion into `go-guides-v1` on
  the existing `pokeagent-strategy` index, and the prompt routing in the
  guides section above.
- The type helper that separates Mega candy types from super-effective
  types.
- The three eval rows for quick catch, Candy XL, and the Pawniard Mega
  question.

Research, eggs, and Rocket lineups are done in this phase, after the
guides. They are filters on the phase 1 cache with a 24 hour TTL. Prompt
lines and eval rows for each. No new UI. The live files, checked on 16
November 2026, still disagree with the wiki: some research rows omit
`type`, eggs include `1 km`, and `rocketLineups.min.json` exists even
though the wiki's Endpoints page does not list it.

### Phase 3

Done. `get_go_pokemon` and `get_pvp_rankings` read PvPoke's MIT-licensed
gamemaster and the `all/overall` files for little, great, ultra, and
master. The cache uses the 24 hour TTL and the same stale fallback as
the slow LeekDuck feeds. A league is an allowlist key, so the name
cannot become a URL path. Cups stay on `web_search`. Ranking results
are labelled as PvPoke simulations. There is no simulator. Decision 20
records the license note. The files are large and the cup list moves,
which is why this stayed separate from the ScrapedDuck feeds.

### Phase 4

Absorbed into phase 6 on 17 November 2026. Do not build a separate
Happening now row. The snapshot route, the browser clock, the LeekDuck
text links, and the rule against hotlinking LeekDuck images move into
the pinned dashboard. The empty-state example prompts stay as the
fallback when that snapshot fails. Phase 6 itself is still not
approved to code.

### Phase 6

Proposed, not approved to code. A GO dashboard of widgets the user pins.
The write-up is the Pinned GO dashboard section. Decision 21 records
the proposal. No tool, prompt, or trace change is part of this proposal.

### Effort

Phase 1 is a protocol change plus a small service. The files it touches
are the ones in the table above. Most of the care is keeping both agents
on the same prompt, the same prefix, and the same tool list.

Phase 2 starts with a corpus and an ingestion script in the shape of
the strategy index, then a tool and a prompt edit both agents share.
The research, egg, and Rocket tools after that are filters on the cache.

Phase 3 is a second client, trimming megabyte-sized JSON down to one
species or a short list, and an allowlist so a cup name cannot become a
path.

Phase 4 is not its own build. Its GET route and empty state move into
phase 6. Phase 6, if approved, is that route plus a pin board on the
chat page. It does not add a fetcher. The species images are PokeAPI
sprites the browser already knows how to build. They are not a new host.

Phase 5 is a class and a second set of CSS tokens on the chat page. The
team page stays on the tokens it already has.

### Risks

- The wiki is already behind the files: raid tier labels, the `1 km` egg,
  optional research `type`, and an undocumented Rocket file. A parser
  written from the wiki alone will drop or mislabel live rows. Tests
  should use a fixture taken from the files, and the trim should ignore
  unknown keys instead of failing the run.
- Local-time event strings compared on the server will mark the wrong
  events as current for anyone not in the server's timezone.
- If `get_pokemon` stays available in GO mode, both agents will sometimes
  answer a CP question with main-series base stats. The tool list is the
  reliable fix. A prompt sentence is not.
- If the type-chart wrapper keeps honouring a stored generation, a hidden
  Gen 4 selection changes Steel's Ghost and Dark resistances in a GO
  answer.
- ScrapedDuck can change a field name on the next scrape. The `data`
  branch is force-pushed. A strict Pydantic model that rejects the whole
  feed on one bad row takes raids down until we deploy a fix. Prefer
  skipping a bad row, logging it, and returning the rest, plus `error`
  only when the file itself will not parse.
- Process-local cache means two isolates can be up to 3 hours apart, and
  a cold start pays one GitHub fetch per feed. That is the trade for not
  adding a store.
- The license metadata is contradictory. Shipping a vendored copy of the
  scraper would be the expensive version of that mistake.
- LeekDuck can withdraw the permission ScrapedDuck claims. The fallback
  is `web_search` and a prompt that stops calling the GO tools. There is
  no second structured source in this plan.
- PvPoke rankings are a moving target and a large download. Caching the
  parsed Great League file in an isolate is fine. Handing it to the model
  is not.
- A GO prompt that is only wired into the custom loop makes the benchmark
  meaningless. The tests that compare the two user texts are the guard.
- A theme that reads `pokeagent.game` on every page would restyle the team
  builder, which does not have a game chip. The theme class is only on the
  chat page, so the team builder keeps the dark workspace it already has.

### Phase 5

Themed UI, pulled ahead of phases 3 and 4. It does not depend on the
PvPoke tools or the Happening now cards, and those stay phases 3 and 4 so
the numbers already used in this plan do not move. The design and the
chosen defaults are the Themed UI section below. Decision 18 records them.

Phase 5 is CSS and a class on the chat page, plus a stored accent that
only the chat reads. No new tool, no prompt edit, no trace event, and no
new package. The heading face is Press Start 2P, loaded by `next/font`
from Google Fonts (SIL Open Font License). Sprites are the PokeAPI URLs
the app already builds.

## Themed UI

Implemented, ahead of phases 3 and 4. Thomas wants the page to feel less
plain, and he wants each game to look like itself: Pokemon GO while that
chip is selected, and the main games while Main series is selected. This
is presentation. It does not change what either agent is asked, which
tools it can call, or what a run records.

The switch is the game chip that phase 1 already stores in
`pokeagent.game`. The chat page sets a theme token from that value. Main
series is the default, including when storage is missing. Switching back
restores the main-series theme in the same render as the generation chip.
`/team` does not read the game. It keeps the main-series theme even if the
chat page last stored `go`.

### What each theme is aiming at

These are original treatments inspired by the games. They are not a copy
of a title screen, a HUD, or a map screenshot.

Pokemon GO:

- Bright, map-like greens and blues. The page reads as outdoors rather
  than as the current dark device shell.
- Rounded, bubbly cards for the answer panels and the composer, closer to
  an item sheet than to a log.
- A round send button with a simple ball-like disc: a circle, a band, and
  a centre button, drawn in CSS. Not the official ball artwork.
- Small accents in the three team colours (blue, red, yellow) used as
  decoration next to a text label. Colour is never the only signal.
- Event and raid answers can sit in a card with a short heading and a
  list, so a raid boss list looks like a card rather than a wall of
  prose. The text is still the agent's answer. The card is a frame.

Main series:

- The answer sits in a classic dialogue frame: a light panel, a dark
  border, and a small continuation mark. The frame is CSS, not a ripped
  text-box graphic.
- A pixel face for headings and for the chip labels only. Body text stays
  the current sans face so a long answer stays readable.
- Pixel sprites where the UI already shows a species, from the PokeAPI
  sprites the app already loads. No new sprite pack.
- A Pokedex-red accent on the primary control and on the focus ring,
  replacing the current amber plasma colour for this theme only.
- The game chip and the generation chip read as menu rows: a stacked
  list, a highlighted row, keyboard focus unchanged.

### How it is built

Colours, radii, and the heading face live as CSS variables on one
ancestor. Today `frontend/app/globals.css` already puts every colour in
`@theme`, and components are not supposed to carry their own hex values.
The theme adds a second set of tokens, selected by a class such as
`theme-go` or `theme-main` on the chat page, rather than a second
stylesheet of raw colours in each component. Shared pieces (the header,
the focus ring, the composer) read the tokens. A component that needs a
different shape, such as the dialogue frame or the round send button,
gets a class under that theme and does not fork the React tree.

The team builder keeps the tokens it has now. It does not inherit
`theme-go`.

### Readability, motion, and small screens

Text contrast stays at WCAG AA for body text on cards and on the dialogue
frame. The bright GO greens are backgrounds. Text on them is a dark ink,
not white-on-lime. Team-colour accents are borders or dots beside a word,
not the text colour of a sentence.

`globals.css` already shortens animation under
`prefers-reduced-motion: reduce`. New motion has to live under that rule.
The allowed motion is small: a send button that presses in, and a card
that fades in. No map panning, no bouncing ball, no sprite bob. Reduced
motion leaves the final state with no travel.

The chat already stacks the two agent panels under the `panels`
breakpoint. Themed cards and the dialogue frame use that same stack.
Chips wrap instead of overflowing. The send control stays a visible tap
target. A theme that only looks right as two columns is not done.

### What this will not use

No copied official logos, wordmarks, or title-screen art. No Nintendo,
Game Freak, or Niantic font files. No ripped UI textures, map tiles, or
item icons. A pixel heading face, if one is added, is an open font or
none at all. PokeAPI sprites that the app already requests are the only
outside images in scope. Hotlinking LeekDuck images stays out, as phase 4
already says.

### Chosen defaults

These were open questions. The implementation picks the following so the
theme can ship without waiting on phases 3 and 4.

1. The theme covers the chat page, including the header and the composer.
   The team builder is not themed. It keeps the dark workspace it already
   has, and it does not read `pokeagent.game` or the accent.
2. Main-series chat is a light page with a light dialogue frame. A light
   card on the near-black shell was the harder contrast problem.
3. Headings use Press Start 2P (CodeMan38, SIL Open Font License 1.1),
   loaded with `next/font`. Body text stays IBM Plex Sans. Chip labels
   stay the sans face too: the pixel face at chip size is hard to read
   on a phone.
4. The accent starts at Neutral, a muted green-gray that is not a team
   colour. A picker labelled Neutral, Blue, Red, and Yellow is stored in
   `pokeagent.goAccent`. The colour is a swatch and the centre of the
   send button, always beside the word. There is still no player-team
   field.
5. An event or raid answer uses the same rounded card as any other GO
   answer. The frame is CSS around the streamed markdown. There is no
   new trace event.
6. The main-series empty state shows three PokeAPI sprites (Bulbasaur,
   Charmander, Squirtle) as decoration. The GO empty state does not.

## 6. Future ideas

These are not designed and have no tool signatures. They are here so the
game selector is not painted into a corner.

**Pokemon TCG mode.** Another value on the same chip, with its own prompt
section and its own tool list, both agents together. The main-series dex
and the GO feeds do not answer card questions. Pick a card source when
that mode is actually scoped. Do not invent one in the GO work.

**Pokedex quick-look cards in chat.** When an answer is about a specific
species, the chat can show a small card: name, types, sprite. The
frontend already loads sprites from PokeAPI. Doing this well wants a
structured handle in the trace, which is an event-schema change and its
own decision. Scraping the prose for names will mis-fire.

**Image upload.** A screenshot to identify a Pokemon, or to react to a
team. Both agents would need the same image content on the user message,
and the provider adapter would have to accept it. The model path today
is DeepSeek through an Anthropic-compatible base URL. This plan does not
assume that path accepts images. A team photo is also close to the team
builder, whose slots are still not sent to the agent. Scope it when the
provider can take an image and when there is a reason to connect the
team page to a run.

## Pinned GO dashboard

Proposed 17 November 2026. Not approved to code. Decision 21 records
this proposal. Nothing in this section is a prompt change, a tool
change, or a trace change. The team page is not part of it.

The chat page, while Pokemon GO is selected, shows a board of widgets
the user pins. The board is a view of the feed cache the agents already
use. It does not call a model.

### Widgets and the cache

Checked against the ScrapedDuck `data` branch on 17 November 2026. The
files there are `events`, `raids`, `research`, `eggs`, `rocketLineups`,
and a `calendars/` directory of `.ics` files. There is no wild-spawn
file.

| Widget | What it shows | Where the data already is | TTL |
| --- | --- | --- | --- |
| Current raids | Bosses grouped by tier, with the feed's `fetched_at` and `stale` | `get_raid_bosses` / the raids feed | 3 hours |
| Events next weekend | Events whose interval overlaps the coming Saturday and Sunday | `get_current_events` / the events feed. The browser filters | 3 hours |
| Community Day | Community Day rows, including the spawns and bonuses the trim already keeps | the same events feed, `event_type` `community-day` | 3 hours |
| Current eggs | Hatches grouped by distance | `get_egg_pool` / the eggs feed | 24 hours |
| Research | Field research tasks and rewards | `get_research_rewards` / the research feed | 24 hours |
| Rocket lineups | The four leaders, with grunts behind a show-more | `get_rocket_lineups` / the Rocket feed | 24 hours |
| Featured event spawns | Species already listed on Community Day and Spotlight rows | `community_day.spawns` and `spotlight.pokemon` on the events feed | 3 hours |

Current wild spawns, meaning the general pool in the world right now,
are not in the mirror. Thomas decided that featured event spawns
replace a wild-spawn widget. There is no wild-pool card. The featured
card says the species are event spawns, not the wild pool. A question
about the general wild pool stays on `web_search`. This proposal does
not add a scraper, and it does not parse the `.ics` calendars. The
events JSON already has start, end, and the structured extras. A second
parser would be a second source for the same events.

"Next weekend" is the browser's local Saturday 00:00 through Sunday
24:00. If today is Saturday or Sunday, that is the current weekend.
Otherwise it is the next one. An event overlaps the window when its
interval does. A timestamp marked `local` is used as a wall time. A
timestamp marked `utc` is converted to the browser's zone. The server
does not decide the window. That is the timezone risk already listed
under Risks, kept on the client on purpose.

### Where pins are stored

`pokeagent.goPins` in localStorage, a JSON array of widget ids from the
allowlist in the table. The same pattern as `pokeagent.game` and
`pokeagent.goAccent`. No account and no URL state in this phase.
A missing or unreadable value falls back to the default pins Thomas
chose: raids, events next weekend, and Community Day. Entries that are
not in the allowlist are dropped on read. The array cannot grow past
the allowlist. Clearing storage restores that default.

Server-side persistence of the pin set is wanted later. It is not this
phase. The feed cache is already server-side and process-local. That
cache is the widget data, not the user's pins. Pins have no user to
attach to, because this app has no accounts. A later step would need
its own decision for where a pin set lives once it leaves the browser.
This phase does not add that store.

### Layout

GO theme only, on the chat page, inside the column the chat already
uses. `/team` does not read the pins and does not gain `theme-go`.

Desktop: a grid of cards, two or three across, in the empty state under
the welcome text and above the example prompts. Cards use the same
frame as a GO answer. Text, a LeekDuck link, and a PokeAPI sprite where
the row names a species.

Mobile: one column. A wrapping row of pin chips sits above the cards.
Cards stack. What happens to the full cards after the first turn is
still open. One option is that they stay open above the transcript.
The other is that they collapse to one line each (name, fresh or
stale) so the two agent panels stay on screen, and expanding a line
shows that card. Do not pick one until Thomas does.

Cards are read-only. They do not fill the composer and they do not
start a run.

Eggs show a count per distance, collapsed. A card whose feed returned
`error` says the feed is unavailable. A card whose feed is `stale`
says so and shows `fetched_at`.

### Species images

Widgets show a Pokemon image wherever a row names a species. Raids and
featured event spawns must. Eggs, research rewards, Rocket slots, and
Community Day spawns do too when the name is a species. An item reward
such as Stardust stays text.

The image source is the PokeAPI sprite the app already uses.
`spriteUrlFor` in `frontend/lib/pokeapi.ts` builds
`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`
from a PokeAPI pokemon id. The name index at
`https://pokeapi.co/api/v2/pokemon?limit=2000` lists forms as their own
entries (`meowth-alola`, `charizard-mega-x`), each with its own id.
The sprite for that id is the form. The national dex number of the
base species is the wrong id: it draws Kantonian Meowth for Alolan
Meowth.

The browser maps a feed name onto a slug, then onto that id. The
snapshot stays text. LeekDuck image fields stay dropped. Do not
hotlink them.

The map, in order:

1. Take the display name from the feed.
2. If it says Shadow, remember that for the caption and remove the
   word before the lookup. PokeAPI has no Shadow sprite. The image is
   the base form, and the caption still says Shadow.
3. Rewrite GO word order onto PokeAPI's slug. "Alolan X" becomes
   `x-alola`, "Galarian X" becomes `x-galar`, "Hisuian X" becomes
   `x-hisui`, "Paldean X" becomes `x-paldea`, "Mega X" becomes
   `x-mega`, and "Mega X Y" becomes `x-mega-y`. A parenthetical form
   becomes hyphenated words: "Basculin (White Striped)" becomes
   `basculin-white-striped`.
4. Look that slug up in the existing name index. On a hit, use
   `spriteUrlFor` with that entry's id.
5. On a miss, try the base species slug, with the regional or Mega
   words removed.
6. On a second miss, show the name and no image. Do not invent an id.
   A sprite that fails to load is the same as a miss.

Form-mapping risks:

- The adjective is on the other side of the name from PokeAPI's slug.
  A join that only lowercases "Alolan Meowth" looks up `alolan-meowth`
  and misses `meowth-alola`.
- Punctuation and accents (`Mr. Mime`, `Farfetch'd`, `Type: Null`,
  Flabebe) do not match a slug without a small alias list.
- "Paldean Tauros" is three breed slugs. A feed name that does not
  name the breed must not guess one. Fall back to the base Tauros
  sprite, or to no image.
- Costumes, hats, and other GO-only forms are not in PokeAPI. They
  get no image.
- A Mega raid that names the base species, "Charizard", must not be
  promoted to a Mega sprite.
- Some forms have no `front_default`. The github sprite path can 404.
  Hide the image. Do not substitute a LeekDuck URL.
- Two feed rows can share a name, such as Galarian Corsola in both
  7 km pools. One sprite is right for both.

### How many rows a card shows

Thomas left the show-more counts open, because they depend on how the
cards size. These are the proposed caps, not a decision:

| Widget | Proposed first view | Sprite |
| --- | --- | --- |
| Raids | Every boss in a tier. If a tier has more than 8, show 8 | On every visible boss |
| Featured event spawns | Every species, and show-more after 12 | Required |
| Community Day | The whole event when there is one | On the featured species |
| Events next weekend | 4 events, then show-more | Only when the event names a species |
| Eggs | 6 hatches per distance, then show-more | On each visible hatch |
| Research | 5 tasks, then show-more | Only when the reward name maps to a species |
| Rocket | The four leaders, with each slot's species. 4 grunts, then show-more | On each visible slot. Shadow uses the base sprite |

### Refresh

The board calls `GET /api/go/snapshot`. The handler calls the existing
feed cache. It does not fetch on its own, and it does not shorten the
TTL. Events and raids refresh inside the 3 hour window the cache
already has. Eggs, research, and Rocket lineups refresh inside 24
hours. A refresh control on the board re-requests the snapshot. Until
the TTL expires, that request returns the cached payload, including
`stale: true` when the last refresh failed. The board does not poll
faster than the cache.

### Phase 4

Decided: phase 6 replaces phase 4. Happening now cards are the default
pins (raids, events next weekend, and Community Day), not a second
empty state beside a pin board. One route, one board. The browser
clock, text, and LeekDuck links move with it. LeekDuck images stay
unlinked. Species images are the PokeAPI sprites above. The phase 1
example prompts stay as the fallback when the snapshot fails. Do not
build phase 4 as its own UI. The dashboard is still not approved to
code.

### API

One route, the one phase 4 already names:

`GET /api/go/snapshot`

No query string. A widget id must not become a path. The body is the
five envelopes the cache already returns, keyed `raids`, `events`,
`eggs`, `research`, and `rockets`. Each envelope keeps `source`,
`source_url`, `fetched_at`, `stale`, and the trimmed list. Community
Day, next weekend, and featured spawns are filters the browser applies
to `events`. They are not extra fetches.

One feed failing returns `{ "error": ... }` for that key and still
returns the others. The route does not run an agent and does not read
an API key.

### Effort

One GET handler that calls `load_feed` for the five feeds, and a board
component on the chat page. The name-to-sprite map lives in the
browser, next to the PokeAPI index the team builder already loads.
No new package. No prompt edit. No tool signature change. No trace
event. The care is the weekend filter, the form slug map, the stale
label, and keeping the board off `/team`.

### Risks

- Computing the weekend on the server would mark the wrong events for
  anyone not in the server's timezone. The filter stays in the browser.
- A stale card that does not say so looks like today's raids.
- localStorage pins do not follow the user to another browser. That is
  the trade for not adding accounts.
- A research or Rocket card that renders every row is too long on a
  phone. The card caps itself.
- Featured event spawns read as the general wild pool unless the card
  says they are event spawns.
- A slug map that uses the base species id draws the wrong form.
  Alolan, Galarian, Hisuian, Paldean, and Mega sprites have to come
  from the form's own PokeAPI id.
- A Shadow, costume, or unmatched name that falls through to a
  LeekDuck image URL breaks the rule this plan already has. The miss
  path is no image.
- Persisting pins on the server later has nothing to key them by
  until there is an identity. That step is not localStorage with a
  different name. It needs its own decision.
- A theme class on the board must stay on the chat page. `/team` has
  no game chip.
- The snapshot must not call the model. A feed envelope is not a run.

### Open questions

Answered 17 November 2026:

1. Phase 6 replaces phase 4. Do not build a separate Happening now row.
2. A new browser starts with raids, events next weekend, and Community
   Day pinned.
3. Featured event spawns replace a wild-spawn widget. There is no
   wild-pool card.
4. Cards are read-only. They do not fill the composer.
5. Pins are in localStorage for this phase. Server-side persistence
   of the pin set is a later step, not part of this proposal.

Still open:

1. After the first turn, do the full cards stay open above the
   transcript, or collapse to one line?
2. The show-more counts above are a proposal. They stay open because
   they depend on how the cards size.

## Decisions from Thomas

Answered 15 November 2026.

1. The team builder stays main-series and ignores the game chip.
2. The phase 1 tool list is approved: events, raids, the two type-chart
   tools pinned to the latest chart, and `web_search`. The main-series
   dex tools and `search_strategy` stay off the GO list.
3. Licensing is a note, not a gate. He is not monetizing. The
   disagreement is recorded above. Do not vendor the scraper.
4. Live feeds (events, raids) cache for 3 hours. Slower-changing feeds
   cache for 24 hours. A failed refresh serves the last payload with
   `stale: true`, or an error when there is no payload, and Brave is the
   fallback.
5. The guides namespace is phase 2, after events and raids. Phase 1 does
   not register `search_go_guides`.
6. A GO type helper is worth adding in phase 2 for the Mega candy
   question. It is not part of the approved phase 1 tool list.

## Still open

1. Answered 17 November 2026. Phase 3 fetches PvPoke's MIT-licensed
   gamemaster and overall ranking JSON, and does not fetch the
   PokeMiners game master. Rankings are quoted as PvPoke simulations.
   Decision 20 records it. Licensing stays a note.
2. Answered 17 November 2026. Phase 6 replaces phase 4's Happening now
   cards. The browser clock and the ban on hotlinking LeekDuck images
   still apply. Species images are PokeAPI sprites. The dashboard is
   not approved to code.
3. Should every GO answer that used a feed include the LeekDuck credit
   in the text, or is the empty-state credit plus the source fields in
   the tool result enough for the model to mention when it matters?
4. Themed UI is phase 5 and is implemented ahead of phases 3 and 4.
   The defaults are in that section and in decision 18.
5. A pinned GO dashboard is proposed as phase 6 and is not approved to
   code. Default pins, featured spawns, read-only cards, and
   localStorage are decided. Collapse after the first turn, and the
   show-more counts, are still open. Decision 21 records it.

## Approved to code

Phase 1 is approved. These are the confirm-first changes that approval
covers:

- The shared prompt gains `system_prompt(game)` and a GO text.
- `Agent`, `RunRequest`, and `ConversationTurn` gain `game`.
- The GO tool list differs from the main list. Both agents still receive
  the same list for a given game.
- New tools in phase 1: `get_current_events` and `get_raid_bosses`.
- `format_user_message` grows a game prefix and suppresses the generation
  prefix on GO turns.

The trace event schema does not change. `search_go_guides`, the guides
corpus, and the type helper are phase 2 and are not part of this approval
to code.
