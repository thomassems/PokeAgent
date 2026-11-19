"""Merge a PvPoke gamemaster with PokéAPI dex numbers and names.

Pure: the caller loads the files. Shiny, Dynamax, Gigantamax, and costumes
are not in either source, so this module leaves them false.
"""

from typing import Any

# PvPoke ids that are not a simple underscore-to-hyphen PokéAPI slug.
_SLUG_ALIASES = {
    "nidoran_female": "nidoran-f",
    "nidoran_male": "nidoran-m",
    "mr_mime": "mr-mime",
    "mime_jr": "mime-jr",
    "ho_oh": "ho-oh",
    "porygon_z": "porygon-z",
    "type_null": "type-null",
    "jangmo_o": "jangmo-o",
    "hakamo_o": "hakamo-o",
    "kommo_o": "kommo-o",
    "sirfetchd": "sirfetchd",
    "mr_rime": "mr-rime",
    "farfetchd": "farfetchd",
    "flabebe": "flabebe",
    "tapu_koko": "tapu-koko",
    "tapu_lele": "tapu-lele",
    "tapu_bulu": "tapu-bulu",
    "tapu_fini": "tapu-fini",
}

_REGIONAL = {"alolan", "galarian", "hisuian", "paldean", "regional"}


def pokeapi_slug(species_id: str) -> str:
    if species_id in _SLUG_ALIASES:
        return _SLUG_ALIASES[species_id]
    return species_id.replace("_", "-")


def _base_id(species_id: str, known: set[str]) -> str:
    parts = species_id.split("_")
    for end in range(len(parts) - 1, 0, -1):
        prefix = "_".join(parts[:end])
        if prefix in known:
            return prefix
    return species_id


def _types(primary: dict[str, Any], info: dict[str, Any] | None) -> list[str]:
    if info and info.get("types"):
        return list(info["types"])
    types = [item for item in primary.get("types") or [] if item and item != "none"]
    return types or ["normal"]


def merge_catalog(
    pvpoke_rows: list[dict[str, Any]],
    national_dex: dict[str, int],
    names_and_types: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """One row per released base species. Forms hang off that row."""
    released = [row for row in pvpoke_rows if row.get("released")]
    known = {row["speciesId"] for row in released}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in released:
        grouped.setdefault(_base_id(row["speciesId"], known), []).append(row)

    catalog: list[dict[str, Any]] = []
    for base, group in grouped.items():
        primary = next((row for row in group if row["speciesId"] == base), group[0])
        slug = pokeapi_slug(base)
        info = names_and_types.get(slug)
        dex = national_dex.get(slug)
        if dex is None:
            raw_dex = primary.get("dex")
            dex = int(raw_dex) if isinstance(raw_dex, int) else 0
        tags: set[str] = set()
        forms: list[str] = []
        shadow = False
        for row in group:
            tags.update(row.get("tags") or [])
            if "shadow" in (row.get("tags") or []):
                shadow = True
            if row["speciesId"] == base:
                continue
            form = row["speciesId"][len(base) + 1 :].replace("_", "-")
            if form == "shadow" or form.endswith("-shadow"):
                shadow = True
                continue
            if form and form not in forms:
                forms.append(form)
        forms.sort()
        catalog.append(
            {
                "id": base,
                "dex": dex,
                "name": info["name"] if info else primary.get("speciesName") or base,
                "types": _types(primary, info),
                "forms": forms,
                "shiny": False,
                "dynamax": False,
                "gigantamax": False,
                "shadow": shadow,
                "costume": False,
                "regional": bool(tags & _REGIONAL),
                "mythical": "mythical" in tags,
                "legendary": "legendary" in tags,
                "tradable": True,
                "untradeable_hint": "untradeable" in tags,
            }
        )
    catalog.sort(key=lambda row: (row["dex"], row["name"], row["id"]))
    ids = [row["id"] for row in catalog]
    if len(ids) != len(set(ids)):
        raise ValueError("Merged catalog ids must be unique.")
    return catalog
