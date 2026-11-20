"""Import costume names from the pokemon-go-api pokedex.

Run by hand from commercial/backend:

    uv run python -m tools.import_community_variants

The fetch is one GET, cached under data/cache, with a named User-Agent and
a one-second gap before any request. A second run reads the cache and does
not add rows that are already in the seed. Images are not stored. Shiny
image URLs are ignored, because that file puts one on every asset.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_SEED = _ROOT / "data" / "go_curated_seed.json"
_CATALOG = _ROOT / "data" / "go_base.json"
_COLLECTIONS = _ROOT / "data" / "collections.json"
_CACHE = _ROOT / "data" / "cache" / "pokemon-go-api-pokedex.json"
_SOURCE = "https://pokemon-go-api.github.io/pokemon-go-api/api/pokedex.json"
_ROBOTS = "https://pokemon-go-api.github.io/robots.txt"
_USER_AGENT = "TrainermonCostumeImport/1.0 (manual costume import; cached)"
_GAP_SECONDS = 1.0
_FETCHED_ON = "2026-11-20"

# Form ids that are event costumes but do not carry a year.
_NAMED_COSTUMES = {
    "POP_STAR",
    "ROCK_STAR",
    "DOCTOR",
    "HORIZONS",
    "KARIYUSHI",
    "KURTA",
    "JEJU",
    "TSHIRT_01",
    "TSHIRT_02",
    "TSHIRT_03",
    "FLYING_01",
    "FLYING_02",
    "FLYING_03",
    "FLYING_04",
    "FLYING_5TH_ANNIV",
    "FLYING_OKINAWA",
}
_YEAR = re.compile(r"(?:19|20)\d{2}")
_SIZE = {
    "AVERAGE": "average",
    "LARGE": "large",
    "SMALL": "small",
    "SUPER": "super",
}
_REGION = {
    "ALOLA": "alolan",
    "GALARIAN": "galarian",
    "HISUIAN": "hisuian",
    "PALDEA": "paldean",
}
_LABELS = {
    "pop-star": "Pop Star",
    "rock-star": "Rock Star",
    "doctor": "Ph.D.",
}


def slug(token: str) -> str:
    """A costume slug: lowercase, hyphens, letters and digits only."""
    text = token.strip().lower().replace("_", "-")
    text = re.sub(r"[^a-z0-9-]", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def is_costume_form(form: str) -> bool:
    """True for event costumes stored in the form field, not battle forms."""
    if form in _NAMED_COSTUMES:
        return True
    return _YEAR.search(form) is not None


def robots_allows(body: str, path: str) -> bool:
    """A missing or empty robots.txt allows the fetch.

    Disallow rules are read only. Allow is not required. A rule of `/`
    blocks the host. A longer prefix blocks that path.
    """
    disallows: list[str] = []
    applies = True
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        lowered = key.lower()
        if lowered == "user-agent":
            applies = value in {"*", _USER_AGENT}
            continue
        if applies and lowered == "disallow" and value:
            disallows.append(value)
    for rule in disallows:
        if rule == "/":
            return False
        if path.startswith(rule):
            return False
    return True


def _note(token: str) -> str:
    lead = f"Game id {token}."
    if token == "DOCTOR":
        lead = "Game id DOCTOR. This is the Ph.D. costume."
    elif token == "POP_STAR":
        lead = "Game id POP_STAR. This is Pop Star."
    elif token == "ROCK_STAR":
        lead = "Game id ROCK_STAR. This is Rock Star."
    return (
        f"{lead} Community draft from the pokedex asset list. "
        "Every asset in that file has a shiny image URL, so shiny is not recorded."
    )


def _species_id(game_id: str, form: str | None, known: set[str]) -> str | None:
    base = game_id.lower()
    if form in _SIZE:
        sized = f"{base}_{_SIZE[form]}"
        if sized in known:
            return sized
    if form in _REGION:
        regional = f"{base}_{_REGION[form]}"
        if regional in known:
            return regional
        if base in known:
            return base
    if base in known:
        return base
    return None


def variants_from_pokedex(
    payload: list[dict[str, Any]], known_ids: set[str]
) -> tuple[list[dict[str, str]], list[str]]:
    """Costume rows, plus game ids that are not in the catalog.

    Female asset copies are skipped when the same id was already seen.
    Mega, Gigantamax, regional, and other battle forms are not costumes.
    """
    seen: set[tuple[str, str, str]] = set()
    rows: list[dict[str, str]] = []
    skipped: list[str] = []
    pending_female: list[tuple[str, dict[str, Any]]] = []

    def consider(game_id: str, asset: dict[str, Any]) -> None:
        form = asset.get("form") or None
        costume = asset.get("costume") or None
        if costume:
            token = str(costume)
            species = _species_id(
                game_id, form if form in _SIZE or form in _REGION else None, known_ids
            )
        elif form and is_costume_form(str(form)):
            token = str(form)
            species = _species_id(game_id, None, known_ids)
        else:
            return
        if species is None:
            skipped.append(f"{game_id}:{token}")
            return
        value = slug(token)
        if not value or not value.replace("-", "").isalnum():
            skipped.append(f"{game_id}:{token}")
            return
        key = (species, "costume", value)
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "species_id": species,
                "kind": "costume",
                "value": value,
                "source_url": _SOURCE,
                "verified_at": _FETCHED_ON,
                "verified_by": "community-import",
                "status": "draft",
                "source_type": "community",
                "notes": _note(token),
            }
        )

    for mon in payload:
        game_id = str(mon.get("id") or "")
        for asset in mon.get("assetForms") or []:
            if asset.get("isFemale"):
                pending_female.append((game_id, asset))
                continue
            consider(game_id, asset)
    for game_id, asset in pending_female:
        consider(game_id, asset)
    rows.sort(key=lambda row: (row["species_id"], row["value"]))
    return rows, skipped


def merge_community_rows(
    seed: dict[str, Any], incoming: list[dict[str, str]]
) -> dict[str, int]:
    """Add community drafts. Never change an existing row's status or source.

    When the species, kind, and slug already exist, only community_source_url
    is filled, and only if it was empty.
    """
    rows: list[dict[str, Any]] = seed["rows"]
    by_fact: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_fact.setdefault((row["species_id"], row["kind"], row["value"]), []).append(
            row
        )
    added = 0
    merged = 0
    unchanged = 0
    for item in incoming:
        key = (item["species_id"], item["kind"], item["value"])
        matches = by_fact.get(key, [])
        if matches:
            attached = False
            for row in matches:
                if row.get("community_source_url"):
                    continue
                if row.get("source_type") == "community":
                    continue
                row["community_source_url"] = _SOURCE
                attached = True
                merged += 1
                break
            if not attached:
                unchanged += 1
            continue
        rows.append(dict(item))
        by_fact[key] = [rows[-1]]
        added += 1
    return {"added": added, "merged": merged, "unchanged": unchanged}


def ensure_collections(
    seed: dict[str, Any],
    catalog: list[dict[str, Any]],
    collections: dict[str, Any],
) -> int:
    """One checklist per species that has a costume or background row."""
    names = {item["id"]: item["name"] for item in catalog}
    wanted: dict[str, set[str]] = {}
    for row in seed["rows"]:
        if row["kind"] in {"costume", "background"}:
            wanted.setdefault(row["species_id"], set()).add(row["kind"])
    by_species = {item["species_id"]: item for item in collections["collections"]}
    added = 0
    for species_id in sorted(wanted):
        kinds = ["costume", "background"]
        kinds = [kind for kind in kinds if kind in wanted[species_id]]
        current = by_species.get(species_id)
        if current is not None:
            if set(current["kinds"]) != set(kinds):
                current["kinds"] = kinds
            continue
        name = names.get(species_id, species_id)
        if kinds == ["background"]:
            title = f"{name} backgrounds"
            summary = f"Verified {name} backgrounds."
        elif "background" in kinds:
            title = f"{name} costumes"
            summary = f"Verified {name} costumes and backgrounds."
        else:
            title = f"{name} costumes"
            summary = f"Verified {name} costumes."
        collections["collections"].append(
            {
                "id": f"{species_id}-costumes",
                "title": title,
                "summary": summary,
                "species_id": species_id,
                "kinds": kinds,
            }
        )
        added += 1
    return added


def _request(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 404, ""
        raise


def fetch_pokedex(refresh: bool = False) -> list[dict[str, Any]]:
    """Return the cached pokedex, or fetch it once if the cache is missing."""
    if _CACHE.exists() and not refresh:
        return json.loads(_CACHE.read_text())
    time.sleep(_GAP_SECONDS)
    status, robots = _request(_ROBOTS)
    path = "/pokemon-go-api/api/pokedex.json"
    if status != 404 and not robots_allows(robots, path):
        raise RuntimeError(f"robots.txt disallows {path}.")
    time.sleep(_GAP_SECONDS)
    status, body = _request(_SOURCE)
    if status != 200:
        raise RuntimeError(f"Pokedex fetch returned {status}.")
    payload = json.loads(body)
    if not isinstance(payload, list):
        raise RuntimeError("Pokedex JSON was not a list.")
    _CACHE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE.write_text(body)
    return payload


def import_variants(payload: list[dict[str, Any]]) -> dict[str, int]:
    catalog = json.loads(_CATALOG.read_text())["species"]
    known = {item["id"] for item in catalog}
    incoming, skipped = variants_from_pokedex(payload, known)
    seed = json.loads(_SEED.read_text())
    stats = merge_community_rows(seed, incoming)
    _SEED.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n")
    collections = json.loads(_COLLECTIONS.read_text())
    stats["collections_added"] = ensure_collections(seed, catalog, collections)
    _COLLECTIONS.write_text(
        json.dumps(collections, indent=2, ensure_ascii=False) + "\n"
    )
    stats["skipped"] = len(skipped)
    stats["incoming"] = len(incoming)
    return stats


def main() -> None:
    payload = fetch_pokedex()
    stats = import_variants(payload)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
