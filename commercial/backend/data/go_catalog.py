"""Hand-curated Pokémon GO catalog. See docs/go-data-sources.md.

TODO: replace this seed when a commercial-ok source covers shiny, Dynamax,
Gigantamax, costume, and tradability. Do not fill those gaps from PokeMiners
or Bulbapedia.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_PATH = Path(__file__).parent / "go_catalog.json"


class Species(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    name: str
    types: list[str] = Field(min_length=1, max_length=2)
    forms: list[str] = Field(default_factory=list)
    shiny: bool
    dynamax: bool
    gigantamax: bool
    shadow: bool
    costume: bool
    regional: bool
    mythical: bool
    legendary: bool
    tradable: bool


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
    raw = json.loads(_PATH.read_text())
    species = tuple(Species.model_validate(row) for row in raw)
    ids = [item.id for item in species]
    if len(ids) != len(set(ids)):
        raise ValueError("Catalog ids must be unique.")
    return species


@lru_cache(maxsize=1)
def catalog() -> tuple[Species, ...]:
    return _load()


def species_by_id(species_id: str) -> Species | None:
    for item in catalog():
        if item.id == species_id:
            return item
    return None


def check_entry(species: Species, flags: EntryFlags) -> None:
    """Reject a list row the catalog says cannot exist or cannot be traded."""
    if not species.tradable:
        if species.mythical:
            raise ValueError(
                f"{species.name} is a Mythical Pokémon and cannot be traded."
            )
        raise ValueError(f"{species.name} cannot be traded.")
    form = flags.form.strip().lower()
    if form and form not in species.forms:
        raise ValueError(f"{species.name} has no {form} form in this catalog.")
    if flags.shiny and not species.shiny:
        raise ValueError(f"{species.name} is not marked shiny in this catalog.")
    if flags.dynamax and not species.dynamax:
        raise ValueError(f"{species.name} is not marked Dynamax in this catalog.")
    if flags.gigantamax and not species.gigantamax:
        raise ValueError(f"{species.name} is not marked Gigantamax in this catalog.")
    if flags.shadow and not species.shadow:
        raise ValueError(f"{species.name} is not marked shadow in this catalog.")
    if flags.costume and not species.costume:
        raise ValueError(f"{species.name} has no costume in this catalog.")
    if len(flags.notes) > 280:
        raise ValueError("Notes are limited to 280 characters.")


def filter_catalog(
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
) -> list[dict[str, Any]]:
    """AND the selected tags. An unselected tag does not filter."""
    needle = query.strip().lower()
    rows: list[dict[str, Any]] = []
    for item in catalog():
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
        if regional and not item.regional:
            continue
        if mythical and not item.mythical:
            continue
        if legendary and not item.legendary:
            continue
        rows.append(item.model_dump())
    rows.sort(key=lambda row: row["name"])
    return rows
