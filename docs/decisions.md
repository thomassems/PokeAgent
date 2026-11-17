# Decision log

What was decided, what was rejected, and why. Newest last.

## 1. Repo layout: `frontend/` + `backend/`

The Python layers (`api/`, `agents/`, `tools/`, `data/`) nest under `backend/`
rather than sitting at the repo root.

Rejected: **Python at the repo root**, which would have matched the architecture
diagram in CLAUDE.md literally. It puts `pyproject.toml` next to `package.json`,
and a root-level `api/` directory collides with Vercel's legacy convention for
file-based Python functions.

Rejected: **`apps/web` + `apps/api`**, the conventional monorepo shape. The extra
nesting buys room for shared packages that this project will not grow - CLAUDE.md
rules out a database, auth, and every other surface that would justify it.

The deciding factor was that `frontend/` and `backend/` map 1:1 onto a Vercel
service `root`, so the deployment story works without moving files, and the
fallback (two separate Vercel projects) also works without moving files.

## 2. Deployment: one Vercel project, two services

`vercel.json` declares a `services` object plus top-level `rewrites`, so both
halves build independently and share one domain and one route table.

Rejected: **two separate Vercel projects** in the same repo, which is what most
guides describe. It requires the two halves to know each other's URLs via
environment variables, and it splits firewall and deployment-protection settings
across two places.

Open risk: the Services docs page is marked "Permissions Required: Services" and
availability on the Hobby plan is unconfirmed. If Services turns out to be gated,
the fallback is two projects pointed at `frontend/` and `backend/` as root
directories - a `vercel.json` change, not a restructure.

## 3. Python toolchain: uv, Python 3.12, non-package layout

`uv` per CLAUDE.md. Python 3.12 is pinned in `backend/.python-version`; it is both
CLAUDE.md's stated version and Vercel's default, so dev and prod agree.

`[tool.uv] package = false` marks the backend an application rather than a
library, so its modules stay as local source instead of being installed into the
environment. That requires `pythonpath = ["."]` under `[tool.pytest.ini_options]`
for `from api.main import app` to resolve - the two settings go together.

`requires-python = ">=3.12"` has no upper bound, deviating slightly from the
original plan's `<3.13`. Upper bounds on `requires-python` cause resolver
problems, and `.python-version` already pins the actual interpreter for both
local dev and Vercel.

## 4. Frontend: Tailwind + ESLint

Rejected: **CSS Modules**, and **no styling framework at all**. The deliverable is
a dense side-by-side dual-trace view; Tailwind keeps that layout work in the
component instead of in a growing stylesheet. ESLint is what satisfies "no new
lint errors" in the definition of done.

Scaffolded with `create-next-app --empty` to skip the marketing boilerplate.

## 5. Local dev: two processes behind a Next.js rewrite

`uvicorn` on :8000 and `next dev` on :3000, with a rewrite in
`frontend/next.config.ts` proxying `/api/*` to uvicorn. The browser only ever
sees one origin, so there is no CORS middleware anywhere in the backend.

Rejected: **`vercel dev`**. It is free and it exercises the real `vercel.json`
route table, but Vercel's own CLI docs say not to use it when the framework's dev
command already covers the need - `next dev` supports rewrites natively. It also
requires the Vercel CLI and couples the inner loop to a feature whose plan
availability is unconfirmed. It stays available for a routing sanity-check before
the first deploy.

The rewrite is guarded with `if (process.env.NODE_ENV === "production") return []`
so it cannot shadow Vercel's own route table in production.

## 6. `data/` owns the one file read; `tools/` stays pure

CLAUDE.md says `tools/` does no I/O, but `tools/` has to read the baked Gen 4
JSON out of `data/`. Those cannot both be literally true.

Resolved by putting the read in `data/`, at module level, so `tools/` imports an
already-materialised constant and never touches the filesystem:

```python
# data/dex.py
_GEN4 = json.loads((Path(__file__).parent / "gen4.json").read_text())

# tools/coverage.py
from data.dex import TYPE_CHART        # an import, not I/O
```

Python executes a module once per process and caches it, so the read happens a
single time no matter how many tool calls a run makes. Every function in `tools/`
above that import stays deterministic and mock-free to test, which is what the
rule was protecting. `data/` keeps "no logic" - a file read is not logic.

The cost is that importing has a side effect, and malformed JSON becomes an
import-time crash rather than a call-time one. For baked, committed data that is
the better failure: it dies at deploy rather than mid-run.

