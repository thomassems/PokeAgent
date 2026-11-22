"""Collection checklists. Items come from approved curated facts.

A collection is a species plus fact kinds. Adding the rest of the dex is
another definition in data/collections.json and more approved rows. This
module does not fetch announcements.

Checklists are free. checklists_open is the only place a later entitlement
check belongs.
"""

import json
from pathlib import Path
from typing import Any

from data.go_catalog import EntryFlags, variant_label
from services.catalog import species_by_id
from services.curation import approved_facts, init_curation
from services.lists import (
    add_entry,
    delete_entry,
    init_lists,
    list_entries,
    update_entry,
)

_PATH = Path(__file__).resolve().parents[1] / "data" / "collections.json"
_ITEM_KINDS = {"costume", "background"}


def checklists_open(user: dict[str, Any]) -> bool:
    """Free for every current account.

    Billing is not built, so there is no entitlement column to read. When
    Thomas moves checklists to a paid tier, this function is the gate.
    """
    del user
    return True


def _definitions() -> list[dict[str, Any]]:
    raw = json.loads(_PATH.read_text())["collections"]
    definitions: list[dict[str, Any]] = []
    for item in raw:
        kinds = tuple(item["kinds"])
        if not kinds or any(kind not in _ITEM_KINDS for kind in kinds):
            raise ValueError(f"Collection '{item['id']}' has an unknown kind.")
        definitions.append(
            {
                "id": item["id"],
                "title": item["title"],
                "summary": item["summary"],
                "species_id": item["species_id"],
                "kinds": kinds,
            }
        )
    return definitions


def _definition(collection_id: str) -> dict[str, Any]:
    for item in _definitions():
        if item["id"] == collection_id:
            return item
    raise LookupError("That collection does not exist.")


def _require_open(user: dict[str, Any]) -> None:
    if not checklists_open(user):
        raise PermissionError("Checklists are not on this account.")


def _game_data_only(fact: dict[str, Any]) -> bool:
    """True when the verifier approved this row from the pokedex alone."""
    raw = fact.get("verification") or ""
    if not raw:
        return False
    parsed = json.loads(raw) if isinstance(raw, str) else raw
    return isinstance(parsed, dict) and parsed.get("verdict") == "game_data_only"


def _matches(entry: dict[str, Any], species_id: str, kind: str, value: str) -> bool:
    if entry["species_id"] != species_id:
        return False
    if kind == "costume":
        return bool(entry["costume"]) and entry["form"] == value
    return entry["background"] == value


def _items(definition: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per approved costume or background. Drafts are not counted."""
    init_curation()
    species = species_by_id(definition["species_id"])
    if species is None:
        raise ValueError(f"Unknown species '{definition['species_id']}'.")
    shiny_for = {
        "costume": set(species.shiny_costumes),
        "background": set(species.shiny_backgrounds),
    }
    chosen: dict[tuple[str, str], dict[str, Any]] = {}
    for fact in approved_facts():
        if fact["species_id"] != definition["species_id"]:
            continue
        if fact["kind"] not in definition["kinds"]:
            continue
        value = str(fact["value"])
        key = (fact["kind"], value)
        current = chosen.get(key)
        if current is None or fact["verified_at"] < current["verified_at"]:
            chosen[key] = fact
    items: list[dict[str, Any]] = []
    for (kind, value), fact in chosen.items():
        items.append(
            {
                "kind": kind,
                "value": value,
                "label": variant_label(kind, value),
                "species_id": species.id,
                "dex": species.dex,
                "name": species.name,
                "types": list(species.types),
                "shiny_released": value in shiny_for[kind],
                "from_game_data": _game_data_only(fact),
                "source_url": fact["source_url"],
                "verified_at": fact["verified_at"],
            }
        )
    items.sort(key=lambda item: (item["kind"], item["label"].lower()))
    return items


def _flags(kind: str, value: str, shiny: bool) -> EntryFlags:
    if kind == "costume":
        return EntryFlags(form=value, costume=True, shiny=shiny)
    return EntryFlags(background=value, shiny=shiny)


def _flags_from_entry(entry: dict[str, Any], shiny: bool) -> EntryFlags:
    return EntryFlags(
        form=entry["form"],
        shiny=shiny,
        dynamax=entry["dynamax"],
        gigantamax=entry["gigantamax"],
        shadow=entry["shadow"],
        purified=entry["purified"],
        lucky=entry["lucky"],
        costume=entry["costume"],
        background=entry["background"],
        notes=entry["notes"],
    )


def _view(user_id: int, definition: dict[str, Any]) -> dict[str, Any]:
    items = _items(definition)
    entries = list_entries(user_id)
    owned_count = 0
    for item in items:
        haves = [
            entry
            for entry in entries
            if entry["kind"] == "have"
            and _matches(entry, item["species_id"], item["kind"], item["value"])
        ]
        item["owned"] = bool(haves)
        item["shiny"] = any(entry["shiny"] for entry in haves)
        if item["owned"]:
            owned_count += 1
    return {
        "id": definition["id"],
        "title": definition["title"],
        "summary": definition["summary"],
        "have": owned_count,
        "total": len(items),
        "items": items,
    }


def list_collections(user: dict[str, Any]) -> list[dict[str, Any]]:
    _require_open(user)
    summaries = []
    for definition in _definitions():
        view = _view(user["id"], definition)
        summaries.append(
            {
                "id": view["id"],
                "title": view["title"],
                "summary": view["summary"],
                "have": view["have"],
                "total": view["total"],
            }
        )
    return summaries


def get_collection(user: dict[str, Any], collection_id: str) -> dict[str, Any]:
    _require_open(user)
    return _view(user["id"], _definition(collection_id))


def set_owned(
    user: dict[str, Any],
    collection_id: str,
    kind: str,
    value: str,
    owned: bool,
    shiny: bool,
) -> dict[str, Any]:
    _require_open(user)
    definition = _definition(collection_id)
    if kind not in definition["kinds"]:
        raise ValueError("That item is not in this collection.")
    needle = value.strip().lower()
    match = next(
        (
            item
            for item in _items(definition)
            if item["kind"] == kind and item["value"] == needle
        ),
        None,
    )
    if match is None:
        raise ValueError("That item is not in this collection.")
    init_lists()
    entries = list_entries(user["id"])
    haves = [
        entry
        for entry in entries
        if entry["kind"] == "have"
        and _matches(entry, match["species_id"], kind, needle)
    ]
    if not owned:
        for entry in haves:
            delete_entry(user["id"], entry["id"])
    elif haves:
        update_entry(user["id"], haves[0]["id"], _flags_from_entry(haves[0], shiny))
    else:
        add_entry(
            user["id"],
            "have",
            _flags(kind, needle, shiny),
            match["species_id"],
        )
    return _view(user["id"], definition)


def add_missing_wants(user: dict[str, Any], collection_id: str) -> dict[str, Any]:
    """Add a want row for each verified item the trainer does not own."""
    _require_open(user)
    definition = _definition(collection_id)
    view = _view(user["id"], definition)
    entries = list_entries(user["id"])
    added = 0
    for item in view["items"]:
        if item["owned"]:
            continue
        already = any(
            entry["kind"] == "want"
            and _matches(entry, item["species_id"], item["kind"], item["value"])
            for entry in entries
        )
        if already:
            continue
        add_entry(
            user["id"],
            "want",
            _flags(item["kind"], item["value"], False),
            item["species_id"],
        )
        added += 1
    refreshed = _view(user["id"], definition)
    refreshed["added"] = added
    return refreshed
