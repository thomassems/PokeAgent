"""Strategy retrieval behavior without making paid or nondeterministic calls."""

from typing import Any

from data.strategy import STRATEGY_RECORDS
from scripts.index_strategy import pinecone_record
from services import strategy_search
from services.strategy_search import search_strategy


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def to_dict(self) -> dict[str, Any]:
        return self.payload


class FakeIndex:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.search_kwargs: dict[str, Any] = {}

    def search(self, **kwargs: Any) -> FakeResponse:
        self.search_kwargs = kwargs
        return FakeResponse(self.payload)


def test_missing_api_key_returns_a_model_readable_error(monkeypatch) -> None:
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    result = search_strategy("Great Tusk hazard control", generation=9)
    assert result["error"] == "Strategy search is not configured."
    assert result["results"] == []


def test_search_filters_then_reranks_candidates(monkeypatch) -> None:
    payload = {
        "result": {
            "hits": [
                {
                    "id_": "great-tusk-role",
                    "score_": 0.91,
                    "fields": {
                        "chunk_text": "Preserve Great Tusk for hazard control.",
                        "title": "Great Tusk preservation",
                        "pokemon": ["great-tusk"],
                        "generation": 9,
                        "format": "ou",
                        "topic": "gameplan",
                        "source_kind": "pokeagent-authored",
                        "source_name": "PokeAgent seed corpus",
                    },
                }
            ]
        },
        "usage": {"embed_total_tokens": 8, "read_units": 6, "rerank_units": 1},
    }
    fake_index = FakeIndex(payload)
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    monkeypatch.setattr(strategy_search, "_index", lambda: fake_index)

    result = search_strategy(
        "  Great Tusk hazard control  ",
        generation=9,
        format="OU",
        pokemon=["Great Tusk"],
        limit=3,
    )

    assert result["results"][0]["id"] == "great-tusk-role"
    assert result["usage"]["rerank_units"] == 1
    assert fake_index.search_kwargs["inputs"] == {"text": "Great Tusk hazard control"}
    assert fake_index.search_kwargs["top_k"] == 15
    assert fake_index.search_kwargs["filter"] == {
        "generation": {"$eq": 9},
        "format": {"$eq": "ou"},
        "pokemon": {"$in": ["great-tusk"]},
    }
    assert fake_index.search_kwargs["rerank"]["top_n"] == 3


def test_pinecone_record_excludes_repository_only_license() -> None:
    source = STRATEGY_RECORDS[0].model_copy(
        update={
            "discovery_urls": ["https://www.reddit.com/r/stunfisk/example"],
            "license": "CC BY 4.0",
        }
    )
    indexed = pinecone_record(source)
    assert "discovery_urls" not in indexed
    assert "license" not in indexed
    assert indexed["source_kind"] == "pokeagent-authored"
    assert indexed["_id"] == source.id