Rejected: **a generated `data/gen4.py` of Python literals**, which would mean
literally zero I/O and would be precompiled to `.pyc` by Vercel at build time. It
puts a very large generated file into every diff for a benefit the approach above
already delivers.

Rejected: **passing the data in as a parameter** - `find_candidates(dex, filters)`.
Purest and easiest to test, but it collides with the tool-schema generator: that
generator turns a function signature into JSON Schema for the model, so a `dex`
parameter would appear in the schema and the model would try to supply it.
Avoiding that needs an exclusion mechanism in the generator on day one, which is
complexity added to a learning surface to solve a problem the chosen approach
does not have.

## 7. `httpx2` over `httpx` for TestClient

Starlette 1.6 deprecation-warns that `TestClient` wants `httpx2` - the next major
version of httpx, published under a separate PyPI name rather than as `httpx>=2`
so both can coexist during migration.

A deprecation warning alone would not justify swapping a working dev dependency.
The deciding fact is that `openai` 3.5.0 requires `httpx2<3,>=2.7.0`, and the
provider adapter will use that SDK against DeepSeek. `httpx2` is therefore
arriving regardless, and keeping `httpx` for tests would mean carrying two HTTP
client libraries that do the same job.

Dev-only either way; it never ships to Vercel. Note that `httpx2` drops `certifi`
in favour of `truststore`, so TLS verification now uses the system trust store.

## 8. Scope widens beyond Generation 4

The project now covers multiple generations. Generation is app-level state,
selected in the header and passed down.

This came out of the static frontend shell, whose spec called for a generation
selector, mock data spread across several generations, and a regional form -
all of which CLAUDE.md forbade. Rather than build a contradiction, the scope
question was raised and answered: the selector is a real feature.

Rejected: **treating the selector as throwaway scaffolding** for the layout
exercise, leaving CLAUDE.md's Gen 4 rule intact. That would have left the repo
disagreeing with itself and the contradiction to rediscover later.

CLAUDE.md changed with this decision: "Generations other than 4" is gone from
Out of scope, and the glossary now defines Generation and Regional form instead
of asserting Gen 4 only.

What this costs later, none of it yet built:

- Type charts become generation-dependent. Dark and Steel arrive in Gen 2,
  Fairy in Gen 6, and the pre-Gen-6 Steel resistance to Ghost and Dark is
  removed in Gen 6.
- A Pokemon's own typing is not stable across generations - Magnemite gains
  Steel in Gen 2, Togetic gains Fairy in Gen 6.
- Evals must state which generation a scenario runs in, or results are not
  comparable between runs.
- The baked dex under `data/` needs a generation axis rather than a flat list.

## 9. Static frontend shell built as a layout probe

The shell in `frontend/` is deliberately inert: no fetch, no streaming, no
persistence, all content hardcoded. It exists to answer whether the two-panel
comparison layout works before any agent can fill it.

Two choices inside it worth recording. The coverage area shows **both** gap
kinds as separately labelled groups, because the glossary forbids unqualified
"coverage" and because two stacked chip rows is the honest worst case for a
narrow column. The picker is a native `<dialog>` opened with `showModal()`,
which supplies the focus trap, Escape handling, and focus restoration that would
otherwise be hand-written and subtly wrong.

Result panels carry deliberately uneven placeholder content and sit in a grid
with `items-start`, so each keeps its natural height. Equal-height columns would
have hidden the layout question the probe exists to answer.

## 10. Strategy retrieval: canonical JSONL plus a hosted Pinecone index

Strategy knowledge is authored and reviewed as versioned JSONL in the repo.
Pinecone is a rebuildable search index over that corpus, not the only copy of
the data. Each focused passage carries generation, format, battle style, topic,
Pokemon, source kind, and update metadata so retrieval can exclude incompatible
advice before semantic ranking.

The index uses Pinecone integrated embedding and reranking. A query is embedded,
filtered, used to retrieve a small candidate set, then reranked in one hosted
search operation. This avoids adding a second inference provider and stays within
the Starter plan's included usage while the corpus is small.

Rejected: **web search as the only strategy source**. It is useful for current
events and usage, but its prose is unversioned and can silently mix generations
or formats.

Rejected: **Pinecone as the source of truth**. Records edited only in a hosted
index cannot be reviewed in pull requests or reproduced after an index mistake.

