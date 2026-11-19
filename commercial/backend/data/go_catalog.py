"""Base GO catalog from PvPoke and PokéAPI, plus pure fact overlay.

Shiny, Dynamax, Gigantamax, costumes, and trade blocks come from curated
facts (see services/curation.py). This module does not read the database.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_PATH = Path(__file__).parent / "go_base.json"
_LABELS = Path(__file__).parent / "go_labels.json"
_FACT_KINDS = {
    "shiny",
    "dynamax",
    "gigantamax",
    "costume",
    "trade_rule",
    "background",
    "dynamax_costume",
    "gigantamax_costume",
    "costume_shiny",
    "background_shiny",
}
_AXES = (
    "shiny",
    "dynamax",
    "gigantamax",
    "shadow",
    "purified",
    "lucky",
    "costume",
)
_AXIS_LABELS = {
    "shiny": "Shiny",
    "dynamax": "Dynamax",
    "gigantamax": "Gigantamax",
    "shadow": "Shadow",
    "purified": "Purified",
    "lucky": "Lucky",
    "costume": "Costume",
}


class Species(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    dex: int = Field(ge=0)
    name: str
    types: list[str] = Field(min_length=1, max_length=2)
    forms: list[str] = Field(default_factory=list)
    costume_forms: list[str] = Field(default_factory=list)
    backgrounds: list[str] = Field(default_factory=list)
    shiny_costumes: list[str] = Field(default_factory=list)
    shiny_backgrounds: list[str] = Field(default_factory=list)
    dynamax_costume: bool = False
    gigantamax_costume: bool = False
    shiny: bool
    dynamax: bool
    gigantamax: bool
    shadow: bool
    costume: bool
    regional: bool
    mythical: bool
    legendary: bool
    tradable: bool
    untradeable_hint: bool = False


class EntryFlags(BaseModel):
    form: str = ""
    shiny: bool = False
    dynamax: bool = False
    gigantamax: bool = False
    shadow: bool = False
    purified: bool = False
    lucky: bool = False
    costume: bool = False
    background: str = ""
    notes: str = ""


def _load() -> tuple[Species, ...]:
    raw = json.loads(_PATH.read_text())["species"]
    species = tuple(Species.model_validate(row) for row in raw)
    ids = [item.id for item in species]
    if len(ids) != len(set(ids)):
        raise ValueError("Catalog ids must be unique.")
    return species


@lru_cache(maxsize=1)
def base_catalog() -> tuple[Species, ...]:
    """Species identity only. Curated flags are applied by the caller."""
    return _load()


def catalog() -> tuple[Species, ...]:
    """Base rows. Callers that show GO flags should use services.catalog."""
    return base_catalog()


@lru_cache(maxsize=1)
def variant_labels() -> dict[str, dict[str, str]]:
    """Display names for costume and background slugs. Data, not code."""
    raw = json.loads(_LABELS.read_text())
    return {
        "costume": dict(raw.get("costume", {})),
        "background": dict(raw.get("background", {})),
    }


def variant_label(kind: str, value: str) -> str:
    """The curated label, or the slug with spaces and a capital first letter."""
    named = variant_labels().get(kind, {}).get(value)
    if named:
        return named
    words = value.replace("-", " ").strip()
    if not words:
        return value
    return words[0].upper() + words[1:]


def apply_facts(species: Species, facts: list[dict[str, Any]]) -> Species:
    """Copy a base row and turn on the approved facts for that species."""
    shiny = species.shiny
    dynamax = species.dynamax
    gigantamax = species.gigantamax
    costume = species.costume
    tradable = species.tradable
    forms = list(species.forms)
    costume_forms = list(species.costume_forms)
    backgrounds = list(species.backgrounds)
    shiny_costumes = list(species.shiny_costumes)
    shiny_backgrounds = list(species.shiny_backgrounds)
    dynamax_costume = species.dynamax_costume
    gigantamax_costume = species.gigantamax_costume
    for fact in facts:
        if fact.get("status") not in (None, "approved"):
            continue
        if fact.get("species_id") != species.id:
            continue
        kind = fact.get("kind")
        if kind not in _FACT_KINDS:
            continue
        value = str(fact.get("value") or "")
        if kind == "shiny" and value == "true":
            shiny = True
        elif kind == "dynamax" and value == "true":
            dynamax = True
        elif kind == "gigantamax" and value == "true":
            gigantamax = True
        elif kind == "costume" and value:
            costume = True
            if value not in forms:
                forms.append(value)
            if value not in costume_forms:
                costume_forms.append(value)
        elif kind == "trade_rule" and value == "untradable":
            tradable = False
        elif kind == "background" and value:
            if value not in backgrounds:
                backgrounds.append(value)
        elif kind == "dynamax_costume" and value == "true":
            dynamax_costume = True
        elif kind == "gigantamax_costume" and value == "true":
            gigantamax_costume = True
        elif kind == "costume_shiny" and value:
            shiny = True
            if value not in shiny_costumes:
                shiny_costumes.append(value)
        elif kind == "background_shiny" and value:
            shiny = True
            if value not in shiny_backgrounds:
                shiny_backgrounds.append(value)
    return species.model_copy(
        update={
            "shiny": shiny,
            "dynamax": dynamax,
            "gigantamax": gigantamax,
            "costume": costume,
            "tradable": tradable,
            "forms": forms,
            "costume_forms": costume_forms,
            "backgrounds": backgrounds,
            "shiny_costumes": shiny_costumes,
            "shiny_backgrounds": shiny_backgrounds,
            "dynamax_costume": dynamax_costume,
            "gigantamax_costume": gigantamax_costume,
        }
    )


def species_by_id(species_id: str) -> Species | None:
    for item in catalog():
        if item.id == species_id:
            return item
    return None


def available_variants(species: Species) -> dict[str, Any]:
    """Status of each axis: verified, unknown, or unavailable.

    A sourced fact, or a released shadow form from PvPoke, is verified.
    Lucky is verified when the species can be traded, and unavailable when a
    trade rule blocks it, because lucky is a trade outcome. Everything else
    with no allowed source is unknown: the UI may offer it, and the API does
    not treat that gap as proof the variant does not exist.

    A background is not an unknown free-text field. It is offered only when a
    curated row names it. Purified follows shadow, because that is the
    Pokémon you purify. Neither purified nor lucky is its own curated fact.
    """
    sourced = "verified"
    missing = "unknown"
    return {
        "shiny": sourced if species.shiny else missing,
        "dynamax": sourced if species.dynamax else missing,
        "gigantamax": sourced if species.gigantamax else missing,
        "shadow": sourced if species.shadow else missing,
        "purified": sourced if species.shadow else missing,
        "lucky": "verified" if species.tradable else "unavailable",
        "costume": sourced if species.costume_forms else missing,
        "forms": list(species.forms),
        "costume_forms": list(species.costume_forms),
        "backgrounds": [
            {"id": item, "label": variant_label("background", item)}
            for item in species.backgrounds
        ],
        "shiny_costumes": list(species.shiny_costumes),
        "shiny_backgrounds": list(species.shiny_backgrounds),
        "dynamax_costume": species.dynamax_costume,
        "gigantamax_costume": species.gigantamax_costume,
    }


def unverified_labels(species: Species, flags: EntryFlags) -> list[str]:
    """Axes the trainer asked for that no allowed source has confirmed."""
    options = available_variants(species)
    labels: list[str] = []
    for axis in _AXES:
        if getattr(flags, axis) and options[axis] == "unknown":
            labels.append(_AXIS_LABELS[axis])
    return labels


def check_variant_filter(species: Species, flags: EntryFlags) -> None:
    """Reject a combination a source rules out. Unknown axes are allowed."""
    options = available_variants(species)
    form = flags.form.strip().lower()
    background = flags.background.strip().lower()
    known_forms = set(options["forms"]) | set(options["costume_forms"])
    sourced_backgrounds = {item["id"] for item in options["backgrounds"]}
    if form and form not in known_forms:
        raise ValueError(f"{species.name} has no {form} form in this catalog.")
    if flags.dynamax and flags.gigantamax:
        raise ValueError("Pick Dynamax or Gigantamax, not both.")
    if flags.shadow and flags.purified:
        raise ValueError("A Pokémon is shadow or purified, not both.")
    if flags.lucky and options["lucky"] == "unavailable":
        raise ValueError(f"{species.name} cannot be lucky because it cannot be traded.")
    if flags.dynamax and flags.costume and not species.dynamax_costume:
        raise ValueError(
            f"{species.name} has no released Dynamax costume. "
            "Dynamax is separate from costume."
        )
    if flags.gigantamax and flags.costume and not species.gigantamax_costume:
        raise ValueError(
            f"{species.name} has no released Gigantamax costume. "
            "Gigantamax is separate from costume."
        )
    if flags.costume and form and form not in options["costume_forms"]:
        raise ValueError(f"That form is not a costume for {species.name}.")
    if flags.costume and not form and options["costume"] == "verified":
        raise ValueError(f"Pick a costume {species.name} actually has.")
    if form in options["costume_forms"] and not flags.costume:
        raise ValueError(f"{form} is a costume. Mark it as a costume.")
    if background and background not in sourced_backgrounds:
        raise ValueError(f"{species.name} has no sourced {background} background.")
    if len(flags.notes) > 280:
        raise ValueError("Notes are limited to 280 characters.")


def check_entry(species: Species, flags: EntryFlags) -> None:
    """Reject a list row the catalog says cannot exist or cannot be traded."""
    if not species.tradable:
        if species.mythical:
            raise ValueError(
                f"{species.name} is a Mythical Pokémon and cannot be traded."
            )
        raise ValueError(f"{species.name} cannot be traded.")
    check_variant_filter(species, flags)


def filter_catalog(
    species: tuple[Species, ...] | list[Species] | None = None,
    *,
    query: str = "",
    shiny: bool = False,
    dynamax: bool = False,
    gigantamax: bool = False,
    shadow: bool = False,
    costume: bool = False,
    regional: bool = False,
    mythical: bool = False,
    legendary: bool = False,
    purified: bool = False,
    lucky: bool = False,
    form: str = "",
) -> list[dict[str, Any]]:
    """AND the selected tags. An unselected tag does not filter."""
    needle = query.strip().lower()
    rows: list[dict[str, Any]] = []
    for item in base_catalog() if species is None else species:
        if needle and needle not in item.name.lower() and needle not in item.id:
            continue
        if shiny and not item.shiny:
            continue
        if dynamax and not item.dynamax:
            continue
        if gigantamax and not item.gigantamax:
            continue
        if shadow and not item.shadow:
            continue
        if costume and not item.costume:
            continue
        if purified and not item.shadow:
            continue
        if lucky and not item.tradable:
            continue
        wanted_form = form.strip().lower()
        known = set(item.forms) | set(item.costume_forms)
        if wanted_form and wanted_form not in known:
            continue
        if regional and not item.regional:
            continue
        if mythical and not item.mythical:
            continue
        if legendary and not item.legendary:
            continue
        rows.append(item.model_dump())
    rows.sort(key=lambda row: row["name"])
    return rows
