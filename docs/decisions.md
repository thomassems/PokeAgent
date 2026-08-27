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
nesting buys room for shared packages that this project will not grow — CLAUDE.md
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
directories — a `vercel.json` change, not a restructure.

## 3. Python toolchain: uv, Python 3.12, non-package layout

`uv` per CLAUDE.md. Python 3.12 is pinned in `backend/.python-version`; it is both
CLAUDE.md's stated version and Vercel's default, so dev and prod agree.

`[tool.uv] package = false` marks the backend an application rather than a
library, so its modules stay as local source instead of being installed into the
environment. That requires `pythonpath = ["."]` under `[tool.pytest.ini_options]`
for `from api.main import app` to resolve — the two settings go together.

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
command already covers the need — `next dev` supports rewrites natively. It also
requires the Vercel CLI and couples the inner loop to a feature whose plan
availability is unconfirmed. It stays available for a routing sanity-check before
the first deploy.

The rewrite is guarded with `if (process.env.NODE_ENV === "production") return []`
so it cannot shadow Vercel's own route table in production.

---

## Open questions

Not decided. Each needs its own proposal before code depends on it.

- **`tools/` cannot literally do "no I/O."** CLAUDE.md says `tools/` performs no
  I/O, but `tools/` has to read the baked Gen 4 JSON out of `data/`. Candidates:
  load once at import into a module-level constant, generate a `.py` data module
  at build time, or read the rule as "no I/O per call." Resolve when there is data
  to load.
- **Post-rewrite path handling on Vercel is unverified.** Whether the backend
  service receives `/api/health` or `/health` after the rewrite has not been
  checked against a real deploy. FastAPI routes carry the `/api` prefix in the
  path itself, which survives either answer, but this needs confirming.
- **`httpx` vs `httpx2`.** Starlette 1.6 emits a deprecation warning saying
  `TestClient` wants `httpx2`. `httpx` works today and the test passes; swapping
  is a dependency change and has not been made.
