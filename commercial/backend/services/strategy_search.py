"""Strategy retrieval backed by Pinecone integrated inference."""

import os
from typing import Any

from pinecone import Pinecone
from pinecone.exceptions import PineconeException
from pydantic import BaseModel, Field

_INDEX_NAME = "pokeagent-strategy"
_NAMESPACE = "strategy-v1"
_RERANK_MODEL = "bge-reranker-v2-m3"
_MAX_QUERY_CHARS = 500
_MAX_RESULTS = 10
_CANDIDATE_COUNT = 15
_RETURN_FIELDS = [
    "chunk_text",
    "title",
    "pokemon",
    "generation",
    "format",
    "battle_style",
    "topic",
    "game",
    "source_kind",
    "source_name",
    "source_url",
    "source_updated_at",
    "dataset_version",
]


class StrategyHit(BaseModel):
    id: str
    text: str
    title: str
    score: float
    pokemon: list[str]
    generation: int
    format: str
    topic: str
    source_kind: str
    source_name: str
    source_url: str | None = None


class StrategySearchUsage(BaseModel):
    embed_total_tokens: int | None = None
    read_units: int | None = None
    rerank_units: int | None = None


class StrategySearchResult(BaseModel):
    query: str
    generation: int
    results: list[StrategyHit] = Field(default_factory=list)
    usage: StrategySearchUsage | None = None
    error: str | None = None


def _index() -> Any:
    return Pinecone().Index(os.getenv("PINECONE_STRATEGY_INDEX", _INDEX_NAME))


def _metadata_filter(
    generation: int,
    format: str | None,
    pokemon: list[str] | None,
) -> dict[str, Any]:
    filters: dict[str, Any] = {"generation": {"$eq": generation}}
    if format:
        filters["format"] = {"$eq": format.strip().lower()}
    if pokemon:
        filters["pokemon"] = {
            "$in": [name.strip().lower().replace(" ", "-") for name in pokemon]
        }
    return filters


def _parse_hits(payload: dict[str, Any]) -> list[StrategyHit]:
    hits = payload.get("result", {}).get("hits", [])
    parsed = []
    for hit in hits:
        fields = hit.get("fields", {})
        parsed.append(
            StrategyHit(
                id=hit.get("id_", hit.get("_id", "")),
                text=fields.get("chunk_text", ""),
                title=fields.get("title", ""),
                score=hit.get("score_", hit.get("_score", 0.0)),
                pokemon=fields.get("pokemon", []),
                generation=fields.get("generation"),
                format=fields.get("format", ""),
                topic=fields.get("topic", ""),
                source_kind=fields.get("source_kind", ""),
                source_name=fields.get("source_name", ""),
                source_url=fields.get("source_url"),
            )
        )
    return parsed


def search_strategy(
    query: str,
    generation: int,
    format: str | None = None,
    pokemon: list[str] | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Retrieve generation-specific strategy passages and rerank them."""
    query = query.strip()[:_MAX_QUERY_CHARS]
    result_limit = max(1, min(limit, _MAX_RESULTS))
    if not os.environ.get("PINECONE_API_KEY"):
        return StrategySearchResult(
            query=query,
            generation=generation,
            error="Strategy search is not configured.",
        ).model_dump(mode="json", exclude_none=True)

    try:
        response = _index().search(
            namespace=_NAMESPACE,
            inputs={"text": query},
            top_k=max(_CANDIDATE_COUNT, result_limit),
            filter=_metadata_filter(generation, format, pokemon),
            fields=_RETURN_FIELDS,
            rerank={
                "model": _RERANK_MODEL,
                "rank_fields": ["chunk_text"],
                "top_n": result_limit,
            },
        )
        payload = response.to_dict()
    except PineconeException as exc:
        print(f"[services.strategy_search] request failed: {type(exc).__name__}: {exc}")
        return StrategySearchResult(
            query=query,
            generation=generation,
            error="Strategy search failed. Try again or answer without it.",
        ).model_dump(mode="json", exclude_none=True)

    usage = payload.get("usage") or None
    return StrategySearchResult(
        query=query,
        generation=generation,
        results=_parse_hits(payload),
        usage=StrategySearchUsage.model_validate(usage) if usage else None,
    ).model_dump(mode="json", exclude_none=True)
