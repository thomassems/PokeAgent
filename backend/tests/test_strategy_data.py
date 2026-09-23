"""Validation for the canonical strategy corpus that will feed Pinecone."""

from data.strategy import STRATEGY_RECORDS


def test_seed_corpus_has_unique_stable_ids() -> None:
    ids = [record.id for record in STRATEGY_RECORDS]
    assert len(ids) == len(set(ids))
    assert all(record.id == record.id.lower() for record in STRATEGY_RECORDS)


def test_filter_metadata_is_normalised() -> None:
    for record in STRATEGY_RECORDS:
        assert record.format == record.format.lower()
        assert record.game == record.game.lower()
        assert all(name == name.lower() for name in record.pokemon)
        assert record.source_kind == "pokeagent-authored"


def test_seed_corpus_exercises_generation_and_topic_filters() -> None:
    assert {record.generation for record in STRATEGY_RECORDS} == {4, 9}
    assert {record.battle_style for record in STRATEGY_RECORDS} == {"singles"}
    assert {record.topic for record in STRATEGY_RECORDS} >= {
        "archetype",
        "counter",
        "gameplan",
        "moveset",
        "role",
        "teammate",
    }


def test_seed_corpus_is_explicitly_versioned() -> None:
    assert {record.dataset_version for record in STRATEGY_RECORDS} == {"strategy-v1"}


def test_expansion_includes_attributed_sources_and_general_archetypes() -> None:
    assert len(STRATEGY_RECORDS) >= 31
    assert any(record.source_url for record in STRATEGY_RECORDS)
    assert any(record.discovery_urls for record in STRATEGY_RECORDS)
    assert any(
        record.topic == "archetype" and not record.pokemon
        for record in STRATEGY_RECORDS
    )


def test_forum_discovery_records_have_a_stronger_verification_source() -> None:
    discovered = [record for record in STRATEGY_RECORDS if record.discovery_urls]
    assert discovered
    assert all(
        record.source_url and "smogon.com" in record.source_url for record in discovered
    )
