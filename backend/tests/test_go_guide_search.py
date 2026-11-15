"""GO guide retrieval without calling Pinecone."""

from typing import Any

from services import go_guide_search
from services.go_guide_search import search_go_guides


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
    result = search_go_guides("How do I quick catch?")
    assert result["error"] == "GO guide search is not configured."
    assert result["results"] == []


def test_search_uses_the_guides_namespace_and_optional_topic(monkeypatch) -> None:
    payload = {
        "result": {
            "hits": [
                {
                    "id_": "go-quick-catch",
                    "score_": 0.8,
                    "fields": {
                        "chunk_text": "Hold the berry button, throw, then flee.",
                        "title": "Quick catch shortcut",
                        "topic": "catching",
                        "pokemon": [],
                        "source_kind": "pokeagent-authored",
                        "source_name": "PokeAgent GO guides",
                    },
                }
            ]
        },
        "usage": {"embed_total_tokens": 4, "read_units": 1, "rerank_units": 1},
    }
    fake_index = FakeIndex(payload)
    monkeypatch.setenv("PINECONE_API_KEY", "test-key")
    monkeypatch.setattr(go_guide_search, "_index", lambda: fake_index)

    result = search_go_guides("  quick catch  ", topic="catching", limit=3)

    assert result["results"][0]["id"] == "go-quick-catch"
    assert result["results"][0]["title"] == "Quick catch shortcut"
    assert fake_index.search_kwargs["namespace"] == "go-guides-v1"
    assert fake_index.search_kwargs["inputs"] == {"text": "quick catch"}
    assert fake_index.search_kwargs["filter"] == {"topic": {"$eq": "catching"}}
    assert fake_index.search_kwargs["rerank"]["top_n"] == 3
    assert "generation" not in fake_index.search_kwargs
