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

---

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
