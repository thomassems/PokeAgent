"""Base catalog plus approved curated facts. Drafts stay out of this view."""

from typing import Any

from data.go_catalog import Species, apply_facts, base_catalog, filter_catalog
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
    for item in filter_catalog(_view(), **filters):
        item["checked_on"] = checked.get(item["id"])
        rows.append(item)
    return rows
