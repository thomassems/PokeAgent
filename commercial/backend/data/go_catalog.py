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
_FACT_KINDS = {"shiny", "dynamax", "gigantamax", "costume", "trade_rule"}


class Species(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    dex: int = Field(ge=0)
    name: str
    types: list[str] = Field(min_length=1, max_length=2)
    forms: list[str] = Field(default_factory=list)
    costume_forms: list[str] = Field(default_factory=list)
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


def apply_facts(species: Species, facts: list[dict[str, Any]]) -> Species:
    """Copy a base row and turn on the approved facts for that species."""
    shiny = species.shiny
    dynamax = species.dynamax
    gigantamax = species.gigantamax
    costume = species.costume
    tradable = species.tradable
    forms = list(species.forms)
    costume_forms = list(species.costume_forms)
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
    return species.model_copy(
        update={
            "shiny": shiny,
            "dynamax": dynamax,
            "gigantamax": gigantamax,
            "costume": costume,
            "tradable": tradable,
            "forms": forms,
            "costume_forms": costume_forms,
        }
    )


def species_by_id(species_id: str) -> Species | None:
    for item in catalog():
        if item.id == species_id:
            return item
    return None


def available_variants(species: Species) -> dict[str, Any]:
    """Which list and filter options this species actually has.

    Purified is offered only when a shadow form exists, because that is the
    Pokémon you purify. Lucky is offered only when the species can be traded,
    because lucky is a trade outcome. Neither is a separate curated fact.
    """
    return {
        "shiny": species.shiny,
        "dynamax": species.dynamax,
        "gigantamax": species.gigantamax,
        "shadow": species.shadow,
        "purified": species.shadow,
        "lucky": species.tradable,
        "costume": bool(species.costume_forms),
        "forms": list(species.forms),
        "costume_forms": list(species.costume_forms),
    }


def check_variant_filter(species: Species, flags: EntryFlags) -> None:
    """Reject a variant combination this species does not have."""
    options = available_variants(species)
    form = flags.form.strip().lower()
    known_forms = set(options["forms"]) | set(options["costume_forms"])
    if form and form not in known_forms:
        raise ValueError(f"{species.name} has no {form} form in this catalog.")
    if flags.shiny and not options["shiny"]:
        raise ValueError(f"{species.name} has no shiny variant in this catalog.")
    if flags.dynamax and not options["dynamax"]:
        raise ValueError(f"{species.name} has no Dynamax variant in this catalog.")
    if flags.gigantamax and not options["gigantamax"]:
        raise ValueError(f"{species.name} has no Gigantamax variant in this catalog.")
    if flags.dynamax and flags.gigantamax:
        raise ValueError("Pick Dynamax or Gigantamax, not both.")
    if flags.shadow and not options["shadow"]:
        raise ValueError(f"{species.name} has no shadow variant in this catalog.")
    if flags.purified and not options["purified"]:
        raise ValueError(
            f"{species.name} has no shadow form, so it cannot be purified."
        )
    if flags.shadow and flags.purified:
        raise ValueError("A Pokémon is shadow or purified, not both.")
    if flags.lucky and not options["lucky"]:
        raise ValueError(f"{species.name} cannot be lucky because it cannot be traded.")
    if flags.costume and form not in options["costume_forms"]:
        raise ValueError(f"Pick a costume {species.name} actually has.")
    if form in options["costume_forms"] and not flags.costume:
        raise ValueError(f"{form} is a costume. Mark it as a costume.")
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
