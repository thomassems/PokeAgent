# Jev Tool-Routing Results

This directory stores committed snapshots from the local Jev classification
experiment. A snapshot is evidence from one model version and fixture version;
it does not enable Jev in either runtime agent.

From `backend/`, run:

```bash
uv run --env-file ../.env python -m evals.run_jev_tool_selection
```

The runner records aggregate and per-case accuracy, probabilities, confidence,
latency, token usage, and reported cost. It never stores the API key.
