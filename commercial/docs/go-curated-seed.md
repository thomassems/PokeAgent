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

## Pikachu costumes and backgrounds

Checked by opening the English pages on 19 November 2026 and restating them.
The app does not download these pages. This is the Pikachu slice of phase I,
not every costume the game has ever released. Rows are in
`backend/data/go_curated_seed.json`. Display names are in
`backend/data/go_labels.json`.

36 costume rows and 5 background rows were added for Pikachu. Where the
post says that costume can be shiny, a `costume_shiny` row uses the same
slug. Where a background encounter can be shiny, a `background_shiny` row
uses the background slug. A post that names the costume and does not attach
a shiny line has the costume only.

### Costumes

- Summer style, straw hat and sunglasses: <https://pokemongolive.com/en/news/birthday2018>
- Straw hat: <https://pokemongolive.com/en/news/strawhat>
- Halloween Mischief: <https://pokemongolive.com/en/news/halloween-2021>
- Pokémon TCG hat, shiny stated: <https://pokemongolive.com/en/news/Pokemon-TCG-Crossover-Event>
- Party hat, shiny stated: <https://pokemongolive.com/en/news/pokemon-festival-jakarta>
- Green T-shirt (Berry), Flying with green balloons, Flying with multicolored balloons, each shiny stated: <https://pokemongolive.com/en/news/pokemon-go-safari-zone-taipei>
- Purple T-shirt (Flower): <https://pokemongolive.com/en/news/safari-zone-singapore-2022-annoucement>
- Shaymin-inspired Gracidea flower, shiny stated: <https://pokemongolive.com/en/news/gofest2022-tickets-shaymin-fulldetails>
- Party top hat, shiny stated: <https://pokemongolive.com/en/news/new-years-2023>
- Holiday attire, shiny stated: <https://pokemongolive.com/en/news/winter-holiday-part-1-2023>
- Cherry blossoms, shiny stated: <https://pokemongolive.com/en/news/spring-into-spring-2023>
- Witch hat: <https://pokemongolive.com/en/news/halloween-part-1-2024>
- Saree, shiny stated: <https://pokemongolive.com/en/news/festival-of-lights-2024>
- Kurta, shiny stated: <https://pokemongolive.com/en/news/festival-of-lights-2025>
- Snowflake beanie, shiny stated: <https://pokemongolive.com/en/news/new-years-2025>
- From the July 2026 anniversary celebration, each with shiny stated: Tricks and Treats, Winter Carnival outfit, summer flair, dapper with red, yellow, and blue accents, safari hat, varsity jacket, amethyst crown, World Championships 2022, 2023, and 2024. <https://pokemongolive.com/en/news/special-anniversary-pikachu-celebration>
- Sun crown and moon crown, shiny stated: <https://pokemongolive.com/en/news/twilight-wishes-2026>
- Astronaut, shiny stated: <https://pokemongolive.com/en/news/world-space-week-2026>
- Batik shirt, shiny stated: <https://pokemongolive.com/en/news/patterns-of-the-wild-2026>
- Professor Willow's assistant, shiny stated: <https://pokemongolive.com/en/news/happy-birthday-professor-willow-2026>
- Hat and capelet, shiny stated: <https://pokemongolive.com/en/news/halloween-part-1-2026>
- PokéXciting (Blue): <https://pokemongolive.com/en/news/event-singapore-30th-anniversary-2026>

### Backgrounds on Pikachu

- Duolingo special background, shiny stated: <https://pokemongolive.com/en/news/duolingo-2026>
- Festival of Lights special background, shiny stated: the 2026 return of the saree and kurta. <https://pokemongolive.com/en/news/festival-of-lights-2026>
- Patterns of the Wild special background, shiny stated: the batik-shirt post above.
- Professor Willow assistant special background, shiny stated. The post says the background is team-leader-specific and does not name one art per team, so this is one row.
- Singapore location background, on PokéXciting Pikachu (Blue). Shiny is not stated.

The hand seed inserts these as approved, `verified_by` `hand-seed`, the same
way as the earlier rows. Rejecting one in `/curate` removes it from the
checklist total.

## How a missing row is read

A species with no dynamax row is unknown, not "cannot Dynamax". The same
is true for shiny, Gigantamax, shadow, and costume. The list and filter
UI still offer those axes and mark them not yet verified. A background is
different: it appears only when a row names it. Dynamax plus a costume is
rejected unless a `dynamax_costume` row says that costume was released.
None of the pages above released a Dynamax costume.

## Drafts checked on 20 November 2026

Thomas approved the rest of phases I and J. These rows are drafts. They
insert with status `draft` and stay off Explorer, lists, and checklist
totals until he approves them on `/curate`. The Pikachu rows from 19
November stay approved. A new shiny flag on an already approved costume is
its own draft `costume_shiny` row.

