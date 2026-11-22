"""Decide whether a costume draft is real enough to approve.

An official Pokémon GO post is a full approval on its own, because the post
is the release. A community id is fully approved when the same species and
code also appear on an independent event-form list. A pokedex id with no
second source is not that approval: the verifier records it later as
game_data_only. Two sources that name different costumes stay a draft.
The list is read for the check. Its sentences are not stored.
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


# A second pass reads official posts. A row is approved only when a post
# names that species in that costume. A game id is merged into an official
# row only when that post is the one the official row already cites and the
# id's year does not contradict the post. Numbered balloon and shirt ids
# stay drafts: the posts name the colors and do not number the files.

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_SEASONS = {
    "spring": {3, 4, 5},
    "summer": {6, 7, 8},
    "fall": {9, 10, 11},
    "winter": {12, 1, 2},
}
_CODE_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}
_BECAUSE = (
    "fashionable costume",
    "flower crown",
    "party hat",
    "Halloween 2022",
    "cempasuchil crown",
    "saree",
    "5-shaped balloon",
    "Ash's famous hat",
    "cherry blossoms",
)
# Game id, official slug, phrase the post must use, slug the post URL must use.
_EXPLICIT = (
    ("diwali-2024", "saree", "saree", "festival-of-lights-2024"),
    ("flying-5th-anniv", "flying-5-balloon", "5-shaped", "birthday2021"),
    ("one-year-anniversary", "ash-hat", "ash", "birthday2017"),
)
_DIRECT = (
    (
        "spring-2023-instinct",
        "elekid",
        "spark",
        "an-instinctive-hero",
        "The Instinctive Hero post says Elekid wears a Spark accessory.",
    ),
    (
        "spring-2023-mystic",
        "lapras",
        "blanche",
        "a-mystic-hero",
        "The Mystic Hero post says Lapras wears a Blanche accessory.",
    ),
    (
        "spring-2023-valor",
        "ponyta",
        "candela",
        "a-valorous-hero",
        "The Valorous Hero post says Ponyta wears a Candela accessory.",
    ),
    (
        "indonesia-2025-noevolve",
        "pikachu",
        "batik",
        "indonesia-journey-2025",
        "The Indonesia Journey 2025 post says Pikachu wears a batik shirt.",
    ),
)


@dataclass(frozen=True)
class Announcement:
    species: str
    phrase: str
    url: str


@dataclass(frozen=True)
class NewsResult:
    action: str
    official: str
    because: str
    url: str
    reason: str
    confidence: str


def url_slug(url: str) -> str:
    path = url.split("?", 1)[0].rstrip("/")
    return path.rsplit("/", 1)[-1].lower()


def parse_announcements(
    text: str, url: str, names: tuple[str, ...]
) -> list[Announcement]:
    """Species and costume phrase from one post. The post text is not kept."""
    cleaned = text.replace("’", "'").replace("‘", "'")
    found: list[Announcement] = []
    seen: set[tuple[str, str]] = set()

    def _add(name: str, raw: str) -> None:
        phrase = re.sub(r"\s+", " ", raw).strip(" *^")
        key = (name.lower(), phrase.lower())
        if phrase and key not in seen:
            seen.add(key)
            found.append(Announcement(name, phrase, url))

    for name in sorted(set(names), key=len, reverse=True):
        wearing = re.compile(
            rf"\b{re.escape(name)}\s+(?:wearing|adorned with)\s+"
            rf"(?:a |an )?([^.]{{2,80}})",
            re.IGNORECASE,
        )
        shirt = re.compile(
            rf"\b{re.escape(name)}\s+berkemeja\s+([A-Za-z]+)",
            re.IGNORECASE,
        )
        for pattern in (wearing, shirt):
            for match in pattern.finditer(cleaned):
                _add(name, match.group(1))
    # "Pikachu ... will be wearing Ash's famous hat" does not put the
    # name immediately before wearing. Take the nearest name in the window.
    for match in re.finditer(
        r"\b(?:wearing|adorned with)\s+(?:a |an )?([^.]{2,80})",
        cleaned,
        re.IGNORECASE,
    ):
        window = cleaned[max(0, match.start() - 80) : match.start()]
        nearest: tuple[int, str] | None = None
        for name in names:
            for hit in re.finditer(rf"\b{re.escape(name)}\b", window, re.IGNORECASE):
                if nearest is None or hit.start() > nearest[0]:
                    nearest = (hit.start(), name)
        if nearest:
            _add(nearest[1], match.group(1))
    for match in re.finditer(
        r"Flying Pikachu(?:\s+with\s+([^.]{3,80}))?", cleaned, re.IGNORECASE
    ):
        phrase = re.sub(r"\s+", " ", match.group(1) or "flying").strip()
        key = ("pikachu", phrase.lower())
        if key not in seen:
            seen.add(key)
            found.append(Announcement("Pikachu", phrase, url))
    return found


def _year(value: str) -> str:
    match = re.search(r"20\d\d", value)
    return match.group(0) if match else ""


def _month(value: str) -> int:
    for part in value.lower().split("-"):
        if part in _CODE_MONTHS:
            return _CODE_MONTHS[part]
    return 0


def _season(value: str) -> str:
    parts = set(value.lower().split("-"))
    for name in _SEASONS:
        if name in parts:
            return name
    return ""


def _months_named(text: str) -> set[int]:
    lowered = text.lower()
    return {number for name, number in _MONTHS.items() if name in lowered}


def _anniversary_year(url: str) -> str:
    match = re.search(r"(\d+)(?:st|nd|rd|th)-anniversary", url, re.IGNORECASE)
    if not match:
        return ""
    return str(2016 + int(match.group(1)))


def because_phrase(notes: str) -> str:
    for phrase in _BECAUSE:
        if phrase in notes:
            return phrase
    return ""


def _compatible(value: str, notes: str, url: str) -> bool:
    year = _year(value)
    if not year:
        return False
    blob = f"{notes} {url}"
    # The 8th-anniversary URL means 2024 only for an anniversary id.
    # A 2024 GO Fest id is not that party hat.
    anniversary = "anniversary" in value.split("-") and _anniversary_year(url) == year
    if year not in blob and not anniversary:
        return False
    extras = [
        part
        for part in value.split("-")
        if part
        not in {"noevolve", "spring", "summer", "fall", "winter", "anniversary"}
        and part not in _CODE_MONTHS
        and not re.fullmatch(r"20\d\d", part)
    ]
    if extras and not any(part in blob.lower() for part in extras):
        return False
    month = _month(value)
    if month and not re.search(rf"\b{_month_name(month)}\b", blob, re.IGNORECASE):
        return False
    season = _season(value)
    named = _months_named(notes)
    if season and named and not (named & _SEASONS[season]):
        return False
    if "anniversary" in value.split("-") and "anniversary" not in blob.lower():
        return False
    return True


def _month_name(number: int) -> str:
    for name, month in _MONTHS.items():
        if month == number:
            return name
    return ""


def _named(
    announcements: list[Announcement], species: str, slug: str
) -> list[Announcement]:
    return [
        item
        for item in announcements
        if item.species.lower() == species.lower() and url_slug(item.url) == slug
    ]


def news_result(
    *,
    species_id: str,
    value: str,
    species_name: str,
    official_rows: list[dict[str, object]],
    announcements: list[Announcement],
) -> NewsResult:
    """Merge into one official row, approve from one post, or leave it."""
    for code, official, needle, slug in _EXPLICIT:
        if species_id != "pikachu" or value != code:
            continue
        hits = [
            item
            for item in announcements
            if item.species.lower() == "pikachu"
            and slug in url_slug(item.url)
            and needle in item.phrase.lower()
        ]
        row = next(
            (item for item in official_rows if item.get("value") == official), None
        )
        because = because_phrase(str(row.get("notes", ""))) if row else ""
        if not hits or not because:
            return NewsResult(
                "leave",
                "",
                "",
                "",
                (
                    "The game-data import lists this code, and no "
                    "official post confirmed it."
                ),
                "low",
            )
        return NewsResult(
            "merge",
            official,
            because,
            hits[0].url,
            f"The official post names this costume, and the game id is {value}.",
            "high",
        )
    compatible = [
        row
        for row in official_rows
        if _compatible(value, str(row.get("notes", "")), str(row.get("source_url", "")))
    ]
    confirmed = []
    for row in compatible:
        slug = url_slug(str(row.get("source_url", "")))
        if _named(announcements, species_name, slug):
            confirmed.append(row)
    if len(confirmed) == 1:
        row = confirmed[0]
        because = because_phrase(str(row.get("notes", "")))
        if because:
            return NewsResult(
                "merge",
                str(row["value"]),
                because,
                str(row["source_url"]),
                "The official post for this event names this species in this costume.",
                "high",
            )
    if len(confirmed) > 1:
        return NewsResult(
            "conflict",
            "",
            "",
            "",
            "Official posts name more than one costume for this id.",
            "low",
        )
    for code, species, needle, slug, reason in _DIRECT:
        if value != code or species_id != species:
            continue
        hits = [
            item
            for item in announcements
            if item.species.lower() == species_name.lower()
            and slug in url_slug(item.url)
            and needle in item.phrase.lower()
        ]
        if hits:
            return NewsResult("approve", "", "", hits[0].url, reason, "high")
        return NewsResult(
            "leave",
            "",
            "",
            "",
            "The game-data import lists this code, and no official post confirmed it.",
            "low",
        )
    if value.startswith("fall-2022") and species_name in {"Pumpkaboo", "Gourgeist"}:
        hits = [
            item
            for item in announcements
            if item.species.lower() == species_name.lower()
            and "halloween-2022" in url_slug(item.url)
            and "spooky" in item.phrase.lower()
        ]
        if hits and not confirmed:
            return NewsResult(
                "approve",
                "",
                "",
                hits[0].url,
                "Halloween 2022 says this species wears a Spooky Festival costume.",
                "high",
            )
    return NewsResult(
        "leave", "", "", "", _leave_reason(value, species_name, announcements), "low"
    )


def _leave_reason(
    value: str, species_name: str, announcements: list[Announcement]
) -> str:
    own = [
        item for item in announcements if item.species.lower() == species_name.lower()
    ]
    phrases = " ".join(item.phrase.lower() for item in own)
    if re.fullmatch(r"flying-0\d", value) and "balloon" in phrases:
        return (
            "Official posts name Flying Pikachu balloon colors and do not "
            "say which numbered id is which."
        )
    if value.startswith("tshirt-") and "t-shirt" in phrases:
        return "Official posts name colored T-shirts and do not number these ids."
    if value == "may-2023" and "cherry blossom" in phrases:
        return "The April 2023 spring post names cherry blossoms, and this id says May."
    if value.endswith("-instinct") and species_name != "Elekid":
        if any("spark" in item.phrase.lower() for item in announcements):
            return (
                "The Instinctive Hero post names Elekid and does not name this species."
            )
    if value.endswith("-valor") and species_name != "Ponyta":
        if any("candela" in item.phrase.lower() for item in announcements):
            return "The Valorous Hero post names Ponyta and does not name this species."
    if value.startswith("gotour-"):
        return "No fetched official page names this GO Tour id."
    if value == "one-year-anniversary" and species_name != "Pikachu":
        if any("ash" in item.phrase.lower() for item in announcements):
            return (
                "The 2017 anniversary post names Pikachu in Ash's hat "
                "and does not name this species."
            )
    return "The game-data import lists this code, and no official post confirmed it."


def slot_stem(value: str) -> str:
    """Primary id when this code is a second slot of the same costume.

    `gotour-2024-a-02` can be that slot. `flying-02` is a numbered balloon,
    not a copy of `flying`. A trailing `noevolve` is the same costume on a
    Pokemon that does not evolve.
    """
    match = re.fullmatch(r"(.+-[abc])-02", value)
    if match:
        return match.group(1)
    if value.endswith("-noevolve"):
        return value[: -len("-noevolve")]
    return ""
