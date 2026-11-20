"""Approve costume drafts that two sources agree on.

Run from commercial/backend:

    uv run python -m tools.verify_costumes
    uv run python -m tools.verify_costumes --dry-run

The pokedex file is the game-data import. The event-form list is read to
check ids and names, then discarded. A second run uses the cache and does
not fetch. Rows a person has already signed (an email in verified_by) are
left alone.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from data.go_catalog import variant_label
from tools.costume_evidence import (
    parse_event_codes,
    parse_sprite_names,
    variant_kind,
    verdict_for,
)
from tools.import_community_variants import (
    fetch_pokedex,
    robots_allows,
    variants_from_pokedex,
)

_ROOT = Path(__file__).resolve().parents[1]
_CATALOG = _ROOT / "data" / "go_base.json"
_SEED = _ROOT / "data" / "go_curated_seed.json"
_CACHE = _ROOT / "data" / "cache" / "costume-evidence.json"
_CHECKED_ON = "2026-11-20"
_POKEDEX_URL = "https://pokemon-go-api.github.io/pokemon-go-api/api/pokedex.json"
_EVENT_TITLE = "Event Pokémon (GO)"
_PIKACHU_TITLE = "Pikachu (GO)"
_EVENT_URL = "https://bulbapedia.bulbagarden.net/wiki/Event_Pok%C3%A9mon_(GO)"
_PIKACHU_URL = "https://bulbapedia.bulbagarden.net/wiki/Pikachu_(GO)"
_API = "https://bulbapedia.bulbagarden.net/w/api.php"
_ROBOTS = "https://bulbapedia.bulbagarden.net/robots.txt"
_USER_AGENT = "TrainermonCostumeVerify/1.0 (costume existence check; cached)"
_GAP_SECONDS = 5.0
_SOURCES = (
    "pokemon-go-api pokedex",
    "Event Pokémon (GO)",
    "Pikachu (GO)",
)
_CHECKED_URLS = (_POKEDEX_URL, _EVENT_URL, _PIKACHU_URL)


def _request(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 404, ""
        raise


def _wikitext(title: str) -> str:
    query = urllib.parse.urlencode(
        {"action": "parse", "page": title, "prop": "wikitext", "format": "json"}
    )
    status, body = _request(f"{_API}?{query}")
    if status != 200:
        raise RuntimeError(f"Checklist fetch for {title} returned {status}.")
    payload = json.loads(body)
    if "error" in payload:
        raise RuntimeError(f"Checklist page {title} was not readable.")
    return str(payload["parse"]["wikitext"]["*"])


def load_evidence(
    *, refresh: bool = False
) -> tuple[dict[tuple[int, str], str], list[tuple[int, str, str]]]:
    """Return parsed ids and names. Fetch only when the cache is missing."""
    if _CACHE.exists() and not refresh:
        cached = json.loads(_CACHE.read_text())
        codes = {
            (int(item["dex"]), str(item["code"])): str(item["url"])
            for item in cached["codes"]
        }
        names = [
            (int(item["dex"]), str(item["name"]), str(item["url"]))
            for item in cached["names"]
        ]
        return codes, names
    time.sleep(_GAP_SECONDS)
    status, robots = _request(_ROBOTS)
    if status != 404 and not robots_allows(robots, "/w/api.php"):
        raise RuntimeError("robots.txt disallows the checklist API.")
    time.sleep(_GAP_SECONDS)
    event = _wikitext(_EVENT_TITLE)
    time.sleep(_GAP_SECONDS)
    pikachu = _wikitext(_PIKACHU_TITLE)
    codes = parse_event_codes(event, _EVENT_URL)
    names = parse_sprite_names(event, _EVENT_URL) + parse_sprite_names(
        pikachu, _PIKACHU_URL
    )
    _CACHE.parent.mkdir(parents=True, exist_ok=True)
    _CACHE.write_text(
        json.dumps(
            {
                "checked_at": _CHECKED_ON,
                "codes": [
                    {"dex": dex, "code": code, "url": url}
                    for (dex, code), url in sorted(codes.items())
                ],
                "names": [
                    {"dex": dex, "name": name, "url": url} for dex, name, url in names
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return codes, names


def _human_signed(row: dict[str, object]) -> bool:
    return "@" in str(row.get("verified_by") or "")


def _should_judge(row: dict[str, object]) -> bool:
    if row.get("status") == "merged" or _human_signed(row):
        return False
    if not variant_kind(str(row.get("kind"))):
        return False
    if row.get("verified_by") == "auto-verifier":
        return True
    return row.get("status") == "draft"


def apply_verdicts(
    seed: dict[str, object],
    *,
    pokedex: set[tuple[str, str]],
    codes: dict[tuple[int, str], str],
    names: list[tuple[int, str, str]],
    dex_of: dict[str, int],
) -> dict[str, int]:
    """Write verdicts onto draft costume rows. A signed row is not changed."""
    rows = seed["rows"]
    assert isinstance(rows, list)
    by_species: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        if row.get("kind") == "costume" and row.get("status") != "merged":
            by_species.setdefault(str(row["species_id"]), []).append(row)
    counts = {"auto_approved": 0, "needs_review": 0, "rejected": 0, "skipped": 0}
    for row in rows:
        if not _should_judge(row):
            counts["skipped"] += 1
            continue
        species_id = str(row["species_id"])
        siblings = by_species.get(species_id, [])
        verdict = verdict_for(
            row,
            pokedex=pokedex,
            codes=codes,
            names=names,
            dex=dex_of.get(species_id),
            label=variant_label(str(row["kind"]), str(row["value"])),
            sibling_labels=tuple(
                variant_label("costume", str(item["value"]))
                for item in siblings
                if item is not row
            ),
            sibling_slugs=tuple(str(item["value"]) for item in siblings),
            checked_sources=_SOURCES,
            checked_urls=_CHECKED_URLS,
        )
        verdict_row = verdict.as_dict()
        verdict_row["checked_at"] = _CHECKED_ON
        row["verification"] = verdict_row
        if verdict.verdict == "auto-approve":
            row["status"] = "approved"
            row["verified_by"] = "auto-verifier"
            row["verified_at"] = _CHECKED_ON
            counts["auto_approved"] += 1
        elif verdict.verdict == "reject-non-costume":
            row["status"] = "rejected"
            row["verified_by"] = "auto-verifier"
            row["verified_at"] = _CHECKED_ON
            counts["rejected"] += 1
        else:
            row["status"] = "draft"
            counts["needs_review"] += 1
    return counts


def _pokedex_keys(payload: list[dict[str, object]]) -> set[tuple[str, str]]:
    catalog = json.loads(_CATALOG.read_text())["species"]
    known = {item["id"] for item in catalog}
    incoming, _skipped = variants_from_pokedex(payload, known)
    return {(row["species_id"], row["value"]) for row in incoming}


def pending_lines(seed: dict[str, object]) -> list[str]:
    rows = seed["rows"]
    assert isinstance(rows, list)
    lines: list[str] = []
    for row in rows:
        verification = row.get("verification") or {}
        if not isinstance(verification, dict):
            continue
        verdict = verification.get("verdict")
        if verdict not in {"needs-review", "reject-non-costume"}:
            continue
        lines.append(
            f"{verdict}\t{row['species_id']}\t{row['kind']}\t{row['value']}\t"
            f"{verification.get('reason', '')}"
        )
    return lines


def verify(*, refresh: bool, dry_run: bool) -> tuple[dict[str, int], list[str]]:
    payload = fetch_pokedex(refresh=refresh)
    codes, names = load_evidence(refresh=refresh)
    catalog = json.loads(_CATALOG.read_text())["species"]
    dex_of = {item["id"]: int(item["dex"]) for item in catalog}
    seed = json.loads(_SEED.read_text())
    counts = apply_verdicts(
        seed,
        pokedex=_pokedex_keys(payload),
        codes=codes,
        names=names,
        dex_of=dex_of,
    )
    seed["method"] = (
        "Rows a person checked stay as they were. Costume and variant drafts "
        "are approved by tools/verify_costumes.py when an official Pokémon GO "
        "post is already cited, or when the game-data id is also on the "
        "independent event-form list. Anything else stays a draft. The "
        f"verifier last ran on {_CHECKED_ON}."
    )
    if not dry_run:
        _SEED.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n")
    return counts, pending_lines(seed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify costume drafts.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    counts, lines = verify(refresh=args.refresh, dry_run=args.dry_run)
    print(json.dumps(counts, indent=2))
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