The pages were opened in English, or the English URL was opened when the
body was still the official post. `pokemongolive.com` news URLs often
redirect to `pokemongo.com/news`. The stored link is the `pokemongolive.com`
URL that was opened. Nothing was copied from LeekDuck, ScrapedDuck,
PokeMiners, Bulbapedia, or Serebii.

359 draft rows were added on top of the approved seed: costumes,
backgrounds, and shiny flags. 173 species have at least one costume or
background row, and each of those species has a collection. A species whose
rows are all drafts shows have 0 of 0 until approval.

Shiny is recorded only when the opened page stars that costume or
background, or says that one can be shiny. A section that says "if you are
lucky" without a star on the costume line does not get a shiny row.

Pumpkaboo and Gourgeist posts do not name a size. Those rows use the
average catalog id. The other sizes are unverified.

Road of Legends names a large raid pool that may have a Special Background.
Each named species is one background row. Formes that share a catalog id,
such as Deoxys and Genesect drives, are one row. A star on the raid boss is
not treated as shiny for the background.

### Pikachu confirmed in this pass

These were missing from the 19 November seed. Shiny follows the page.

- World Cap, shiny stated: <https://pokemongolive.com/news/animationweek2020>
- Flower crown, shiny stated: <https://pokemongolive.com/news/egg-citing-spring-surprise-2022>
- Pikachu Libre, shiny not stated: <https://pokemongolive.com/news/go-battle-league-hidden-gems>
- Flying, purple balloons, shiny stated: <https://pokemongolive.com/news/pokemon-go-safari-zone-singapore>
- Flying, 5-shaped balloon, shiny not stated: <https://pokemongolive.com/news/birthday2021>
- Flying Pikachu with no balloon color, shiny stated by a Shiny Icon On image: <https://pokemongolive.com/news/air-adventures-global>
- Okinawa kariyushi shirt, shiny not stated: <https://pokemongolive.com/news/flying-pikachu-2022>
- Cosmog-themed spacesuit, shiny stated: <https://pokemongolive.com/news/world-championships-event-2026>
- World Championships 2026, shiny stated: the same page
- Clone, shiny not stated: <https://pokemongolive.com/news/pokemonday2020>
- Beanie, shiny not stated: <https://pokemongolive.com/news/holiday2019>
- Festive hat, shiny not stated: <https://pokemongolive.com/news/holiday2016>
- Holiday hat, shiny not stated: <https://pokemongolive.com/news/holiday2021>
- 2020 holiday costume, garment not named, shiny not stated: <https://pokemongolive.com/news/holiday2020>
- Cake hat. The 2022 debut does not star it. The 2023 anniversary page does: <https://pokemongolive.com/news/pokemongo-7th-anniversary>
- Shaymin-inspired scarf, shiny stated: <https://pokemongolive.com/news/gofest2022-finale-event>
- Detective hat, shiny not stated: <https://pokemongolive.com/news/detective-pikachu-returns-event>
- Cap's hat, shiny stated: <https://pokemongolive.com/news/pokemon-horizons-anime-celebration>
- Dapper, without a color, shiny not stated: <https://pokemongolive.com/en/news/go-fest-2025-ultra-unlock-challenges>
- Team hat, shiny not stated: <https://pokemongolive.com/en/news/road-of-legends-2026>
- Festival of Colors 2026 special background, shiny stated: <https://pokemongolive.com/en/news/festival-of-colors-2026>

Draft shiny flags were also added for the witch hat (Halloween 2024 part 2)
and the purple T-shirt (Flower) (Safari Zone: Singapore). Those costumes
were already approved.

### Coverage pass on 20 November 2026

