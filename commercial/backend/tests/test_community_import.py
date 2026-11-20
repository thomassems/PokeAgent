"""Community costume import: names only, drafts only, no second copy."""

from tools.import_community_variants import (
    merge_community_rows,
    robots_allows,
    variants_from_pokedex,
)


def _pokedex() -> list[dict]:
    return [
        {
            "id": "PIKACHU",
            "assetForms": [
                {"form": "POP_STAR", "costume": None, "isFemale": False},
                {"form": "POP_STAR", "costume": None, "isFemale": True},
                {"form": "ROCK_STAR", "costume": None, "isFemale": False},
                {"form": "DOCTOR", "costume": None, "isFemale": False},
                {"form": "MEGA", "costume": None, "isFemale": False},
                {"form": None, "costume": "PARTY_HAT", "isFemale": False},
            ],
        }
    ]


def test_named_costumes_are_kept_and_battle_forms_are_not() -> None:
    rows, skipped = variants_from_pokedex(_pokedex(), {"pikachu"})
    values = {row["value"] for row in rows}
    assert values == {"pop-star", "rock-star", "doctor", "party-hat"}
    assert skipped == []
    doctor = next(row for row in rows if row["value"] == "doctor")
    assert doctor["status"] == "draft"
    assert doctor["source_type"] == "community"
    assert "Ph.D." in doctor["notes"]
    assert ".png" not in doctor["notes"]


def test_merge_does_not_overwrite_an_approved_row() -> None:
    seed = {
        "rows": [
            {
                "species_id": "pikachu",
                "kind": "costume",
                "value": "party-hat",
                "source_url": "https://pokemongolive.com/en/post/example",
                "status": "approved",
                "notes": "Official.",
            }
        ]
    }
    incoming, _skipped = variants_from_pokedex(_pokedex(), {"pikachu"})
    first = merge_community_rows(seed, incoming)
    assert first["added"] == 3
    assert first["merged"] == 1
    party = next(row for row in seed["rows"] if row["value"] == "party-hat")
    assert party["status"] == "approved"
    assert party["source_url"].startswith("https://pokemongolive.com/")
    assert party["notes"] == "Official."
    assert party["community_source_url"].startswith("https://pokemon-go-api.github.io/")
    second = merge_community_rows(seed, incoming)
    assert second == {"added": 0, "merged": 0, "unchanged": 4}
    assert len(seed["rows"]) == 4


def test_robots_txt_can_block_the_pokedex_path() -> None:
    assert robots_allows("", "/pokemon-go-api/api/pokedex.json")
    blocked = "User-agent: *\nDisallow: /\n"
    assert robots_allows(blocked, "/pokemon-go-api/api/pokedex.json") is False
    allowed = "User-agent: *\nDisallow: /private\n"
    assert robots_allows(allowed, "/pokemon-go-api/api/pokedex.json")