Licensing metadata remains in the canonical record for ingestion review but is
not uploaded to Pinecone or shown to the agent. Source kind, name, URL, and date
remain indexed because they affect how retrieved advice should be presented.

---

## 11. One custom-agent run over a POST SSE response

The first live frontend path sends a prompt and the selected generation to
`POST /api/runs`. FastAPI runs the custom agent and sends its progress and final
answer as server-sent events. The agent emits one shared `TraceEvent` model;
the API converts it to HTTP events, and the browser reads them with `fetch`.
This keeps HTTP details out of the agent and uses the existing same-origin
`/api` rewrite. Model calls still complete one step at a time, so progress is
live while the final answer arrives as one event.

Rejected: **native `EventSource` with a GET endpoint**. The run needs a prompt
and generation in the request body. A separate create-run request would need
server-side run coordination that this single-agent milestone does not need.
Rejected: **a Next.js relay route**. It would add another streaming layer when
the existing rewrite already reaches FastAPI. Rejected for now: **token-level
model streaming**, which would change the provider call and agent loop beyond
what is needed to show each agent step.

## 12. Follow-ups carry completed conversation turns

The browser sends prior completed prompt and answer pairs with each new
`POST /api/runs`. Each pair includes the generation selected when its prompt was
sent. The API validates these turns, and the agent appends them as alternating
user and assistant messages before the new prompt. Tool traces and failed turns
are not replayed. Each HTTP request is still a bounded run, but the model sees
the earlier conversation. Refreshing the page clears this in-memory transcript.

Rejected: **server-side session state**. Vercel workers do not provide durable
per-user memory, and a database is outside this project's scope. Rejected:
**replaying all tool calls**, which would increase context size and couple
follow-ups to old tool results when the visible conversation needs only the
answers. The run-wide output budget is now 10,000 tokens after a 2,000-token
budget stopped a short question before its final answer. Step, tool-call, and
time limits remain unchanged.

## 13. Stream answer text during each model step

The custom agent now consumes the provider's message stream and emits each text
chunk as an `answer_delta` trace event. It still reads the complete provider
message after the stream ends, so tool calls, token accounting, and the final
`answer` event use the assembled result. The browser appends deltas immediately
and replaces them with the final answer when that event arrives. If a model step
ends in a tool call, its provisional text is cleared when the tool event arrives.
The same event type belongs to the shared protocol for the future second agent.

Rejected: **revealing a completed answer gradually in the browser**. It looks
similar but leaves the user waiting for the full model response before the first
word appears. The tradeoff with real streaming is that a step can show provisional
text before deciding to call a tool. The UI clears that text when the tool starts.
For scrolling, a new turn is positioned once at its start. Later text chunks do
not move the viewport, so the reader chooses when to see more.

## 14. Event streams opt out of proxy compression

`POST /api/runs` is a server-sent event stream. Next's dev server gzips a
proxied response when the browser sends `Accept-Encoding: gzip`, and the
rewrite proxy never flushes that zlib stream. Measured locally, three events
spaced 0.6s apart arrived together at 1.8s with gzip, and on time without it.
The same compression middleware skips any response whose `Cache-Control`
contains `no-transform`. FastAPI already sends `no-cache` and
`X-Accel-Buffering: no`. Neither stops this gzip path. The API middleware
adds `no-transform` to that one header on `text/event-stream` responses.

Rejected: **`compress: false` in `next.config.ts`**. It also stops the
buffering, but Next's own config docs advise against turning compression off
for the whole server. Static pages and assets would go out uncompressed in
`next dev` and `next start`. The header leaves that compression in place and
matches the opt-out the middleware already implements.

## 15. Pokemon news is in scope and goes to web search

The shared system prompt treats Pokemon-related news and current events as in
scope: the games, events, raids, tournaments, announcements, the anime, and the
trading card game. Those questions are answered with `web_search`, and the
answer names the sources the search returned. News that is not about Pokemon is
declined briefly, with no search.

Rejected: **leaving news outside the scope sentence**. That sentence listed
only team building, matchups, stats, moves, typings, and battle strategy. The
custom loop treated a Pokemon news question as off-topic and refused it, while
the LangChain agent searched. The comparison was then measuring the wording,
not the two loops. Rejected: **answering any current-events question**.
Stock-market news and other news that is not about Pokemon stay out of scope.

## 16. Generation is optional context, off by default

