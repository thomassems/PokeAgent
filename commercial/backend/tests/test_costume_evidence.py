"""Costume verifier: fixtures only, no network."""

from tools.costume_evidence import (
    normalize_code,
    parse_event_codes,
    parse_sprite_names,
    verdict_for,
)
from tools.verify_costumes import apply_verdicts

_PAGE = "https://example.test/event-forms"
_POKEDEX = "https://example.test/pokedex.json"
_LIST = """
| Festive hat
|{{MSP/GO|size=80|0025Holiday2016|Pikachu}}
* Holiday 2016: December 12, 2016, a sentence that must not be stored.
{{Spritebox/GO|ndex=0025Po|name=Pikachu Pop Star (2021)|type=Electric}}
{{Spritebox/GO|ndex=0025PhD|name=Pikachu, Ph.D. (2024)|type=Electric}}
{{MSP/GO|size=80|0025FlyOkinawa|Pikachu}}
{{MSP/GO|size=80|0025BlueGoggles|Pikachu}}
{{MSP/GO|size=80|0025Costume2|Pikachu}}
{{MSP/GO|size=80|0025RedHat|Pikachu}}
"""
_SOURCES = ("pokemon-go-api pokedex", "event-form list")
_URLS = (_POKEDEX, _PAGE)


def _codes() -> dict[tuple[int, str], str]:
    return parse_event_codes(_LIST, _PAGE)


def _names() -> list[tuple[int, str, str]]:
    return parse_sprite_names(_LIST, _PAGE)


def _verdict(row: dict[str, str], **overrides: object) -> object:
    payload = {
        "pokedex": {("pikachu", row["value"])},
        "codes": _codes(),
        "names": _names(),
        "dex": 25,
        "label": row.get("label", row["value"]),
        "sibling_labels": (),
        "sibling_slugs": (row["value"],),
        "checked_sources": _SOURCES,
        "checked_urls": _URLS,
    }
    payload.update(overrides)
    return verdict_for(row, **payload)  # type: ignore[arg-type]


def test_code_normalization_keeps_ordinals_and_drops_noevolve() -> None:
    assert normalize_code("Holiday2016") == "holiday-2016"
    assert normalize_code("FLYING_OKINAWA") == "fly-okinawa"
    assert normalize_code("flying-5th-anniv") == "fly-5th-anniv"
    assert normalize_code("Fly5") == "fly-5"
    assert normalize_code("anniversary-2022-noevolve") == "anniversary-2022"


def test_parser_keeps_ids_and_drops_the_sentence() -> None:
    codes = _codes()
    assert codes[(25, "holiday-2016")] == _PAGE
    blob = " ".join(codes.values())
    assert "December" not in blob
    names = _names()
    assert (25, "pikachupopstar2021", _PAGE) in names
    assert all("December" not in name for _dex, name, _url in names)


def test_official_post_approves_without_the_pokedex() -> None:
    row = {
        "species_id": "pikachu",
        "kind": "costume",
        "value": "flower-crown",
        "source_url": "https://pokemongolive.com/news/example",
    }
    verdict = _verdict(row, pokedex=set())
    assert verdict.verdict == "auto-approve"
    assert verdict.confidence == "high"
    assert verdict.urls == ("https://pokemongolive.com/news/example",)
    assert verdict.reason.startswith("Official")


def test_matching_game_id_is_approved_with_both_urls() -> None:
    row = {
        "species_id": "pikachu",
        "kind": "costume",
        "value": "holiday-2016",
        "source_url": _POKEDEX,
        "label": "Holiday 2016",
    }
    verdict = _verdict(row)
    assert verdict.verdict == "auto-approve"
    assert verdict.confidence == "high"
    assert _POKEDEX in verdict.urls
    assert _PAGE in verdict.urls
    assert "December" not in verdict.reason


def test_named_costume_matches_the_sprite_label() -> None:
    row = {
        "species_id": "pikachu",
        "kind": "costume",
        "value": "pop-star",
        "source_url": _POKEDEX,
        "label": "Pop Star",
    }
    verdict = _verdict(row)
    assert verdict.verdict == "auto-approve"
    assert verdict.confidence == "medium"
    doctor = _verdict(
        {
            "species_id": "pikachu",
            "kind": "costume",
            "value": "doctor",
            "source_url": _POKEDEX,
            "label": "Ph.D.",
        }
    )
    assert doctor.verdict == "auto-approve"


def test_shared_words_match_only_when_one_row_fits() -> None:
    row = {
        "species_id": "pikachu",
        "kind": "costume",
        "value": "gofest-2025-goggles-blue",
        "source_url": _POKEDEX,
        "label": "GO Fest 2025 Goggles Blue",
    }
    verdict = _verdict(row)
    assert verdict.verdict == "auto-approve"
    assert verdict.confidence == "medium"
    ambiguous = _verdict(
        {
            "species_id": "pikachu",
            "kind": "costume",
            "value": "red-hat-2020",
            "source_url": _POKEDEX,
            "label": "Red hat 2020",
        },
        sibling_slugs=("red-hat-2020", "red-hat-2021"),
    )
    assert ambiguous.verdict == "needs-review"


def test_one_source_stays_a_draft() -> None:
    row = {
        "species_id": "pikachu",
        "kind": "costume",
        "value": "jeju",
        "source_url": _POKEDEX,
        "label": "Jeju",
    }
    verdict = _verdict(row)
    assert verdict.verdict == "needs-review"
    assert verdict.confidence == "low"
    assert "no second source" in verdict.reason


def test_battle_forms_and_internal_slots_are_rejected() -> None:
    for value in ("shadow", "purified", "alolan", "normal", "test-form"):
        verdict = _verdict(
            {
                "species_id": "pikachu",
                "kind": "costume",
                "value": value,
                "source_url": _POKEDEX,
            }
        )
        assert verdict.verdict == "reject-non-costume"
    numbered = _verdict(
        {
            "species_id": "pikachu",
            "kind": "costume",
            "value": "costume-1",
            "source_url": _POKEDEX,
            "label": "Costume 1",
        }
    )
    assert numbered.verdict == "reject-non-costume"
    released = _verdict(
        {
            "species_id": "pikachu",
            "kind": "costume",
            "value": "costume-2",
            "source_url": _POKEDEX,
            "label": "Costume 2",
        }
    )
    assert released.verdict == "auto-approve"


def test_apply_skips_a_row_a_person_signed() -> None:
    seed = {
        "rows": [
            {
                "species_id": "pikachu",
                "kind": "costume",
                "value": "flower-crown",
                "source_url": "https://pokemongolive.com/news/example",
                "verified_by": "ada@example.com",
                "verified_at": "2026-11-18",
                "status": "draft",
                "notes": "Kept.",
            },
            {
                "species_id": "pikachu",
                "kind": "costume",
                "value": "party-hat",
                "source_url": "https://pokemongolive.com/news/party",
                "verified_by": "hand-seed",
                "verified_at": "2026-11-20",
                "status": "draft",
                "notes": "",
            },
        ]
    }
    counts = apply_verdicts(
        seed,
        pokedex=set(),
        codes={},
        names=[],
        dex_of={"pikachu": 25},
    )
    signed, approved = seed["rows"]
    assert signed["status"] == "draft"
    assert signed["verified_by"] == "ada@example.com"
    assert signed["notes"] == "Kept."
    assert approved["status"] == "approved"
    assert approved["verified_by"] == "auto-verifier"
    assert counts["auto_approved"] == 1
    assert counts["skipped"] == 1
