# Backend Tests

These tests are the deterministic backend safety net. They run without model
calls, web requests, or other paid/non-deterministic work.

## How To Run

From `backend/`:

```bash
uv run pytest
```

`backend/pyproject.toml` sets `testpaths = ["tests"]`, so that command runs
everything in this directory.

To run one file:

```bash
uv run pytest tests/test_registry.py
```

Run the full suite before committing backend changes. Run the narrower file
while iterating on one area.

## Layout

`test_dex.py`

Checks the baked dex data and generation-specific type charts. This covers type
chart shape, historical matchup quirks, neutral-pair omission, real immunities,
dual-type multiplication examples, form aliases, inherited learnsets, required
record fields, ability effect text, move power/nullability, and the latest
generation marker.

`test_dex_query.py`

Checks `tools.dex_query.find_pokemon`. This covers filters, filter
combinations, deduping form/name results, sorting by stats, stored base stat
total, limit clamping, count versus returned page size, and erroring on unknown
sort keys.

`test_registry.py`

Checks the model-facing tool layer in `llm/tools/registry.py`. This covers name
normalisation, unknown Pokemon/move misses, payload shaping, avoiding mutation
of shared dex records, matchup bucketing, defending multiplication, attacking
same-type coverage, ability payloads/warnings, invalid inputs, and schema-to-
function signature consistency.

`test_retrieval_fixtures.py`

Checks the deterministic half of retrieval evals. It loads
`backend/evals/fixtures/retrieval.yaml` and verifies each expected answer
against the dex/tools without calling a model. If this test fails, the fixture
or data is wrong. If this passes but a live retrieval eval fails, the agent
hallucinated or chose the wrong tool.

`test_health.py`

Checks the FastAPI health endpoint response shape.

## Eval Fixtures

The files under `backend/evals/fixtures/` are not all live evals by themselves:

- `retrieval.yaml` is loaded by `test_retrieval_fixtures.py` for deterministic
  validation.
- `tool_selection.yaml` describes tool-call expectations for live agent evals.
- `team_quality.yaml` describes broader judged team-building cases for live
  agent evals.

Only the deterministic retrieval fixture check runs with `uv run pytest`.
Tool-selection and team-quality evals require the future eval runner/model call
path and should be reported separately from unit test results.

## What Belongs Here

Add tests here when the expected behavior is deterministic and can be checked
from local code/data. Examples: exact type math, dex record shape, tool schema
contracts, payload trimming, and API response shape.

Do not put slow or nondeterministic agent runs here. Those belong under
`backend/evals/` and should report distributions over multiple runs rather than
one anecdotal pass/fail.
