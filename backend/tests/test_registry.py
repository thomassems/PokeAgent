"""The model-facing tool layer: normalisation, misses, and payload shaping."""

from data.dex import POKEMON
from llm.tools.registry import (
    TOOL_FUNCTIONS,
    TOOLS,
    get_move,
    get_pokemon,
    get_type_effectiveness,
    get_type_matchups,
)


def test_names_are_normalised_before_lookup() -> None:
    # A model will send any of these for the id "rotom-wash".
    for sent in ("Rotom-Wash", "rotom wash", "  ROTOM WASH  "):
        assert get_pokemon([sent])[sent]["name"] == "Rotom"


def test_unknown_pokemon_reports_a_miss_rather_than_raising() -> None:
    result = get_pokemon(["Missingno"])["Missingno"]
    assert isinstance(result, str)
    assert "does not exist" in result


def test_results_are_keyed_by_what_was_asked_for() -> None:
    # Keyed by the request, not the canonical id, so the model can match its
    # input to its output without translating.
    result = get_pokemon(["rotom wash", "Garchomp"])
    assert set(result) == {"rotom wash", "Garchomp"}


def test_moves_are_excluded_by_default() -> None:
    record = get_pokemon(["Garchomp"])["Garchomp"]
    assert "moves" not in record
    assert record["move_count"] == len(POKEMON["garchomp"]["moves"])


def test_include_moves_returns_the_list() -> None:
    record = get_pokemon(["Garchomp"], include_moves=True)["Garchomp"]
    assert record["moves"] == POKEMON["garchomp"]["moves"]


def test_trimming_does_not_mutate_the_shared_dex() -> None:
    # POKEMON is loaded once per process. Trimming in place would delete the
    # movepool for every later call, including include_moves=True ones.
    before = len(POKEMON["garchomp"]["moves"])
    get_pokemon(["Garchomp"])
    assert len(POKEMON["garchomp"]["moves"]) == before
    assert get_pokemon(["Garchomp"], include_moves=True)["Garchomp"]["moves"]


def test_include_moves_does_not_return_the_shared_dex_record() -> None:
    record = get_pokemon(["Garchomp"], include_moves=True)["Garchomp"]
    record["moves"].clear()
    assert POKEMON["garchomp"]["moves"]


def test_move_names_are_normalised() -> None:
    assert get_move(["Stone Edge"])["Stone Edge"]["type"] == "rock"


def test_unknown_move_reports_a_miss() -> None:
    assert "does not exist" in get_move(["Nonsense Beam"])["Nonsense Beam"]


def test_move_lookup_does_not_return_the_shared_dex_record() -> None:
    record = get_move(["Stone Edge"])["Stone Edge"]
    record["power"] = 1
    assert get_move(["Stone Edge"])["Stone Edge"]["power"] == 100


def test_matchups_multiply_across_both_types() -> None:
    # Ferrothorn is grass/steel, so Fire is 2x twice over. Returning raw rows and
    # leaving the model to multiply is exactly what this replaced.
    entry = get_type_matchups(["Ferrothorn"], "defending")["matchups"]["Ferrothorn"]
    assert entry["defending"]["4"] == ["fire"]
    assert "fighting" in entry["defending"]["2"]


def test_attacking_matchups_use_best_stab_not_product() -> None:
    # Swampert has Water and Ground STAB. Both hit Fire super effectively, but a
    # Pokemon uses one move at a time, so this is 2x coverage rather than 4x.
    entry = get_type_matchups(["Swampert"], "attacking")["matchups"]["Swampert"]
    assert "fire" in entry["attacking"]["2"]
    assert "4" not in entry["attacking"]


def test_attacking_immunity_does_not_hide_other_stab_options() -> None:
    # Dragon does nothing to Fairy, but Garchomp's Ground STAB hits Fairy
    # neutrally, so Fairy should be omitted as neutral rather than listed as 0.
    entry = get_type_matchups(["Garchomp"], "attacking")["matchups"]["Garchomp"]
    listed = {t for types in entry["attacking"].values() for t in types}
    assert "fairy" not in listed


