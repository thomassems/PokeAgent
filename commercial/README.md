# Commercial edition

A second copy of the app, kept under `commercial/` so it can later become its
own repository. The personal app at the repo root is the free edition and is
unchanged. This copy is the one that could charge money. Nothing here is a
decision to charge yet.

The product name is **Trainermon**. `APP_NAME` overrides the label. If it is
unset, the UI says Trainermon. The name does not use a "Poke" prefix. The
PokéAPI credit in the footer is their license notice, not this product's name.

Until this tree is split out, a fix to code that exists in both places has to
be applied twice. There is no shared package.

## What is different

Removed, because a paid or ad-supported app cannot keep them:

- LeekDuck and ScrapedDuck live data: events, raids, field research, eggs,
  Rocket lineups, and the tools that served them (`get_current_events`,
  `get_raid_bosses`, `get_research_rewards`, `get_egg_pool`,
  `get_rocket_lineups`). ScrapedDuck's README, read on 17 November 2026,
  says applications of that data cannot be hidden behind a paywall and
  cannot be monetized with advertisements.
- Official Pokémon artwork. PokeAPI sprite URLs are The Pokémon Company's
  art. Team slots and the welcome row use a type-coloured badge with
  initials. The client does not build or store a sprite URL.
- Any claim, in the shared system prompt, that the agent has a live GO
  event feed. A "right now" question is answered by saying so, and a web
  search is labeled a web report.

Kept:

- Both agents, the custom loop and the LangChain one, on the same prompt
  and the same remaining tools.
- Main-series dex, moves, and the type chart. Those JSON files are baked
  from PokeAPI's CSV source. PokeAPI's `LICENSE.md` is BSD-style: keep the
  copyright notice, and do not use the PokeAPI name to endorse a product.
  Pokémon and Pokémon character names are trademarks of Nintendo, which
  that license also says.
- `get_go_pokemon` and `get_pvp_rankings`. They fetch PvPoke's gamemaster
  and the four open overall ranking files at runtime. PvPoke's repository
  license is MIT, Copyright (c) 2019 pvpoke
  (https://github.com/pvpoke/pvpoke/blob/master/LICENSE). The footer carries
  that credit. MIT covers PvPoke's repository. It does not grant rights in
  the game data PvPoke republishes.
- `search_go_guides` and `get_go_type_roles`. The guides in
  `backend/data/go_guides/guides.jsonl` are original summaries
  (`source_kind: pokeagent-authored`). They are not a LeekDuck feed. Each
  record's `license` field says so.
- `web_search`, for cups and for current questions this edition cannot
  answer from a feed.

Not present here, so nothing had to be deleted: a wild-spawn feed, and the
pinned dashboard. That dashboard is a proposal on the personal app and it
depends on ScrapedDuck.

## Run it

From `commercial/`. Requires [uv](https://docs.astral.sh/uv/) and Node 22+.

```bash
cd backend && uv sync
cd ../frontend && npm install
cp ../.env.example ../.env
```

`.env` is gitignored. `.env.example` holds names only. Never commit a key.
`frontend/next.config.ts` reads `APP_NAME` from `commercial/.env` and ignores
every other line, so model keys stay out of the Next process unless you
export them yourself. The backend loads the file explicitly:

```bash
cd backend && uv run --env-file ../.env uvicorn api.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

Open http://localhost:3000. The frontend proxies `/api/*` to port 8000 in
development. FastAPI's docs are at http://localhost:8000/docs.

## Accounts

Local accounts use a SQLite file. You do not need a hosted database, and you
do not create a Supabase project to run or test this copy. `TRAINERMON_DB`
overrides the path. Unset, the file is `backend/data/local.db`, which is
gitignored.

Sign-in is a local email and password. The password hash stays in that file.
There is no call to Pokémon GO, and no account-trading flow. Sign-up asks
the trainer to confirm they are 13 or older and rejects the account
otherwise.

`TRAINERMON_ADMINS` is a comma-separated list of emails that may open
`/curate`. Nobody is an admin until you set it. `SHOW_OFFICIAL_SPRITES`
defaults off and does not add artwork. Drafting a curated row needs
`ANTHROPIC_API_KEY` on the server, the same key the assistant already uses.
`TRAINERMON_DRAFT_MODEL` overrides the draft model. Unset, it uses
`deepseek-v4-flash`.

A friend code is optional. It is returned only on `/api/me` for the signed-in
trainer. Search results do not include it. `SHARE_FRIEND_CODES` defaults off
and does not publish codes. The contact method is still undecided.

When you want this off your laptop, a free [Supabase](https://supabase.com/pricing)
project is the intended host: Postgres, and their free Auth tier if we wire it
later. This build does not read `SUPABASE_URL` or any Supabase key. The tables
to create there, when that work happens, match the local schema:

```sql
CREATE TABLE users (
  id bigint generated always as identity primary key,
  email text not null unique,
  password_hash text not null,
  trainer_name text not null,
  city text not null,
  friend_code text,
  created_at timestamptz not null,
  age_ok boolean
);
CREATE TABLE sessions (
  token_hash text primary key,
  user_id bigint not null references users(id),
  expires_at timestamptz not null
);
CREATE TABLE list_entries (
  id bigint generated always as identity primary key,
  user_id bigint not null references users(id),
  kind text not null,
  species_id text not null,
  form text not null,
  shiny boolean not null,
  dynamax boolean not null,
  gigantamax boolean not null,
  shadow boolean not null,
  purified boolean not null,
  lucky boolean not null,
  costume boolean not null,
  notes text not null
);
CREATE TABLE curated_facts (
  id bigint generated always as identity primary key,
  species_id text not null,
  kind text not null,
  value text not null,
  source_url text not null,
  verified_at date not null,
  verified_by text not null,
  status text not null,
  notes text not null,
  unique (species_id, kind, value, source_url)
);
```

The base species list is generated, not typed by hand:

```bash
cd backend && uv run python -m scripts.refresh_base_catalog
```

That downloads the PvPoke gamemaster and two PokéAPI CSVs, and nothing else.
Curated shiny and Dynamax rows ship in `backend/data/go_curated_seed.json`.
What was checked, and what was left out, is in `docs/go-curated-seed.md`.

Demo trainers for the trade page:

```bash
cd backend && uv run python -m scripts.seed_trade_demo
```

The four emails end in `@demo.test` and the password is `demo-password`.
Avery and Jordan in Toronto overlap. Sam is in Montreal. Riley does not
overlap with Avery.

## Checks

```bash
cd backend && uv run pytest
cd backend && uv run ruff check . && uv run ruff format --check .
cd frontend && npm run build && npm run lint
cd frontend && node --test tests/*.mjs
```

`tests/answer-markdown.test.mjs` fails here the same way it fails in the
personal app: the test still calls `AgentRunPanel` with flat props, and the
component now expects a `run` object. That failure is not caused by this
edition.

`ruff format --check` also reports the same four files as the personal
tree: `data/dex.py`, `data/fetch_dex.py`, `tests/test_dex.py`, and
`tools/matchups.py`. `ruff check` is clean.

## Split it into its own repo later

From the personal repository, on a clean commit:

```bash
git subtree split --prefix=commercial -b commercial-split
```

That branch has `commercial/` as its root: `backend/` and `frontend/` sit
at the top, and this README is the repository README. Push it into a new
empty repository:

```bash
git remote add commercial-edition <new-repo-url>
git push commercial-edition commercial-split:main
```

After the new repository has the history, the personal repo can delete the
`commercial-split` branch. Further fixes do not flow across by themselves.
