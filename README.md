# PokeAgent

A benchmark disguised as a Pokemon team builder. Two agent implementations - one
hand-rolled, one built on LangChain - solve the same open-ended team-building
problems against the same tools, and the app streams both traces side by side so
they can be compared on outcome quality, step count, latency, and cost.

Scope is Generation 4 only. See [CLAUDE.md](CLAUDE.md) for the working agreement
and architecture rules, and [docs/decisions.md](docs/decisions.md) for the
decision log.

## Layout

```
frontend/    Next.js 16 (TypeScript, Tailwind, App Router)
backend/     FastAPI (Python 3.12)
  api/         routes, SSE streaming, request/response models
  agents/      the two implementations plus the protocol they share
  tools/       pure, deterministic functions over data/
  data/        baked Gen 4 JSON plus the one-time fetch script
  evals/       agent runs - slow, nondeterministic, on demand
  tests/       unit tests
```

Dependencies point inward: `api/ -> agents/ -> tools/ -> data/`.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Node 22+.

```bash
# backend - creates .venv and installs from uv.lock
cd backend && uv sync

# frontend
cd frontend && npm install

# secrets
cp .env.example .env.local   # then fill it in; .env.local is gitignored
```

## Running locally

Two processes. The frontend proxies `/api/*` to the backend via a rewrite in
`frontend/next.config.ts`, so the browser only ever talks to port 3000 and there
is no CORS to configure.

```bash
# terminal 1
cd backend && uv run uvicorn api.main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev
```

Open http://localhost:3000. The page renders the payload from `/api/health`,
which fails visibly if the backend is not up.

FastAPI's generated docs are at http://localhost:8000/docs.

## Checks

```bash
cd backend  && uv run pytest
cd backend  && uv run ruff check . && uv run ruff format --check .
cd frontend && npm run build && npm run lint
```

## Deployment

One Vercel project, two services, configured in [vercel.json](vercel.json).
Vercel builds `frontend/` and `backend/` independently and routes `/api/*` to the
backend, everything else to the frontend. The Python entrypoint is declared as
`api.main:app` in `backend/pyproject.toml`.

Not yet deployed - see the open questions in `docs/decisions.md` before the first
deploy.
