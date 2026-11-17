"""The GO guides corpus, the upload payload, and the type helper."""

from data.go_guides import GO_GUIDE_RECORDS, GO_GUIDE_TOPICS
from evals.loader import go_tool_selection_cases
from scripts.index_go_guides import NAMESPACE, pinecone_record
from tools.go_types import go_type_roles


def test_guides_are_unique_authored_summaries() -> None:
    ids = [record.id for record in GO_GUIDE_RECORDS]
    assert len(ids) == len(set(ids))
    assert len(GO_GUIDE_RECORDS) <= 12
    for record in GO_GUIDE_RECORDS:
        assert record.dataset_version == "go-guides-v1"
        assert record.topic in GO_GUIDE_TOPICS
        assert record.source_kind == "pokeagent-authored"
        assert record.license
        assert "\u2014" not in record.chunk_text


def test_upload_payload_drops_repository_only_fields() -> None:
    assert NAMESPACE == "go-guides-v1"
    payload = pinecone_record(GO_GUIDE_RECORDS[0])
    assert payload["_id"] == GO_GUIDE_RECORDS[0].id
    assert "id" not in payload
    assert "license" not in payload
    assert "discovery_urls" not in payload
    assert "chunk_text" in payload


def test_pawniard_candy_types_are_not_its_weaknesses() -> None:
    result = go_type_roles(["Dark", "Steel"])
    assert result["candy_bonus_types"] == ["dark", "steel"]
    by_type = {row["type"]: row["multiplier"] for row in result["super_effective"]}
    assert by_type["fighting"] == 4
    assert by_type["ground"] == 2
    assert by_type["fire"] == 2
    assert "fairy" not in by_type
    assert "bug" not in by_type


def test_unknown_type_is_an_error() -> None:
    assert "error" in go_type_roles(["shadow"])
    assert "error" in go_type_roles([])
    assert "error" in go_type_roles("dark")  # type: ignore[arg-type]


def test_phase_2_eval_rows_name_the_guide_tool() -> None:
    cases = {case.id: case for case in go_tool_selection_cases()}
    assert set(cases) == {
        "go-quick-catch-uses-guides",
        "go-candy-xl-uses-guides",
        "go-community-day-mega-candy",
        "go-egg-pool-uses-eggs",
        "go-research-shiny-uses-research",
        "go-giovanni-uses-rockets",
    }
    assert cases["go-quick-catch-uses-guides"].expect_tools == ["search_go_guides"]
    assert "web_search" in cases["go-quick-catch-uses-guides"].forbid_tools
    pawniard = cases["go-community-day-mega-candy"]
    assert pawniard.expect_tools == ["get_current_events", "search_go_guides"]
    assert "web_search" in pawniard.forbid_tools
    assert "today" not in pawniard.prompt.lower()
    assert cases["go-egg-pool-uses-eggs"].expect_tools == ["get_egg_pool"]
    assert cases["go-research-shiny-uses-research"].expect_tools == [
        "get_research_rewards"
    ]
    assert cases["go-giovanni-uses-rockets"].expect_tools == ["get_rocket_lineups"]
