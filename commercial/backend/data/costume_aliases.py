"""Community game ids that name a costume the official seed already has.

The official row keeps its slug, its source link, and its status. The
community row is marked merged so the same costume is not curated twice.
The `because` text is a phrase from that official row's own notes, which
were restated from pokemongolive.com. It is the reason the two slugs are
the same costume. Shiny is not copied from the game id.
"""

from typing import NamedTuple


class CostumeAlias(NamedTuple):
    species_id: str
    community: str
    official: str
    because: str


COSTUME_ALIASES: tuple[CostumeAlias, ...] = (
    CostumeAlias("pikachu", "holiday-2016", "festive-hat", "festive hats"),
    CostumeAlias("pikachu", "kanto-2020-noevolve", "charizard-hat", "Charizard"),
    CostumeAlias("pikachu", "johto-2020-noevolve", "umbreon-hat", "Umbreon"),
    CostumeAlias("pikachu", "hoenn-2020-noevolve", "rayquaza-hat", "Rayquaza"),
    CostumeAlias("pikachu", "sinnoh-2020-noevolve", "lucario-hat", "Lucario"),
    CostumeAlias("pikachu", "wcs-2022", "worlds-2022", "2022"),
    CostumeAlias("pikachu", "wcs-2023", "worlds-2023", "2023"),
    CostumeAlias("pikachu", "wcs-2024", "worlds-2024", "2024"),
    CostumeAlias("pikachu", "horizons", "caps-hat", "Cap's hat"),
    CostumeAlias("pikachu", "tcg-2022-noevolve", "tcg-hat", "TCG"),
    CostumeAlias("bulbasaur", "fall-2019", "shedinja-costume", "Shedinja"),
    CostumeAlias("charmander", "fall-2019", "cubone-costume", "Cubone"),
    CostumeAlias("squirtle", "fall-2019", "yamask-costume", "Yamask"),
    CostumeAlias("jigglypuff", "jan-2024", "ribbon", "2024"),
    CostumeAlias("wigglytuff", "jan-2024", "ribbon", "2024"),
    CostumeAlias("froakie", "fall-2024", "pokemon-halloween", "2024"),
    CostumeAlias("rowlet", "fall-2024", "pokemon-halloween", "2024"),
    CostumeAlias("wooloo", "winter-2024", "holiday-attire", "2024"),
    CostumeAlias("dubwool", "winter-2024", "holiday-attire", "Dubwool"),
    CostumeAlias("dedenne", "winter-2024", "holiday-attire", "2024"),
    CostumeAlias("teddiursa", "halloween-2025", "witch-hat", "2025"),
    CostumeAlias("ursaring", "halloween-2025", "witch-hat", "Ursaring"),
    CostumeAlias("ursaluna", "halloween-2025", "witch-hat", "Ursaluna"),
    CostumeAlias("noibat", "halloween-2025", "headband", "2025"),
    CostumeAlias("noivern", "halloween-2025", "headband", "Noivern"),
    CostumeAlias("psyduck", "swim-2025", "swim-ring", "swim ring"),
    CostumeAlias("psyduck", "holiday-2023", "holiday-attire", "holiday attire"),
    CostumeAlias("golduck", "holiday-2023", "holiday-attire", "2023"),
    CostumeAlias("falinks", "gofest-2025-train-conductor", "train-ing", "train-ing"),
)
