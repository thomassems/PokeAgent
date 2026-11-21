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
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from data.go_catalog import variant_label
from tools.costume_evidence import (
    Announcement,
    news_result,
    parse_announcements,
    parse_event_codes,
    parse_sprite_names,
    slot_stem,
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
_NEWS_CACHE = _ROOT / "data" / "cache" / "costume-news.json"
_CHECKED_ON = "2026-11-20"
_NEWS_ON = "2026-11-21"
_NEWS_GAP = 1.0
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


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip = False

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)


def _page_text(url: str) -> str:
    status, body = _request(url)
    if status != 200 or not body.lstrip().startswith("<"):
        return ""
    parser = _Text()
    parser.feed(body)
    return re.sub(r"\s+", " ", " ".join(parser.parts))


def _news_urls(seed: dict[str, object], names: dict[str, str]) -> list[str]:
    rows = seed["rows"]
    assert isinstance(rows, list)
    draft_names = {
        names.get(str(row["species_id"]), "")
        for row in rows
        if (row.get("verification") or {}).get("verdict") == "needs-review"
    }
    draft_names.discard("")
    urls: list[str] = []
    for row in rows:
        if row.get("kind") != "costume":
            continue
        if names.get(str(row["species_id"]), "") not in draft_names:
            continue
        if row.get("source_type", "official") != "official":
            continue
        url = str(row.get("source_url") or "")
        if url.startswith("https://") and url not in urls:
            urls.append(url)
    extras = (
        "https://pokemongo.com/news/an-instinctive-hero",
        "https://pokemongo.com/news/a-mystic-hero",
        "https://pokemongo.com/news/a-valorous-hero",
        "https://pokemongo.com/news/indonesia-journey-2025-bekasi",
        "https://pokemongo.com/news/birthday2017",
        "https://pokemongo.com/news/birthday2021",
        "https://pokemongo.com/news/flying-pikachu-2022",
        "https://pokemongo.com/news/pokemon-go-safari-zone-taipei",
    )
    for url in extras:
        if url not in urls:
            urls.append(url)
    return urls