A question that names no generation, with none selected in the UI, is answered
for the latest games. The system prompt says so, and asks for a brief mention
when a generation difference changes the answer. Pokemon news stays in scope
and still goes to web search. News that is not about Pokemon is still declined.

When the user does select a generation, both agents prefix that turn with the
same `Selected generation: N` line, including on replayed history. A turn sent
with generation left off has no prefix. The wording lives in one function,
`format_user_message`, so the two loops cannot drift.

Matchup tools still fall back to the latest chart when the model omits
generation and nothing is selected. When a generation is selected, both agents
fill that argument before the call if the model left it out. An explicit
generation on the tool call is kept, because the question may have named a
different one. `find_pokemon`'s generation filter means "debuted in", so it is
not filled in.

The chat page and the team builder share the selection in localStorage. With
nothing selected, the team builder's type list uses the latest generation, so
Fairy stays available.

Rejected: **prefixing every turn, including a marker that no generation was
selected.** That would keep a generation in front of general questions.
Rejected: **a different prefix in each agent.** The benchmark compares the two
loops, so the question text has to be the same string.

## 17. Pokemon GO is a game mode beside generation

Decided 15 November 2026. The full write-up is
`docs/plans/pokemon-go-mode.md`.

Pokemon GO is a second game on the chat composer. Main series stays the
default. While GO is selected the generation chip hides, the stored generation
is left alone, and both agents receive the same GO prompt section and the same
GO tool list. Phase 1 tools are current events and raid bosses, from the
ScrapedDuck mirror of LeekDuck, cached for 3 hours. Slower feeds, when they
exist, cache for 24 hours. The main-series dex and `search_strategy` are not
on the GO list. The two type-chart tools stay, pinned to the latest chart.
The team builder stays main-series. The trace event schema does not change.

Evergreen GO mechanics (quick catch, Candy XL, trading, Mega candy bonuses)
go in a later phase: a JSONL corpus indexed into the existing
`pokeagent-strategy` Pinecone index under namespace `go-guides-v1`, queried
by `search_go_guides`. That namespace stays separate from `strategy-v1`.
Brave search is the fallback, not the first stop, once the guides exist.

The ScrapedDuck license files disagree (package.json says MIT, there is no
LICENSE file, GitHub metadata said AGPL-3.0). That is a note. It does not
block the work while the app is not monetized. The implementation fetches
JSON and does not vendor the scraper.

Rejected: **treating GO as another generation.** GO CP, moves, and events do
not follow the generation charts. Rejected: **a GO prompt that lives in only
one agent.** Decision 15 already showed that a wording difference is what the
benchmark then measures. Rejected: **scraping LeekDuck directly, or vendoring
ScrapedDuck.** Rejected: **putting GO guides in `strategy-v1`.** That index
is main-series advice filtered by generation and format.

## 18. Chat theme follows the selected game

Decided 16 November 2026, when the theme was implemented ahead of phases
3 and 4. The write-up is the Themed UI section of
`docs/plans/pokemon-go-mode.md`.

The game chip from decision 17 picks the token set on the chat page.
Pokemon GO uses bright map-like greens and blues, rounded cards, a CSS
ball button, and a team-colour accent. Main series uses a light dialogue
frame, Press Start 2P for headings only, the PokeAPI sprites the app
already loads, and a Pokedex-red accent. The team builder is not themed.
It keeps the dark workspace it already has, because it has no game chip
and must not inherit `theme-go`.

This is CSS plus one stored accent (`pokeagent.goAccent`). It does not
change the prompt, the tool list, or the trace event schema. No official
logos, fonts, or ripped art. Press Start 2P is SIL Open Font License,
loaded with `next/font`. Body text stays IBM Plex Sans, and so do the
chip labels, because the pixel face is hard to read at chip size on a
phone.

Defaults for the questions that were still open:

- The theme covers the chat page, header, and composer. It does not
  cover `/team`.
- The main-series frame is a light panel on a light page.
- The accent starts at Neutral. The picker offers Neutral, Blue, Red,
  and Yellow, each as a swatch beside the word. There is no player-team
  field.
- Event and raid answers use the same card frame as any other GO answer.
  The text is still the streamed markdown.
- The main-series empty state shows three PokeAPI starter sprites. The
  GO empty state does not.

## 19. Simple answers stay short

Decided 16 November 2026. Numbered 19 because decision 18 is the theme
proposal that landed with the theme plan.

