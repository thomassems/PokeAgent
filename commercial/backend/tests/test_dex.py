"""The baked dex and the per-generation type charts."""

from data.dex import (
    ABILITIES,
    ATTACKING_CHARTS,
    DEFENDING_CHARTS,
    LATEST_GENERATION,
    MOVES,
    POKEMON,
)

# Steel and Dark arrive in gen 2, Fairy in gen 6.
TYPES_BY_GENERATION = {"1": 15, "2": 17, "5": 17, "6": 18, "9": 18}


def test_every_generation_has_a_chart() -> None:
    assert sorted(ATTACKING_CHARTS, key=int) == [str(g) for g in range(1, 10)]


def test_type_count_grows_with_generation() -> None:
    for generation, expected in TYPES_BY_GENERATION.items():
        assert len(ATTACKING_CHARTS[generation]) == expected, generation


def test_fairy_only_exists_from_gen_six() -> None:
    assert "fairy" not in ATTACKING_CHARTS["5"]
    assert "fairy" in ATTACKING_CHARTS["6"]


def test_steel_resists_ghost_and_dark_before_gen_six() -> None:
    for generation in ("2", "5"):
        assert ATTACKING_CHARTS[generation]["ghost"]["steel"] == 0.5
        assert ATTACKING_CHARTS[generation]["dark"]["steel"] == 0.5
    for generation in ("6", "9"):
        assert "steel" not in ATTACKING_CHARTS[generation]["ghost"]
        assert "steel" not in ATTACKING_CHARTS[generation]["dark"]


def test_gen_one_quirks() -> None:
    gen1 = ATTACKING_CHARTS["1"]
    assert gen1["poison"]["bug"] == 2.0
    assert gen1["ghost"]["psychic"] == 0.0
    # Ice into Fire was neutral in gen 1, so it must be absent rather than 0.5.
    assert "fire" not in gen1["ice"]
    assert ATTACKING_CHARTS["9"]["ice"]["fire"] == 0.5

# test makes sure neutral matchups are represented by absence not by storing
# something like "nomrla":1.0
def test_neutral_pairs_are_absent_not_stored() -> None:
    assert "normal" not in ATTACKING_CHARTS["9"]["fire"]


def test_immunity_is_zero_not_missing() -> None:
    # A falsy check would collapse this into neutral and quietly lose immunities.
    assert ATTACKING_CHARTS["9"]["electric"]["ground"] == 0.0
    assert ATTACKING_CHARTS["9"]["dragon"]["fairy"] == 0.0


def test_defending_chart_is_a_faithful_inversion() -> None:
    for generation, chart in ATTACKING_CHARTS.items():
        for attacker, row in chart.items():
            for defender, multiplier in row.items():
                assert DEFENDING_CHARTS[generation][defender][attacker] == multiplier


def test_dual_type_multiplication() -> None:
    defending = DEFENDING_CHARTS["9"]
    # Garchomp is dragon/ground: 2x from ice twice over, and immune to electric.
    assert defending["dragon"]["ice"] * defending["ground"].get("ice", 1.0) == 4.0
    electric = defending["dragon"].get("electric", 1.0)
    assert electric * defending["ground"]["electric"] == 0.0


def test_species_stored_only_as_a_form_resolve_by_plain_name() -> None:
    # Upstream has no "mimikyu", only "mimikyu-disguised". Same for 36 others.
    for name in ("mimikyu", "aegislash", "giratina", "darmanitan"):
        assert name in POKEMON, name


def test_aliases_point_at_the_default_form() -> None:
    assert POKEMON["mimikyu"]["types"] == ["ghost", "fairy"]


def test_forms_without_an_upstream_learnset_inherit_one() -> None:
    heatran_mega = POKEMON["heatran-mega"]
    assert heatran_mega["moves"], "an empty list reads as 'learns nothing'"
    assert heatran_mega["moves_inherited_from"] == "heatran"


def test_records_carry_the_fields_the_tools_advertise() -> None:
    garchomp = POKEMON["garchomp"]
    fields = ("name", "types", "stats", "generation", "is_legendary", "is_mythical")
    for field in fields:
        assert field in garchomp, field
    assert garchomp["stats"]["total"] == 600


def test_abilities_carry_effect_text() -> None:
    # "Levitate" alone tells a model nothing; the effect is why it is stored.
    assert ABILITIES["levitate"]["effect"]


def test_status_moves_have_no_power() -> None:
    assert MOVES["swords-dance"]["power"] is None
    assert MOVES["earthquake"]["power"] == 100


def test_latest_generation_is_a_real_chart() -> None:
    assert LATEST_GENERATION in ATTACKING_CHARTS
