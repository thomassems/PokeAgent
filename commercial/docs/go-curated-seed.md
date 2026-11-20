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

### Still unverified

These were looked for on official pages and not put in the database.

- Ash caps other than World Cap and Cap's hat. Original, Kalos, Alola,
  Unova, Sinnoh, Johto, Galar, and partner caps. The guessed news slugs
  returned 404.
- A Santa hat under those words. The festive hat and holiday hat rows use
  the words the posts actually use. They may be the same garment. That was
  not assumed.
- Dawn, Lucas, Akari, and Rei costumes. The Sinnoh Tour gameplay URLs that
  were tried returned 404, including the Los Angeles event-gameplay page.
- A Fragment hat on Pikachu. The FENDI x FRGMT page names avatar items, not
  a caught Pikachu.
- Balloon colors other than green, multicolored, purple, and the 5-shaped
  balloon. The Okinawa post says differently colored balloons and names
  none.
- World Championships Pikachu before 2022. No English page naming one was
  opened.
- Pumpkaboo and Gourgeist sizes other than average.
- Winter Holiday 2025 and 2026, Fashion Week 2024 and 2026, and the in-person
  Tour and GO Fest city pages that would name location cards species by
  species. Those slugs returned 404 or were not opened.
- Costumes hidden in "and more", and older events whose English page was
  not opened. A missing row is still unknown, not a denial.
- PokeMiners, Bulbapedia, LeekDuck, ScrapedDuck, and Serebii. They were not
  used.

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
- PokeMiners, Bulbapedia, LeekDuck, ScrapedDuck, and Serebii. Third-party
  costume lists were not used as sources.
