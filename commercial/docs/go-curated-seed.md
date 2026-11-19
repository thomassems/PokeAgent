# Curated seed: what was checked

Checked by opening the pages below on 18 November 2026 and restating them.
The app does not download these pages. This is not a full shiny dex and not
a full Dynamax dex. Rows are in `backend/data/go_curated_seed.json`.

## Dynamax debut

Source: <https://pokemongolive.com/post/go-big-dynamax/>

The 10 September 2024 post names Bulbasaur, Charmander, Squirtle, Skwovet,
and Wooloo as Dynamax debuts in one-star Max Battles, and marks each as a
possible shiny. It also says a Pokémon caught from those battles, and its
evolutions, can Dynamax. The seed therefore includes Ivysaur, Venusaur,
Charmeleon, Charizard, Wartortle, Blastoise, Greedent, and Dubwool as
Dynamax, and not as shiny. The post does not mark the evolutions shiny.

## Gigantamax Machamp day

Source: <https://pokemongolive.com/post/gigantamax-machamp-max-battle-day>

The 25 May 2025 post debuts Gigantamax Machamp and marks it as a possible
shiny. Timed Research offers a Dynamax Beldum, also marked as a possible
shiny. No other Dynamax species is named there, so none were added from
this page.

## Water Festival 2025

Source: <https://pokemongolive.com/en/post/water-festival-2025/>

The July 2025 post marks these as possible shinies in the wild or in raids:
Squirtle, Slowpoke, Krabby, Staryu, Magikarp, Marill, Barboach, Clamperl,
Buizel, Finneon, Wimpod, Feebas, Tirtouga, Shellder, Ducklett, and Gyarados.
It also names a higher chance of shiny Staryu and shiny Tirtouga. Lapras
wearing a scarf is a raid boss marked as a possible shiny, so Lapras has a
shiny row and a costume row with the value `scarf`. Tatsugiri is a debut in
that post and is not marked shiny, so it is not in the seed.

## Trade rule

Source: <https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/96-trading-pokemon/?l=en&p=web>

The Help Center says Mythical Pokémon, with Mew as the example, cannot be
traded. The seed applies that sentence to every released base species the
PvPoke file tags mythical, except Meltan and Melmetal. That page does not
state an exception for those two, and an earlier review could not confirm
one, so they stay tradable until someone pastes a page that decides it.

## Left out on purpose

- A 2026 "Big Footprints" post was only opened in Japanese during this
  check, so Eternatus and the "all previous Dynamax" line are not in the
  seed.
- Anything shiny or Dynamax that is not named on the four pages above.
- PokeMiners, Bulbapedia, LeekDuck, and ScrapedDuck.