def load_announcements(
    seed: dict[str, object], names: dict[str, str], *, refresh: bool
) -> list[Announcement]:
    """Parsed species and costume phrases. The post HTML is not stored."""
    if _NEWS_CACHE.exists() and not refresh:
        cached = json.loads(_NEWS_CACHE.read_text())
        return [
            Announcement(str(item["species"]), str(item["phrase"]), str(item["url"]))
            for item in cached["announcements"]
        ]
    found: list[Announcement] = []
    for url in _news_urls(seed, names):
        time.sleep(_NEWS_GAP)
        try:
            text = _page_text(url)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            print(f"news fetch failed\t{url}")
            continue
        if not text:
            print(f"news fetch empty\t{url}")
            continue
        found.extend(parse_announcements(text, url, tuple(names.values())))
    _NEWS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    _NEWS_CACHE.write_text(
        json.dumps(
            {
                "checked_at": _NEWS_ON,
                "announcements": [
                    {"species": item.species, "phrase": item.phrase, "url": item.url}
                    for item in found
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return found


def _append_alias(row: dict[str, object], code: str) -> None:
    current = row.get("community_aliases")
    aliases = list(current) if isinstance(current, list) else []
    if code not in aliases:
        aliases.append(code)
    row["community_aliases"] = aliases


def apply_news(
    seed: dict[str, object],
    announcements: list[Announcement],
    names: dict[str, str],
) -> dict[str, int]:
    """Upgrade drafts a fetched official post actually names."""
    rows = seed["rows"]
    assert isinstance(rows, list)
    official: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        if row.get("kind") != "costume" or row.get("status") == "merged":
            continue
        if row.get("source_type", "official") != "official":
            continue
        official.setdefault(str(row["species_id"]), []).append(row)
    counts = {"news_approved": 0, "news_merged": 0}
    for row in rows:
        verification = row.get("verification") or {}
        if not isinstance(verification, dict):
            continue
        if (
            verification.get("verdict") != "needs-review"
            or row.get("status") != "draft"
        ):
            continue
        species_id = str(row["species_id"])
        result = news_result(
            species_id=species_id,
            value=str(row["value"]),
            species_name=names.get(species_id, ""),
            official_rows=official.get(species_id, []),
            announcements=announcements,
        )
        if result.action == "merge":
            target = next(
                item
                for item in official[species_id]
                if item["value"] == result.official
            )
            _append_alias(target, str(row["value"]))
            row["status"] = "merged"
            row["merged_into"] = result.official
            row["verified_by"] = "community-import"
            note = str(row.get("notes") or "")
            extra = f" Same costume as {result.official}. Kept on that row as an alias."
            if extra.strip() not in note:
                row["notes"] = note + extra
            row["verification"] = {
                "verdict": "alias",
                "confidence": result.confidence,
                "sources": ["official Pokémon GO post"],
                "urls": [result.url],
                "reason": result.reason,
                "checked_at": _NEWS_ON,
                "because": result.because,
            }
            counts["news_merged"] += 1
        elif result.action == "approve":
            row["status"] = "approved"
            row["verified_by"] = "auto-verifier"
            row["verified_at"] = _NEWS_ON
            row["verification"] = {
                "verdict": "auto-approve",
                "confidence": result.confidence,
                "sources": ["pokemon-go-api pokedex", "official Pokémon GO post"],
                "urls": [str(row["source_url"]), result.url],
                "reason": result.reason,
                "checked_at": _NEWS_ON,
            }
            counts["news_approved"] += 1
        else:
            verification["reason"] = result.reason
            verification["checked_at"] = _NEWS_ON
            row["verification"] = verification
    return counts


def _icon_map(payload: list[dict[str, object]]) -> dict[tuple[str, str], str]:
    """Species id and costume slug to an icon URL. The file is not copied."""
    from tools.import_community_variants import slug

    icons: dict[tuple[str, str], str] = {}
    for mon in payload:
        game_id = str(mon.get("id") or "").lower()
        assets = mon.get("assetForms")
        if not isinstance(assets, list):
            continue
        for asset in assets:
            if not isinstance(asset, dict) or asset.get("isFemale"):
                continue
            token = asset.get("costume") or asset.get("form") or ""
            image = str(asset.get("image") or "")
            if game_id and token and image:
                icons[(game_id, slug(str(token)))] = image
    return icons


def _same_icon(left: str, right: str) -> bool:
    hashes: list[str] = []
    for url in (left, right):
        time.sleep(_NEWS_GAP)
        request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status != 200:
                    return False
                payload = response.read()
        except urllib.error.URLError:
            return False
        if not payload:
            return False
        hashes.append(hashlib.sha256(payload).hexdigest())
    return hashes[0] == hashes[1]


def apply_slot_merges(
    seed: dict[str, object], payload: list[dict[str, object]]
) -> list[str]:
    """Merge a second slot when it is the same costume, not a different one.

    A no-evolve suffix is the same costume. An `-a-02` suffix is merged only
    when its icon matches the primary icon. Different pixels stay separate.
    """
    rows = seed["rows"]
    assert isinstance(rows, list)
    costumes = [
        row
        for row in rows
        if row.get("kind") == "costume" and row.get("status") != "merged"
    ]
    by_key = {(str(row["species_id"]), str(row["value"])): row for row in costumes}
    icons = _icon_map(payload)
    merged: list[str] = []
    for row in costumes:
        stem = slot_stem(str(row["value"]))
        if not stem:
            continue
        primary = by_key.get((str(row["species_id"]), stem))
        if primary is None or primary is row:
            continue
        if str(row["value"]).endswith("-02"):
            left = icons.get((str(row["species_id"]), str(row["value"])), "")
            right = icons.get((str(row["species_id"]), stem), "")
            if not left or not right or not _same_icon(left, right):
                continue
        _append_alias(primary, str(row["value"]))
        row["status"] = "merged"
        row["merged_into"] = stem
        row["verified_by"] = "community-import"
        note = str(row.get("notes") or "")
        extra = f" Same costume as {stem}. Kept on that row as an alias."
        if extra.strip() not in note:
            row["notes"] = note + extra
        row["verification"] = {
            "verdict": "alias",
            "confidence": "high",
            "sources": ["pokemon-go-api pokedex"],
            "urls": [str(row.get("source_url") or "")],
            "reason": "This is a second internal slot for the same costume.",
            "checked_at": _NEWS_ON,
        }
        merged.append(f"{row['species_id']} {row['value']} -> {stem}")
    return merged


def verify(*, refresh: bool, dry_run: bool) -> tuple[dict[str, int], list[str]]:
    payload = fetch_pokedex(refresh=refresh)
    codes, names = load_evidence(refresh=refresh)
    catalog = json.loads(_CATALOG.read_text())["species"]
    dex_of = {item["id"]: int(item["dex"]) for item in catalog}
    species_names = {item["id"]: str(item["name"]) for item in catalog}
    seed = json.loads(_SEED.read_text())
    counts = apply_verdicts(
        seed,
        pokedex=_pokedex_keys(payload),
        codes=codes,
        names=names,
        dex_of=dex_of,
    )
    announcements = load_announcements(seed, species_names, refresh=refresh)
    counts.update(apply_news(seed, announcements, species_names))
    slot_merges = apply_slot_merges(seed, payload)
    counts["slot_merged"] = len(slot_merges)
    seed["method"] = (
        "Rows a person checked stay as they were. Costume and variant drafts "
        "are approved by tools/verify_costumes.py when an official Pokémon GO "
        "post is already cited, or when the game-data id is also on the "
        "independent event-form list. A later pass reads official posts and "
        "approves a leftover only when a post names that species in that "
        "costume. A second slot is merged when it is the same costume. "
        f"The verifier last ran on {_NEWS_ON}."
    )
    if not dry_run:
        _SEED.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n")
    lines = [f"slot-merge\t{line}" for line in slot_merges]
    lines.extend(pending_lines(seed))
    return counts, lines


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
