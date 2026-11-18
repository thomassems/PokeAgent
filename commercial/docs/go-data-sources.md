# GO species data for the Explorer and lists

Status: **research, then a choice.** Read on 17 November 2026. This is the
catalog behind the Explorer and the want/have lists: which species and forms
exist in Pokémon GO, and the tags shiny, Dynamax, Gigantamax, shadow,
costume, regional, and tradable or mythical.

The commercial app cannot use a source that forbids commercial use. A source
is used below only when the license text itself allows it. Where a file is
MIT or BSD but does not contain the tag, that gap is stated. It is not filled
in from a non-commercial wiki.

## Recommendation

Use a **small hand-curated seed** in `backend/data/go_catalog.json`, written
for this app. No third-party GO catalog is both clearly commercial-ok and
complete for the tags the Explorer filters on.

PvPoke is the closest commercial-ok file, and it is already fetched for
battle stats. Its gamemaster does not carry shiny availability, Dynamax,
Gigantamax, or costume. Its `untradeable` tag is also incomplete (Shaymin is
mythical there and is not tagged untradeable). Building the Explorer on it
would show those filters as empty, or would invent the missing flags.

TODO: replace the seed when a source publishes those tags under a license
that allows commercial use, with the attribution that license requires. Do
not fill the gap from PokeMiners, Bulbapedia, or an unlicensed scrape.

The seed is a starting list, not a complete GO dex. It will go stale. The
Explorer says so on the page.

## Sources

### PokeMiners game master

Link: [README](https://github.com/PokeMiners/game_masters/blob/master/README.md),
read 17 November 2026.

Quoted disclaimer:

> This repo is for educational use only. All content found within this repo
> is the property of The Pokemon Company and Niantic. PokeMiners did not
> create or modify any files found within this repo and all copyright belongs
> to the respective companies.

- Commercial use: **no.** Educational use only, and the files are described
  as TPC and Niantic property.
- Attribution: not offered as a grant.
- Freshness: high. The `latest` folder tracks the current game master.
- Risk: the file has the tags we want, and using it in a paid app is the
  thing the README forbids. The personal app already refused to fetch it
  for the same reason.

### pogoapi.net

Link: [legal notice](https://pogoapi.net/Legal/), read 17 November 2026.

Quoted notice:

> All information distributed here is provided as-is and we (the authors)
> cannot be responsible for your use of the information contained in or
> linked from PoGoAPI.net.

The [documentation](https://pogoapi.net/documentation/) says callers should
cache the JSON. It does not grant a license.

- Commercial use: **not clearly allowed.** "As-is" is a disclaimer, not a
  permission to sell a product on the data.
- Attribution: not stated.
- Freshness: the author says the data can become outdated.
- Risk: a paid app needs a grant we can point at. This page is not one.

### PvPoke gamemaster

Link: [MIT license](https://github.com/pvpoke/pvpoke/blob/master/LICENSE),
Copyright (c) 2019 pvpoke. Read 17 November 2026.

Quoted grant:

> Permission is hereby granted, free of charge, to any person obtaining a
> copy of this software and associated documentation files (the "Software"),
> to deal in the Software without restriction, including without limitation
> the rights to use, copy, modify, merge, publish, distribute, sublicense,
> and/or sell copies of the Software, and to permit persons to whom the
> Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in
> all copies or substantial portions of the Software.

The gamemaster checked the same day is
`src/data/gamemaster/pokemon.json` (1753 rows). Tags present on those rows:
`alolan`, `galarian`, `hisuian`, `paldean`, `regional`, `legendary`,
`mythical`, `shadow`, `shadoweligible`, `untradeable`, `mega`, `ultrabeast`,
and a few battle-list tags. Species ids contained no `costume`, `dynamax`,
`gigantamax`, or `shiny`.

- Commercial use: **yes, for PvPoke's repository**, if the MIT notice is
  kept. MIT does not grant rights in the game data PvPoke did not write.
- Attribution: the copyright line and the MIT notice. The footer already
  credits PvPoke for stats and rankings.
- Freshness: good for battle species. The file moves when the maintainer
  updates it.
- Risk: wrong tool for this catalog. Shiny, Dynamax, Gigantamax, and costume
  are absent. `untradeable` missed Shaymin Land on the day it was checked
  (`tags` were `mythical` only). Meltan is mythical and not `untradeable`,
  which matches the game, so the tag is not "every mythical".

Keep using PvPoke for `get_go_pokemon` and `get_pvp_rankings`. Do not use it
as the Explorer catalog.

### PokeAPI data

Link: [LICENSE.md](https://github.com/PokeAPI/pokeapi/blob/master/LICENSE.md).
Copyright (c) 2013-2023 Paul Hallett and PokéAPI contributors. The same file
says Pokémon and Pokémon character names are trademarks of Nintendo.

The license is BSD-style. Quoted conditions:

> Redistribution and use in source and binary forms, with or without
> modification, are permitted provided that the following conditions are met:
>
> Redistributions of source code must retain the above copyright notice,
> this list of conditions and the following disclaimer.
>
> Redistributions in binary form must reproduce the above copyright notice,
> this list of conditions and the following disclaimer in the documentation
> and/or other materials provided with the distribution.
>
> Neither the name of PokéAPI nor the names of its contributors may be used
> to endorse or promote products derived from this software without specific
> prior written permission.

- Commercial use: **yes, for the data and code PokeAPI publishes**, with the
  notice kept and without implying PokeAPI endorses the product. Sprite
  images are a different repository and are The Pokémon Company's art. This
  edition does not use those images.
- Attribution: the copyright notice in the docs, and a data credit in the
  footer. The credit is their name, which the license tells us to keep. It
  is not this product's name.
- Freshness: the baked main-series dex is already in the repo. It is not a
  GO release list.
- Risk: it does not say which GO forms are released, which can be shiny, or
  which can Dynamax. Using it as the Explorer would be a main-series list
  wearing a GO label.

### Bulbapedia

Link: [Bulbapedia:Copyrights](https://bulbapedia.bulbagarden.net/wiki/Bulbapedia:Copyrights),
read 17 November 2026.

Quoted statement:

> Original Bulbapedia content is licensed under the Creative Commons
> Attribution-NonCommercial-ShareAlike license. This basically means that:
>
> You may copy and modify Bulbapedia content, provided you attribute it to
> Bulbapedia.
>
> You may copy and modify Bulbapedia content, provided it is not for
> commercial purposes.
>
> You may copy and modify Bulbapedia content, provided the resulting work is
> also licensed under the same copyright as the Bulbapedia content.

Wikidata records that license as CC BY-NC-SA 2.5.

- Commercial use: **no.** NonCommercial is the point of the license.
- Attribution: required, and not sufficient, because commercial use is out.
- Freshness: high.
- Risk: the articles have the tags, and the license still forbids this app.

### Hand-curated seed

The file is written in this repository. We hold that text.

- Commercial use: **yes.** It is our list.
- Attribution: none owed for the seed itself. Species names remain Nintendo
  trademarks, which the footer disclaimer already states.
- Freshness: **poor.** Nothing updates it until a person edits the JSON.
- Risk: incomplete coverage, and a flag can be wrong. The page says the list
  is a seed. A wrong "tradable" flag is the serious one, so untradable
  mythicals in the seed are explicit, and Meltan and Melmetal stay tradable
  because that is the GO exception. Confirm that exception before launch.

## What was rejected

- Fetching the PokeMiners game master.
- Copying Bulbapedia tables.
- Treating pogoapi.net's disclaimer as permission.
- Pretending the PvPoke gamemaster knows shiny, Dynamax, and costume.
