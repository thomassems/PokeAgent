"""find_pokemon: filtering, sorting and the caps around them."""

from data.dex import POKEMON
from tools.dex_query import MAX_LIMIT, find_pokemon


def names(result: dict) -> list[str]:
    return [entry["name"] for entry in result["pokemon"]]


def deduped_names_matching(**filters: object) -> set[str]:
    found: set[str] = set()
    for record in POKEMON.values():
        if all(record.get(key) == value for key, value in filters.items()):
            found.add(record["name"])
    return found


def test_no_filters_returns_the_whole_dex_deduped() -> None:
    result = find_pokemon(limit=MAX_LIMIT)
    # Aliases and forms mean one Pokemon appears under several ids.
    assert result["count"] == len({record["name"] for record in POKEMON.values()})


def test_types_filter_requires_all_listed_types() -> None:
    duals = find_pokemon(types=["dragon", "ground"], limit=MAX_LIMIT)
    singles = find_pokemon(types=["dragon"], limit=MAX_LIMIT)
    assert "Garchomp" in names(duals)
    assert duals["count"] < singles["count"], "two types must narrow, not widen"


def test_type_filter_is_case_and_space_insensitive() -> None:
    spaced = find_pokemon(types=[" DRAGON "])["count"]
    assert spaced == find_pokemon(types=["dragon"])["count"]


def test_generation_filter() -> None:
    gen4 = find_pokemon(generation=4, limit=MAX_LIMIT)
    # Count is deduped the same way find_pokemon dedupes: by display name after
    # filtering, so alternate forms do not inflate the expected total.
    assert gen4["count"] == len(deduped_names_matching(generation=4))
    assert "Garchomp" in names(gen4)
    assert "Charizard" not in names(gen4)


def test_legendary_filter_separates_from_mythical() -> None:
    legendary = deduped_names_matching(is_legendary=True)
    mythical = deduped_names_matching(is_mythical=True)
    legendary_result = find_pokemon(is_legendary=True, limit=MAX_LIMIT)
    mythical_result = find_pokemon(is_mythical=True, limit=MAX_LIMIT)
    assert legendary
    assert mythical
    assert legendary.isdisjoint(mythical)
    assert legendary_result["count"] == len(legendary)
    assert mythical_result["count"] == len(mythical)
    assert set(names(legendary_result)) <= legendary
    assert set(names(mythical_result)) <= mythical


def test_filters_combine_with_and() -> None:
    result = find_pokemon(is_legendary=True, generation=4, limit=MAX_LIMIT)
    assert result["count"] < find_pokemon(is_legendary=True, limit=MAX_LIMIT)["count"]
    assert result["count"] < find_pokemon(generation=4, limit=MAX_LIMIT)["count"]


def test_results_are_sorted_descending_by_the_requested_stat() -> None:
    result = find_pokemon(types=["dragon"], sort_by="speed", limit=10)
    speeds = [entry["speed"] for entry in result["pokemon"]]
    assert speeds == sorted(speeds, reverse=True)


def test_sorting_picks_the_best_form_before_deduping_by_name() -> None:
    result = find_pokemon(types=["psychic"], sort_by="speed", limit=1)
    [fastest] = result["pokemon"]
    assert fastest["name"] == "Deoxys"
    assert fastest["id"] == "deoxys-speed"
    assert fastest["speed"] == 180


def test_sort_by_total_sums_the_six_base_stats() -> None:
    # "total" is stored with the other stats so filtering/sorting code does not
    # have to recompute it for every candidate.
    #
    # Resolve by name *and* typing. Several species have forms that differ in
    # both, and the filter matched a specific one: asking for dragons returns
    # Necrozma's Ultra form, not the psychic-only base form of the same name.
    wanted = {"dragon"}
    for entry in find_pokemon(types=list(wanted), sort_by="total", limit=5)["pokemon"]:
        record = POKEMON[entry["id"]]
        expected = sum(
            record["stats"][stat]
            for stat in (
                "hp",
                "attack",
                "defense",
                "special_attack",
                "special_defense",
                "speed",
            )
        )
        assert record["stats"]["total"] == expected
        assert entry["total"] == record["stats"]["total"]


def test_limit_is_clamped_at_both_ends() -> None:
    # Too-large limits are capped to keep tool payloads bounded. Too-small
    # limits still return one result, because asking for zero is not useful to a
    # model trying to answer a question.
    assert find_pokemon(limit=9999)["returned"] == MAX_LIMIT
    assert find_pokemon(limit=0)["returned"] == 1


def test_count_reports_matches_not_the_page() -> None:
    # returned is the page size. count is the full number of matches, so the
    # caller knows there are more candidates than the first page contains.
    result = find_pokemon(types=["dragon"], limit=3)
    assert result["returned"] == 3
    assert result["count"] > 3, "count is the full match set, not what was returned"


def test_unknown_sort_key_errors_rather_than_returning_nothing() -> None:
    # The model may invent a stat-like field. Returning an explicit error is
    # easier to recover from than returning an empty list that looks like "no
    # Pokemon matched".
    result = find_pokemon(sort_by="luck")
    assert "error" in result
    assert "pokemon" not in result


def test_results_have_no_duplicate_names() -> None:
    found = names(find_pokemon(types=["dragon"], limit=MAX_LIMIT))
    assert len(found) == len(set(found))


def test_impossible_filter_returns_empty_rather_than_erroring() -> None:
    result = find_pokemon(types=["normal"], is_mythical=True, generation=1)
    assert result["count"] == 0
    assert result["pokemon"] == []
