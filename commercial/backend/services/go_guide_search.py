"""Pokemon GO guide retrieval backed by Pinecone integrated inference.

Same index and embedding field as strategy search. A different namespace,
so a GO mechanic is not retrieved as main-series advice.
"""

import os
from typing import Any

from pinecone import Pinecone
from pinecone.exceptions import PineconeException
from pydantic import BaseModel, Field

_INDEX_NAME = "pokeagent-strategy"
_NAMESPACE = "go-guides-v1"
_RERANK_MODEL = "bge-reranker-v2-m3"
_MAX_QUERY_CHARS = 500
_MAX_RESULTS = 10
_CANDIDATE_COUNT = 12
_RETURN_FIELDS = [
    "chunk_text",
    "title",
    "pokemon",
    "topic",
    "source_kind",
    "source_name",
    "source_url",
    "source_updated_at",
    "dataset_version",
]


class GoGuideHit(BaseModel):
    id: str
    text: str
    title: str
    score: float
    topic: str
    pokemon: list[str] = Field(default_factory=list)
    source_kind: str
    source_name: str
    source_url: str | None = None


class GoGuideSearchUsage(BaseModel):
    embed_total_tokens: int | None = None
    read_units: int | None = None
    rerank_units: int | None = None


class GoGuideSearchResult(BaseModel):
    query: str
    topic: str | None = None
    results: list[GoGuideHit] = Field(default_factory=list)
    usage: GoGuideSearchUsage | None = None
    error: str | None = None


def _index() -> Any:
    return Pinecone().Index(os.getenv("PINECONE_STRATEGY_INDEX", _INDEX_NAME))


def _parse_hits(payload: dict[str, Any]) -> list[GoGuideHit]:
    hits = payload.get("result", {}).get("hits", [])
    parsed = []
    for hit in hits:
        fields = hit.get("fields", {})
        parsed.append(
            GoGuideHit(
                id=hit.get("id_", hit.get("_id", "")),
                text=fields.get("chunk_text", ""),
                title=fields.get("title", ""),
                score=hit.get("score_", hit.get("_score", 0.0)),
                topic=fields.get("topic", ""),
                pokemon=fields.get("pokemon", []),
                source_kind=fields.get("source_kind", ""),
                source_name=fields.get("source_name", ""),
                source_url=fields.get("source_url"),
            )
        )
    return parsed


def search_go_guides(
    query: str,
    topic: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Retrieve evergreen GO mechanics and rerank them. No generation filter."""
    query = query.strip()[:_MAX_QUERY_CHARS]
    result_limit = max(1, min(limit, _MAX_RESULTS))
    if not os.environ.get("PINECONE_API_KEY"):
        return GoGuideSearchResult(
            query=query,
            topic=topic,
            error="GO guide search is not configured.",
        ).model_dump(mode="json", exclude_none=True)

    search_kwargs: dict[str, Any] = {
        "namespace": _NAMESPACE,
        "inputs": {"text": query},
        "top_k": max(_CANDIDATE_COUNT, result_limit),
        "fields": _RETURN_FIELDS,
        "rerank": {
            "model": _RERANK_MODEL,
            "rank_fields": ["chunk_text"],
            "top_n": result_limit,
        },
    }
    if topic:
        search_kwargs["filter"] = {"topic": {"$eq": topic}}

    try:
        payload = _index().search(**search_kwargs).to_dict()
    except PineconeException as exc:
        print(f"[services.go_guide_search] request failed: {type(exc).__name__}: {exc}")
        return GoGuideSearchResult(
            query=query,
            topic=topic,
            error="GO guide search failed. Try again or answer without it.",
        ).model_dump(mode="json", exclude_none=True)

    usage = payload.get("usage") or None
    return GoGuideSearchResult(
        query=query,
        topic=topic,
        results=_parse_hits(payload),
        usage=GoGuideSearchUsage.model_validate(usage) if usage else None,
    ).model_dump(mode="json", exclude_none=True)