Community pages were used only as a name checklist. Bulbapedia's
[Pikachu (GO)](https://bulbapedia.bulbagarden.net/wiki/Pikachu_(GO)) event
forms table supplied the names. Nothing from that page was copied into a
row. Each new row below was restated from a page on pokemongolive.com that
was opened the same day. Shiny follows that official page.

Confirmed and added as drafts:

- Ash's famous hat, shiny not stated:
  <https://pokemongolive.com/en/post/birthday2017>
- Charizard hat, Umbreon hat, Rayquaza hat, and Lucario hat, shiny not
  stated. The lucky line on each week names a different species:
  <https://pokemongolive.com/en/post/throwbackchallenge2020>
- Mimikyu costume on Pikachu, shiny stated in the same sentence. The same
  page names Bulbasaur in a Shedinja costume, Charmander in a Cubone
  costume, and Squirtle in a Yamask costume, also shiny:
  <https://pokemongolive.com/en/post/halloween2019>

Fashion Week 2021, 2022, 2023, and 2025 were opened. The Pikachu line on
the 2023 page is summer flair, which was already approved. The other
Fashion Week costumes named there were already drafted. Fashion Week
2020, 2024, and 2026 slugs returned 404. Holiday 2017 calls the Pikachu
a familiar festive Pikachu and does not name a new garment, so no second
row was added.

### Community import on 20 November 2026

Thomas asked for a manual import of a public costume list. Decision 16
records the source choice. The file is the pokemon-go-api pokedex JSON.
The script is `commercial/backend/tools/import_community_variants.py`.
It is run by hand. It caches the download, and it does not store images
or announcement text.

The run on 20 November 2026 added 288 community costume drafts across 124
species, and 34 new checklists. Four existing rows gained a
`community_source_url` and were otherwise left alone: approved Pikachu
kurta, draft Pikachu kariyushi, and the draft Fashion Week 2025 rows for
Minccino and Cinccino. No shiny flags and no backgrounds were added.
That file has no background field, and a shiny image URL is present on
every asset, so it is not treated as a shiny release.

Pop Star, Rock Star, and Ph.D. are in the seed as community drafts.
The game ids are `POP_STAR`, `ROCK_STAR`, and `DOCTOR`. The Ph.D. label
is `doctor`.

Decision 18 approves a community row when the game id is also on the
event-form list. The rest stay drafts. A lawyer reviews the source before
anyone is charged.

### Alias merges on 20 November 2026

Some community game ids are the same costume as an official row. The
official row keeps its slug, link, and status. `community_aliases` stores
the game id. The community row is `merged` and points at the official slug
with `merged_into`, so `/curate` does not list it twice. The pairs are in
`data/costume_aliases.py`. Each one is there because the official notes,
already restated from pokemongolive.com, name that costume.

- Pikachu `holiday-2016` into festive hat
- Pikachu `kanto-2020-noevolve` into Charizard hat
- Pikachu `johto-2020-noevolve` into Umbreon hat
- Pikachu `hoenn-2020-noevolve` into Rayquaza hat
- Pikachu `sinnoh-2020-noevolve` into Lucario hat
- Pikachu `wcs-2022` into World Championships 2022
- Pikachu `wcs-2023` into World Championships 2023
- Pikachu `wcs-2024` into World Championships 2024
- Pikachu `horizons` into Cap's hat
- Pikachu `tcg-2022-noevolve` into the Pokémon TCG hat
- Bulbasaur `fall-2019` into the Shedinja costume
- Charmander `fall-2019` into the Cubone costume
- Squirtle `fall-2019` into the Yamask costume
- Jigglypuff and Wigglytuff `jan-2024` into the ribbon
- Froakie and Rowlet `fall-2024` into the Pokemon Halloween costume
- Wooloo, Dubwool, and Dedenne `winter-2024` into holiday attire
- Teddiursa, Ursaring, and Ursaluna `halloween-2025` into the witch hat
- Noibat and Noivern `halloween-2025` into the headband
- Psyduck `swim-2025` into the swim ring
- Psyduck and Golduck `holiday-2023` into holiday attire
- Falinks `gofest-2025-train-conductor` into Falinks in train-ing

No shiny row was added from a game id. Shiny stays unknown unless a
`costume_shiny` or `background_shiny` row was already in the seed.

### Verifier run on 20 November 2026

`uv run python -m tools.verify_costumes` judged every draft costume,
background, and shiny-variant row. 508 were auto-approved, 122 were left
as drafts, and 2 were rejected as internal costume slots (`pikachu`
`costume-1` and `raichu` `costume-1`). An official draft was approved
from the pokemongolive.com post already on the row. A community draft was
approved only when the pokedex id also matched the event-form list. The
list was read for the check. Its sentences were not copied. Pikachu's
checklist then has 104 verified rows: 98 costumes and 6 backgrounds.

### Verifier run on 21 November 2026

The same script read official posts for the 122 drafts. It approved 10,
merged 21 into the official row for that event, and merged one already
approved no-evolve slot (`pikachu` `gofest-2022-noevolve` into
`gofest-2022`). 91 stayed drafts. Pikachu's checklist stays at 104:
the new Indonesia 2025 shirt is one verified row, and the merged
no-evolve slot is no longer a second row. GO Tour letter codes and the
numbered Flying Pikachu and T-shirt ids stayed drafts. The posts do not
say which file is which, and the `-02` icons are different costumes,
not copies.

### Verifier run on 22 November 2026

The same script now approves a pokedex costume that no post corroborated.
Those 91 drafts became `game_data_only`: status `approved`, confidence
`low`, evidence the pokedex import URL, reason "present in game data; no
official post found". They count on checklists. They are not auto-verified,
and the script does not assign a color, a trainer, or a shiny release to
them. The two `costume-1` placeholder slots stay rejected. A row stays a
draft only when two sources name different costumes for the same id.
None of the 91 were that case. Pikachu's checklist counts the new rows.

### Still unverified

These names came up on a community list, or were already on the list from
the first pass. No official page that was opened names them, so they are
not in the database. The community page is named so the next lookup can
start there. It is not a source.

- Hoenn, Sinnoh, Unova, Kalos, Alola, Partner, Johto, and Galar caps.
  Bulbapedia's Pikachu in a cap article and the Pikachu (GO) event forms
  table use those names for the anime caps. The 2017 post confirms only
  "Ash's famous hat", which is the original cap. World Cap is already in
  the seed from the Animation Week post. Guessed news slugs returned 404.
- H.F. Custom Cap (2018), flower hat (2020) as a garment distinct from the
  flower crown, Explorer Pikachu (2020), New Year's hat (2020) as a
  garment distinct from the party hat, and Meloetta hat (2021). Named on
  Bulbapedia's Pikachu (GO) event forms table. No official page was opened.
- Pikachu Pop Star, Pikachu Rock Star, and Pikachu, Ph.D. Named on that
  same table. Pikachu Libre is already in the seed. The GO Fest 2021 slug
  returned 404.
- Dawn's hat, Lucas's hat, Rei's cap, and Akari's kerchief. Named on
  Bulbapedia's Pikachu (GO) event forms table for 2024. The Sinnoh Tour
  gameplay URLs that were opened returned 404, including
  gotour.pokemongolive.com event-gameplay.
- Brendan's hat, May's bow, Hilbert's hat, Hilda's hat, Nate's visor, and
  Rosa's visor. Named on that table. Hoenn Tour and Unova Tour slugs
  returned 404.
- Quartz, pyrite, malachite, and aquamarine crowns. The table lists them
  beside the amethyst crown, which is already approved. No page opened
  this pass names the other four.
- T-shirt years 2023 and 2024 beyond the green and purple shirts already
  in the seed. Named on that table. No new official shirt page was opened.
- Captain Pikachu. Named on that table for 2024. The Horizons post that is
  already the source for Cap's hat says "Cap's hat" and does not say
  Captain, so the two were not merged.
- Formal Pikachu as a name distinct from the dapper rows already in the
  seed. The table lists both. The anniversary page already used for the
  dapper rows was not re-read as a new garment.
- A Santa hat under those words. Holiday 2017 says a familiar festive
  Pikachu is back. Festive hat and holiday hat stay separate rows.
- A Fragment hat on a caught Pikachu. The FENDI x FRGMT page names avatar
  items. Further fragment slugs returned 404. Bulbapedia's table did not
  put a Fragment hat in the event-forms names read this pass.
- Flying Pikachu colors and years other than the rows already stored
  (no color named, green, multicolored, purple, and the 5-shaped balloon).
  The table lists Flying Pikachu for 2020, 2021, 2022 (Okinawa, green,
  purple), 2023, and 2024. The extra years and colors were not on an
  official page opened this pass.
- World Championships Pikachu before 2022, and 2025. The table lists 2022,
  2023, 2024, and 2026, which are already in the seed. Championship slugs
  for the missing years returned 404.
- Pumpkaboo and Gourgeist sizes other than average.
- Winter Holiday 2025 and 2026, Fashion Week 2024 and 2026, and the
  in-person Tour and GO Fest city pages that would name location cards
  species by species. Those slugs returned 404 or were not opened.
- Costumes hidden in "and more", and older events whose English page was
  not opened. A missing row is still unknown, not a denial.
- PokeMiners and ScrapedDuck. They were not used. LeekDuck, Serebii, and
  Pokémon GO Hub were not opened this pass. The guessed costume-list URLs
  returned 404.

## Left out on purpose

- Species hid inside "and more" on Forever Forward, Delightful Days, and
  Kanto Celebration.
- The specific Max Monday date for Magikarp. The season page names the
  debut. It does not name the Monday.
- Gigantamax backgrounds. Dynamax Trails talks about Dynamax catches.
- Shadow and lucky, beyond PvPoke's released shadow forms and the Help
  Center trade rule already in the seed.
- Costumes other than the Lapras scarf and the Pikachu rows, as of the 19
  November pass. The 20 November draft section above replaces this bullet.
  What is still unverified is listed there.
- Location cards and special backgrounds the posts did not attach to
  Pikachu. A Los Angeles location card on the Sinnoh Tour page is for
  Dialga and Palkia raid catches.
- Gigantamax Pikachu, from the March 2026 Max Battle Day post. That is a
  Gigantamax form, not a costume and not a background, so it is outside
  this slice.
- Pikachu Pumpkin Head on the 2021 Halloween post. That line is an avatar
  item, not a caught costume.
- Shiny for Summer Style, Straw Hat, Halloween Mischief, the purple
  T-shirt, the witch hat, and PokéXciting Pikachu (Blue). Those posts do
  not state it.
- PokeMiners and ScrapedDuck. They were not used. The 20 November coverage
  pass, above, is the one that read a community list for names only.
