"""find_pokemon: filtering, sorting and the caps around them."""

from data.dex import POKEMON
from tools.dex_query import MAX_LIMIT, find_pokemon


def names(result: dict) -> list[str]:
    return [entry["name"] for entry in result["pokemon"]]


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
    assert gen4["count"] > 0
    assert "Garchomp" in names(gen4)
    assert "Charizard" not in names(gen4)


def test_legendary_filter_separates_from_mythical() -> None:
    legendary = names(find_pokemon(is_legendary=True, limit=MAX_LIMIT))
    mythical = names(find_pokemon(is_mythical=True, limit=MAX_LIMIT))
    assert "Mewtwo" in legendary and "Mew" not in legendary
    assert "Mew" in mythical and "Mewtwo" not in mythical


def test_filters_combine_with_and() -> None:
    result = find_pokemon(is_legendary=True, generation=4, limit=MAX_LIMIT)
    assert result["count"] < find_pokemon(is_legendary=True, limit=MAX_LIMIT)["count"]
    assert result["count"] < find_pokemon(generation=4, limit=MAX_LIMIT)["count"]


def test_results_are_sorted_descending_by_the_requested_stat() -> None:
    result = find_pokemon(types=["dragon"], sort_by="speed", limit=10)
    speeds = [entry["speed"] for entry in result["pokemon"]]
    assert speeds == sorted(speeds, reverse=True)


def test_sort_by_total_sums_the_six_base_stats() -> None:
    # Resolve by name *and* typing. Several species have forms that differ in
    # both, and the filter matched a specific one: asking for dragons returns
    # Necrozma's Ultra form, not the psychic-only base form of the same name.
    wanted = {"dragon"}
    for entry in find_pokemon(types=list(wanted), sort_by="total", limit=5)["pokemon"]:
        record = next(
            r
            for r in POKEMON.values()
            if r["name"] == entry["name"] and wanted <= set(r["types"])
        )
        assert entry["total"] == sum(record["stats"].values())


def test_limit_is_clamped_at_both_ends() -> None:
    assert find_pokemon(limit=9999)["returned"] == MAX_LIMIT
    assert find_pokemon(limit=0)["returned"] == 1


def test_count_reports_matches_not_the_page() -> None:
    result = find_pokemon(types=["dragon"], limit=3)
    assert result["returned"] == 3
    assert result["count"] > 3, "count is the full match set, not what was returned"


def test_unknown_sort_key_errors_rather_than_returning_nothing() -> None:
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