Both agents share one length rule. A simple factual question or a how-to is
at most four sentences, or one short list plus one sentence of caveat.
The answer comes first. There is no preamble, no second section, and no
recap. The answer goes long only for an analytical question
(team building, matchups, counters, comparisons) or when the user asks for
more detail. The same paragraph is in the main-series prompt and the GO
prompt, so the comparison is not measuring two writing styles.

The run also has one output-token cap, `MAX_OUTPUT_TOKENS` in
`agents/custom.py`. The LangChain agent imports that name, so the two
cannot drift. It was 30,000. It is now 8,000. That is a safety limit for
the whole run, including tool-call JSON. It is not what makes a how-to
short. A counter-team run on the shorter prompt used about 3,700 output
tokens, so 8,000 finishes that kind of answer. The prompt is what keeps a
quick-catch answer short.

Rejected: **a cap of a few hundred tokens.** Tool calls count as output, so
that would cut a multi-step team answer off mid-sentence. Rejected: **a
different length rule in each agent.** Decision 15 already showed that a
wording difference is what the benchmark then measures.


## 20. PvPoke GO stats are fetched, and the license is a note

Decided 17 November 2026, when phase 3 was approved. The write-up is the
battle-stats section of `docs/plans/pokemon-go-mode.md`.

`get_go_pokemon` and `get_pvp_rankings` read PvPoke's MIT-licensed
gamemaster (`src/data/gamemaster/pokemon.json`) and the open overall
ranking files for Little, Great, Ultra, and Master League. PvPoke's
LICENSE grants use of that repository. The underlying numbers are still
Niantic's game data, which PvPoke republishes, and the rankings are
simulations the maintainer regenerates. That is a note. It does not
block the work while the app is not monetized. The same posture as the
ScrapedDuck note in decision 17. An answer that quotes a ranking says
the numbers are PvPoke simulations as of `fetched_at`, not an official
ladder.

The PokeMiners game master is not fetched. Its README does not grant an
application the right to serve that file. Cups stay on `web_search`,
because a model-supplied cup name must not be concatenated into a URL.
There is no battle simulator in this app.

Rejected: **vendoring the gamemaster or the ranking JSON.** They move,
and a checked-in copy goes stale in silence. Rejected: **fetching every
cup directory.** The path is an allowlist of four leagues.

## 21. A pinned GO dashboard is proposed, not approved

Proposed 17 November 2026. Not approved to code. Numbered 21 because
decision 20, above, is the PvPoke license note. The write-up is the
Pinned GO dashboard section of `docs/plans/pokemon-go-mode.md`.

The chat page, while Pokemon GO is selected, would show widgets the user
pins: raids, events over the coming weekend, Community Day, eggs,
research, and Rocket lineups. Pins live in `pokeagent.goPins` in
localStorage, the same kind of browser storage as `pokeagent.game`.
There is no account and no database. The board reads `GET /api/go/snapshot`,
which returns the feed envelopes the tools already cache. Events and
raids stay on the 3 hour TTL. Eggs, research, and Rocket lineups stay
on the 24 hour TTL. The browser clock decides "next weekend". The server
does not.

ScrapedDuck's data branch has no wild-spawn file. A general wild pool is
not a widget. Featured spawns already on event rows can be a card, and
the card says they are event spawns. A true wild-pool question stays on
`web_search`.

This proposal absorbs phase 4. Happening now cards would be the default
pins, not a second empty state. That recommendation is part of what
Thomas still has to accept.

Rejected for this proposal, even if the dashboard is later approved:
**user accounts or a database for pins.** Team state already lives in
the URL, and this app does not grow accounts. Rejected: **a second
fetcher or an ICS parser.** The events JSON is already cached.
Rejected: **scraping a wild-spawn page.** There is no structured feed
for it. Rejected: **computing the weekend on the server.** That uses
the server's timezone, which the plan already calls out as wrong.


## Open questions

Not decided. Each needs its own proposal before code depends on it.

- **Vercel Services availability is unconfirmed.** The docs page is marked
  "Permissions Required: Services" and it is not known whether it is available on
  the Hobby plan. Fallback is two Vercel projects - a `vercel.json` change, not a
  restructure. See decision 2.
- **Post-rewrite path handling on Vercel is unverified.** Whether the backend
  service receives `/api/health` or `/health` after the rewrite has not been
  checked against a real deploy. FastAPI routes carry the `/api` prefix in the
  path itself, which survives either answer, but this needs confirming.
