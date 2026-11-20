"""Decide whether a costume draft is real enough to approve.

A game-data id on its own is not enough: that file also holds unreleased
assets. An official Pokémon GO post is enough on its own, because the post
is the release. A community id is approved only when the same species and
code also appear on an independent event-form list. The list is read for
the check. Its sentences are not stored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_VARIANT_KINDS = {"costume", "background", "costume_shiny", "background_shiny"}
_OFFICIAL_HOSTS = {"pokemongolive.com", "pokemongo.com", "pokemon.com"}
_HARD_NON_COSTUME = {
    "normal",
    "shadow",
    "purified",
    "alolan",
    "galarian",
    "hisuian",
    "paldean",
    "mega",
    "gigantamax",
    "gmax",
    "primal",
    "origin",
    "therian",
    "incarnate",
    "test",
    "debug",
    "unreleased",
    "internal",
    "dummy",
    "placeholder",
    "temp",
    "wip",
}
# Short words that show up inside many costume names. A name match on one
# of these would approve the wrong row.
_NAME_STOP = {
    "hat",
    "cap",
    "red",
    "blue",
    "yellow",
    "sun",
    "moon",
    "bow",
    "fly",
    "pi",
}
_MSP = re.compile(r"\{\{MSP/GO\|(?:size=\d+\|)?(\d+)([A-Za-z][A-Za-z0-9_]*)")
_SPRITE = re.compile(r"\{\{Spritebox/GO\|ndex=(\d+)[A-Za-z0-9_]*\|name=([^|}]+)")
# costume-1 is an internal slot. costume-2020 still has a year, so it stays
# a draft until a second source names it.
_PLACEHOLDER = re.compile(r"costume-\d{1,2}")


@dataclass(frozen=True)
class Verdict:
    verdict: str
    confidence: str
    sources: tuple[str, ...]
    urls: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict,
            "confidence": self.confidence,
            "sources": list(self.sources),
            "urls": list(self.urls),
            "reason": self.reason,
        }


def variant_kind(kind: str) -> bool:
    return kind in _VARIANT_KINDS


def official_news(url: str) -> bool:
    if not url.startswith("https://"):
        return False
    host = url.split("/", 3)[2].lower()
    if host.startswith("www."):
        host = host[4:]
    return host in _OFFICIAL_HOSTS


def normalize_code(token: str) -> str:
    """Compare a game id and a checklist id as the same words.

    `flying` and `fly` are the same word. A trailing `noevolve` marks a
    costume that cannot evolve, not a different costume.
    """
    text = token.replace("_", "-")
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)
    text = re.sub(r"([A-Za-z])(\d)", r"\1-\2", text)
    # 2024Lucas splits. 5th does not: the h is already lower case.
    text = re.sub(r"(\d)([A-Z])", r"\1-\2", text)
    parts = []
    for part in text.lower().split("-"):
        if not part or part == "noevolve":
            continue
        if part == "flying":
            part = "fly"
        parts.append(part)
    return "-".join(parts)


def phrase_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", label.lower())


def parse_event_codes(wikitext: str, url: str) -> dict[tuple[int, str], str]:
    """Dex and costume code pairs from one checklist page.

    The page text is not returned. Only the id and the page URL are.
    """
    found: dict[tuple[int, str], str] = {}
    for dex, token in _MSP.findall(wikitext):
        code = normalize_code(token)
        if code:
            found[(int(dex), code)] = url
    return found


def parse_sprite_names(wikitext: str, url: str) -> list[tuple[int, str, str]]:
    """Dex, normalized costume name, and the page URL. No sentence text."""
    names: list[tuple[int, str, str]] = []
    for dex, name in _SPRITE.findall(wikitext):
        key = phrase_key(name)
        if key:
            names.append((int(dex), key, url))
    return names


def _hard_non_costume(value: str) -> bool:
    tokens = set(value.lower().split("-"))
    return value.lower() in _HARD_NON_COSTUME or bool(tokens & _HARD_NON_COSTUME)


def _name_url(
    label: str,
    names: list[tuple[str, str]],
    sibling_labels: tuple[str, ...],
) -> str | None:
    key = phrase_key(label)
    if len(key) < 3 or key in _NAME_STOP:
        return None
    hits = [(name, url) for name, url in names if key in name]
    if len(hits) != 1:
        return None
    name, url = hits[0]
    for other in sibling_labels:
        other_key = phrase_key(other)
        if not other_key or other_key == key:
            continue
        if len(other_key) >= 3 and other_key not in _NAME_STOP and other_key in name:
            return None
    return url


def _subset_url(
    slug: str,
    codes: dict[str, str],
    sibling_slugs: tuple[str, ...],
) -> str | None:
    ours = set(normalize_code(slug).split("-"))
    ours.discard("")
    hits: list[tuple[str, str]] = []
    for code, url in codes.items():
        words = [part for part in code.split("-") if part]
        if len(words) < 2:
            continue
        if set(words) < ours:
            hits.append((code, url))
    if len(hits) != 1:
        return None
    code, url = hits[0]
    words = set(code.split("-"))
    rivals = [
        other
        for other in sibling_slugs
        if words <= set(normalize_code(other).split("-"))
    ]
    if rivals != [slug]:
        return None
    return url


def verdict_for(
    row: dict[str, str],
    *,
    pokedex: set[tuple[str, str]],
    codes: dict[tuple[int, str], str],
    names: list[tuple[int, str, str]],
    dex: int | None,
    label: str,
    sibling_labels: tuple[str, ...] = (),
    sibling_slugs: tuple[str, ...] = (),
    checked_sources: tuple[str, ...] = (),
    checked_urls: tuple[str, ...] = (),
) -> Verdict:
    """One draft. `codes` maps (dex, normalized id) to the page that had it."""
    value = row["value"]
    if _hard_non_costume(value):
        return Verdict(
            "reject-non-costume",
            "high",
            checked_sources,
            checked_urls,
            "This code is a battle form or an internal id, not a costume.",
        )
    if official_news(row.get("source_url", "")):
        return Verdict(
            "auto-approve",
            "high",
            ("pokemongolive.com",),
            (row["source_url"],),
            "Official Pokémon GO post already cited on this row.",
        )
    species_id = row["species_id"]
    if (species_id, value) not in pokedex or dex is None:
        return Verdict(
            "needs-review",
            "low",
            checked_sources,
            checked_urls,
            "Only one source lists this row, so it still needs a person.",
        )
    code = normalize_code(value)
    exact = codes.get((dex, code))
    if exact:
        return Verdict(
            "auto-approve",
            "high",
            checked_sources,
            _unique((exact, *checked_urls)),
            "The game id is in the pokedex import and on the event-form list.",
        )
    species_names = [(name, url) for ndex, name, url in names if ndex == dex]
    named = _name_url(label, species_names, sibling_labels)
    if named:
        return Verdict(
            "auto-approve",
            "medium",
            checked_sources,
            _unique((named, *checked_urls)),
            "The pokedex lists this code, and the event-form list names this costume.",
        )
    species_codes = {item: url for (ndex, item), url in codes.items() if ndex == dex}
    subset = _subset_url(value, species_codes, sibling_slugs)
    if subset:
        return Verdict(
            "auto-approve",
            "medium",
            checked_sources,
            _unique((subset, *checked_urls)),
            "The pokedex lists this code, and the event-form list uses the same words.",
        )
    if _PLACEHOLDER.fullmatch(value):
        return Verdict(
            "reject-non-costume",
            "high",
            checked_sources,
            checked_urls,
            "This numbered costume id is not on the event-form list.",
        )
    return Verdict(
        "needs-review",
        "low",
        checked_sources,
        checked_urls,
        "The game-data import lists this code, and no second source confirmed it.",
    )


def _unique(urls: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.append(url)
    return tuple(seen)
