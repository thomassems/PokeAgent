"""Web search, backed by the Brave Search API.

This lives in `services/` rather than `tools/` because it crosses the network.
That is the whole reason this directory exists: `tools/` keeps its no-network,
no-I/O purity rule, and anything that has to reach the outside world sits here
where being unpure and mock-dependent is expected rather than a violation.

Switching provider (Tavily, Serper, Exa) means changing _ENDPOINT, the auth
header, and _parse. The rest of this module is provider agnostic.
"""

import os
from typing import Any

import httpx2

_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
_TIMEOUT_SECONDS = 10.0

# A search query is inherently free-form text, which is in tension with the rule
# in CLAUDE.md that tools take constrained inputs. It is bounded here instead:
# the query is sent as an encoded query parameter, never interpolated into a
# path or a URL, and its length is capped so one call cannot become a large
# outbound request.
_MAX_QUERY_CHARS = 400

# Snippets are third-party text that ends up in the model's context. Capping the
# length bounds both token spend and how much untrusted prose arrives per call.
_MAX_SNIPPET_CHARS = 300

_MAX_RESULTS_ALLOWED = 10


def _parse(payload: dict[str, Any], limit: int) -> list[dict[str, str]]:
    """Pull the fields worth showing a model out of a Brave response."""
    results = payload.get("web", {}).get("results", [])
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", "")[:_MAX_SNIPPET_CHARS],
        }
        for item in results[:limit]
    ]


def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search the web and return titles, urls and snippets.

    Returns a dict carrying either `results` or `error`, never raising, so a
    failed search is something the agent can read and recover from rather than
    an exception that ends the run. The error text is deliberately short and
    free of provider detail, since it reaches the model and may reach the user.
    """
    query = query.strip()[:_MAX_QUERY_CHARS]
    limit = max(1, min(max_results, _MAX_RESULTS_ALLOWED))

    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return {"query": query, "error": "Web search is not configured."}

    try:
        response = httpx2.get(
            _ENDPOINT,
            params={"q": query, "count": limit},
            headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            timeout=httpx2.Timeout(_TIMEOUT_SECONDS),
        )
        response.raise_for_status()
    except httpx2.HTTPError as exc:
        # Logged with detail, reported without it. Raw provider errors and URLs
        # stay out of anything the model or the browser sees.
        print(f"[services.search] request failed: {type(exc).__name__}: {exc}")
        return {
            "query": query,
            "error": "Web search failed. Try again or answer without it.",
        }

    return {"query": query, "results": _parse(response.json(), limit)}