def test_immunity_beats_any_number_of_weaknesses() -> None:
    # Electric is normally 2x into Flying, but Ground is immune, so the product is 0.
    entry = get_type_matchups(["Gliscor"], "defending")["matchups"]["Gliscor"]
    assert "electric" in entry["defending"]["0"]


def test_neutral_types_are_omitted() -> None:
    entry = get_type_matchups(["Snorlax"], "defending")["matchups"]["Snorlax"]
    listed = {t for types in entry["defending"].values() for t in types}
    assert "water" not in listed, "neutral carries no information and is dropped"


def test_matchups_report_the_generation_used() -> None:
    assert get_type_matchups(["Garchomp"], "defending")["generation"] == 9


def test_matchups_accept_a_generation() -> None:
    gen4 = get_type_matchups(["Registeel"], "defending", generation=4)
    gen6 = get_type_matchups(["Registeel"], "defending", generation=6)
    assert "ghost" in gen4["matchups"]["Registeel"]["defending"]["0.5"]
    assert "ghost" not in {
        attack_type
        for types in gen6["matchups"]["Registeel"]["defending"].values()
        for attack_type in types
    }


def test_type_effectiveness_reads_raw_generation_chart() -> None:
    gen4 = get_type_effectiveness("ghost", "steel", generation=4)
    gen6 = get_type_effectiveness("ghost", "steel", generation=6)
    assert gen4["multiplier"] == 0.5
    assert gen6["multiplier"] == 1.0


def test_type_effectiveness_keeps_zero_and_neutral_distinct() -> None:
    immune = get_type_effectiveness("electric", "ground")
    neutral = get_type_effectiveness("fire", "normal")
    assert immune["multiplier"] == 0.0
    assert neutral["multiplier"] == 1.0


def test_ability_the_pokemon_can_have_returns_its_effect() -> None:
    entry = get_type_matchups(["Flygon"], "defending", "Levitate")["matchups"]["Flygon"]
    assert entry["ability"]["name"] == "Levitate"
    assert entry["ability"]["effect"] == "Evades Ground moves."
    assert "ability_warning" not in entry


def test_ability_the_pokemon_cannot_have_warns() -> None:
    result = get_type_matchups(["Garchomp"], "defending", "Levitate")
    entry = result["matchups"]["Garchomp"]
    assert "cannot have Levitate" in entry["ability_warning"]


def test_unknown_ability_errors() -> None:
    assert "error" in get_type_matchups(["Garchomp"], "defending", "Super Speed")


def test_invalid_direction_is_reported() -> None:
    assert "error" in get_type_matchups(["Garchomp"], "sideways")


def test_unknown_pokemon_in_matchups_reports_a_miss() -> None:
    entry = get_type_matchups(["Missingno"], "defending")["matchups"]["Missingno"]
    assert "error" in entry


def test_every_schema_matches_its_function_signature() -> None:
    """Guards the convention that lets the loop splat tool input straight in.

    A mismatch is a TypeError at the worst possible moment: mid-run, after the
    model has already paid for the call.
    """
    import inspect

    for tool in TOOLS:
        properties = set(tool["input_schema"]["properties"])
        parameters = set(inspect.signature(TOOL_FUNCTIONS[tool["name"]]).parameters)
        assert properties <= parameters, tool["name"]


def test_schemas_and_dispatch_map_agree() -> None:
    assert {tool["name"] for tool in TOOLS} == set(TOOL_FUNCTIONS)


def test_required_schema_fields_are_real_parameters() -> None:
    import inspect

    for tool in TOOLS:
        required = set(tool["input_schema"].get("required", []))
        parameters = set(inspect.signature(TOOL_FUNCTIONS[tool["name"]]).parameters)
        assert required <= parameters, tool["name"]
