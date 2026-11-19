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

## Checked again on 19 November 2026

These pages were opened in English and restated. The app still does not
download them.

### Forever Forward

Source: <https://pokemongolive.com/en/seasons/forever-forward>

The season runs 2 June 2026 to 8 September 2026. Under Max Pokémon debuts
it names Dynamax Electabuzz, Dynamax Magikarp, and Dynamax Feebas, then
says "and more". Those three are dynamax rows. The page does not call
them costumes, and it does not mark them shiny. Magikarp's shiny row is
still the Water Festival one. The words "and more" are not a species list,
so nothing else was added from that sentence.

### Delightful Days

Source: <https://pokemongolive.com/en/seasons/delightful-days>

The season runs 3 June 2025 to 2 September 2025. It names Gigantamax
Cinderace, Gigantamax Inteleon, and Dynamax Hatenna. Those three rows were
added. It does not mark them shiny. "Even more discoveries" and "more
Dynamax Pokémon" were not expanded.

### Gigantamax Snorlax Max Battle Day

Source: <https://pokemongolive.com/post/gigantamax-snorlax-max-battle-day/>

19 April 2025. Gigantamax Snorlax debuts and is marked as a possible shiny.
Timed Research offers Dynamax Machop, also marked as a possible shiny.
Both species gained those rows.

### Kanto Celebration

Source: <https://pokemongolive.com/post/pokemongo-kanto-celebration-2025/>

2 to 7 September 2025. Paid Special Research names Dynamax Articuno,
Dynamax Zapdos, and Dynamax Moltres, each marked as a possible shiny.
Wild encounters mark Chansey, Snorlax, and Abra as possible shinies.
Snorlax's shiny row comes from the Snorlax day post above. Chansey and
Abra gained shiny rows. "And more" was not expanded.

### Dynamax Trails

Source: <https://pokemongolive.com/en/news/dynamax-trails-eternamax-eternatus-2026>

16 to 23 November 2026. Max Battle catches can have a Special Background.
Every Dynamax Pokémon that has appeared may show up in those battles,
excluding Legendary and Mythical. The background value is `dynamax-trails`,
labelled "Dynamax Trails special background". It was added for each
non-legendary species the seed already marks Dynamax, including Magikarp.
It was not added for Articuno, Zapdos, or Moltres, because this post
excludes Legendary Pokémon from that battle pool.

The same post says Eternamax Eternatus darkens the sky. Trainers cannot
catch that form. The catchable Eternatus encounter is a GO Pass reward and
is not described as a Dynamax form, so Eternatus has no dynamax row and no
background row. The background is not stored under the name "dark skies".

## How a missing row is read

A species with no dynamax row is unknown, not "cannot Dynamax". The same
is true for shiny, Gigantamax, shadow, and costume. The list and filter
UI still offer those axes and mark them not yet verified. A background is
different: it appears only when a row names it. Dynamax plus a costume is
rejected unless a `dynamax_costume` row says that costume was released.
None of the pages above released a Dynamax costume.

## Left out on purpose

- Species hid inside "and more" on Forever Forward, Delightful Days, and
  Kanto Celebration.
- The specific Max Monday date for Magikarp. The season page names the
  debut. It does not name the Monday.
- Gigantamax backgrounds. Dynamax Trails talks about Dynamax catches.
- Shadow and lucky, beyond PvPoke's released shadow forms and the Help
  Center trade rule already in the seed.
- Costumes other than the Lapras scarf from the Water Festival post.
- PokeMiners, Bulbapedia, LeekDuck, and ScrapedDuck. Third-party Max Monday
  write-ups were not used as sources.
