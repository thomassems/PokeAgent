"""Base catalog plus approved curated facts. Drafts stay out of this view."""

from typing import Any

from data.go_catalog import (
    Species,
    apply_facts,
    available_variants,
    base_catalog,
    filter_catalog,
)
from services.curation import approved_facts, init_curation


def _view() -> tuple[Species, ...]:
    init_curation()
    facts = approved_facts()
    return tuple(apply_facts(item, facts) for item in base_catalog())


def species_by_id(species_id: str) -> Species | None:
    for item in _view():
        if item.id == species_id:
            return item
    return None


def species_for_query(query: str) -> Species | None:
    """The one species whose id or name is the whole query, if there is one."""
    needle = query.strip().lower()
    if not needle:
        return None
    hits = [
        item for item in _view() if item.id == needle or item.name.lower() == needle
    ]
    if len(hits) == 1:
        return hits[0]
    return None


def form_exists(form: str) -> bool:
    wanted = form.strip().lower()
    if not wanted:
        return True
    return any(wanted in item.forms or wanted in item.costume_forms for item in _view())


def _checked_on(facts: list[dict[str, Any]]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for fact in facts:
        species_id = fact["species_id"]
        day = fact["verified_at"]
        if species_id not in latest or day > latest[species_id]:
            latest[species_id] = day
    return latest


def public_catalog(**filters: Any) -> list[dict[str, Any]]:
    facts = approved_facts()
    checked = _checked_on(facts)
    rows = []
    view = {item.id: item for item in _view()}
    for item in filter_catalog(tuple(view.values()), **filters):
        species = view[item["id"]]
        item["checked_on"] = checked.get(item["id"])
        item["variants"] = available_variants(species)
        rows.append(item)
    return rows
