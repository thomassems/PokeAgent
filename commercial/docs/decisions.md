# Commercial decision log

Choices for the Trainermon tree only. The personal app keeps its own log in
the repo root. A fix to code that still exists in both trees has to be applied
in both places.

## 1. Catalog is a hand-kept seed

Explorer and the want/have lists read `backend/data/go_catalog.json`.

Rejected: **PokeMiners game master**, educational use only, and the files are
Niantic and The Pokémon Company property. **Bulbapedia**, CC BY-NC-SA, which
blocks commercial use. **pogoapi.net**, no written licence. **PvPoke's
gamemaster**, MIT and fine to keep for battle stats, but it has no shiny,
Dynamax, Gigantamax, or costume fields, and its untradeable tag misses
species GO will not trade. **PokéAPI**, BSD and already used for the main
series, but it is not a GO release list.

The seed stays until a source has a written commercial grant covering those
fields. The comparison is in `docs/go-data-sources.md`. Decision 4
(17 November 2026) replaces the wait: the next catalog is PvPoke plus
PokéAPI, with a hand-curated GO layer on top. This seed stays until that
import lands.

Mew, Celebi, and Jirachi are blocked as untradable mythicals. Meltan and
Melmetal stay tradable because GO allows those two. That exception is still
open for Thomas to confirm.

## 2. Accounts are local SQLite until a host is wired

Sign-in is a SQLite file and a session cookie. Tests set `TRAINERMON_DB` and
need no secrets. `SHARE_FRIEND_CODES` defaults off and does not publish a
friend code. Search results are trainer name, city, and the matched Pokémon.

Rejected: **calling Supabase from this build**. It would add a dependency and
a secret before the contact method is chosen. The README records the free
Postgres tables for later. The app does not read a GO account and does not
offer account trading.

## 3. Trade search is not an agent

Overlap is a pure function: a have covers a want when the species and form
match and every true flag on the want is true on the have. City defaults to
Toronto. The assistant tab is unchanged and is not used here.

Rejected: **asking the model to rank partners**. Thomas asked for plain
filters, and a model call would make two trainers with the same lists get
different results.

## 4. Data setup: PvPoke, PokéAPI, and a curated GO layer

Decided 17 November 2026, from `docs/licensing-data-review.md` section 2.

The base catalog is PvPoke (MIT) plus PokéAPI (BSD) for species, forms,
types, stats, and moves. Keep both notices. On top of that, Trainermon keeps
its own GO layer: shiny, Dynamax, Gigantamax, costumes, raids, events, and
trade rules. Each row is restated by hand from an official announcement,
with a source link and a verified date. An AI may draft a row from text a
human pastes. A human approves the row before it is published. Moderated
user reports can correct it.

Hard rules:

- No PokeMiners files or assets.
- No Bulbapedia text copied into the repo. On 20 November 2026 Thomas
  allowed a community page to be read as a discovery checklist of names.
  Bulbapedia, LeekDuck, Serebii, Pokémon GO Hub, and the Fandom wiki are
  in that set. Their words, tables, and images are not stored and are not
  the source link on a row.
- No scraping of official Scopely or Niantic sites, including
  pokemongolive.com. Opening a named news URL to restate one announcement
  is the curated-layer method, not a crawl.
- No LeekDuck or ScrapedDuck data copied into the repo. A LeekDuck page
  may be read for a name to look up. ScrapedDuck stays unused.
- No reading of game accounts.

An official row still cites an official page: pokemongolive.com or
pokemongo.com news, the official Pokémon GO blog or X account, or
pokemon.com. Decision 16 is the exception. A community JSON import may
add a draft that cites that JSON URL. It does not replace an official row.

Rejected: **waiting for one licensed feed that already has shiny, Dynamax,
and costumes.** Nothing reviewed both allows commercial use and covers those
fields. Rejected: **copying PokeMiners, Bulbapedia, or a scraped event
feed.** Those are the paths the review ranked as not commercial-ok.

## 5. Do not ask other sites for a licence yet

Decided 17 November 2026.

Do not email LeekDuck, ScrapedDuck, Pokebattler, pogoapi.net, or anyone else
for a data licence yet.

Rejected: **sending those emails in parallel with the curated layer.** Thomas
wants the owned layer first. Asking later is still open. It is not this
plan.

## 6. Compact text rows, sprites later and off

Decided 17 November 2026, from the review's section 3.

Replace the large letter cards with compact text-first rows. A row leads
with a dex-number badge such as `#0131 Lapras`, then our own coloured type
labels (words, not the official type symbols), then variant chips: Shiny,
Dynamax, Gigantamax, costume, Lucky, Shadow.

Official sprites stay undecided until a lawyer consult. The plan keeps a
feature flag for them, default off. No sprite files ship with the flag.

Rejected: **commissioning original drawings of real Pokémon.** A redraw is
still a derivative of the character. Rejected: **turning sprites on now**
because the paid competitors do. The review treats that as tolerance, not
permission.

## 7. First paid feature is remote-raid matchmaking

Decided 17 November 2026.

The first feature meant to be paid is remote-raid matchmaking, with queue
priority for paying users. Lists, trade search, and Explorer stay the free
product. Trading stays a filter, not an assistant, and it is not the paid
anchor.

Rejected: **charging for trade search first.** The review found the trade
finders are free. Rejected: **paying hosts**, which is the PokeRaid
Frontliner shape. Scopely's terms ban performing services in the apps in
exchange for payment outside the apps.

## 8. Three prices, web-first Stripe

Decided 17 November 2026.

Tiers are Free, $4.99, and $9.99, each paid tier with an annual plan. The
annual amounts are not set. Billing is web-first Stripe, before any app
store. Test mode only until the open items in decision 10 are done and
Thomas says to charge.

Rejected: **a single $9.99 tier**, and **starting on the App Store or Play
Store.** Store review and store fees wait.

## 9. Age and contact at launch

Decided 17 November 2026.

The app is 13+ only. Friend codes are opt-in. There is no in-app chat at
launch.

Rejected: **a younger audience with parental consent flows**, and **direct
messages at launch.** Both add safety work the launch does not need. Trade
search still does not show a friend code. A raid lobby may show an opted-in
code to the people in that lobby, which phase E has to spell out before it
is built.

## 10. Lawyer and trademark search wait until before charging

Decided 17 November 2026.

A Canadian IP and privacy consult, and a CIPO and USPTO search for
"Trainermon", happen later. They are open items that must be done before
Trainermon charges money. Sprites stay off until that consult.

Rejected: **blocking the free catalog and row work on the consult.** Those
do not charge anyone. Rejected: **charging first and asking the lawyer
after.** Decision 8 keeps Stripe in test mode until this is done.

## 11. Build A, B, C, and G. Leave the paid phases unbuilt

Decided 18 November 2026, when Thomas approved those four phases from
`plan-next.md`.

Compact text rows replace the letter cards on lists, trade results, and
Explorer. The base catalog is generated from PvPoke and PokéAPI by
`scripts/refresh_base_catalog.py`. Curated facts live in their own table.
An admin pastes announcement text, a model may draft rows from that paste,
and a human approves them. Drafts are not public. Sign-up requires a 13+
confirmation. Privacy and terms pages are drafts.

No approver was named, so `TRAINERMON_ADMINS` is the allow-list. Empty means
nobody can curate. The old hand seed `backend/data/go_catalog.json` is gone.
Identity comes from `go_base.json`. GO flags come from approved curated rows.

Rejected for this build: **user reports, Stripe, raid matchmaking, and the
lawyer consult.** Those stay in the plan as D, F, E, and H.

## 12. Trainer profile and species-valid variants

Decided 19 November 2026, from Thomas's review of the commercial edition.

Sign-up and the profile editor collect trainer level (1 to 80), team, and a
timezone from a fixed list. The region is stored beside that zone so a later
raid lobby does not have to ask again. Friend codes stay optional and private.
`SHARE_FRIEND_CODES` still does not publish one.

List rows, trade search, and Explorer only offer a variant when the base
catalog plus approved curated facts say that species has it. Purified follows
shadow. Lucky follows tradable, because lucky is a trade outcome. The API
returns 400 for any other combination.

Rejected: **letting the trainer type a free-form timezone or a variant the
catalog does not have.**

## 13. Silent timezone, and unknown is not unavailable

Decided 19 November 2026, from Thomas's review of sign-up and of Magikarp.

Sign-up is three short steps: email and password with the 13+ confirmation,
then trainer name, team, and level, then an optional friend code that can
be skipped. City is not asked there. It stays on the profile and can be
blank. Trade search uses it when the trainer fills it in. The page reads
`Intl.DateTimeFormat().resolvedOptions().timeZone` and stores that IANA
zone. There is no timezone picker, and saving the profile does not change
the stored zone.

Variant axes are independent. Dynamax and Gigantamax are not costumes.
A costume combined with either is rejected unless a curated row says that
costume was released on that form. Background is its own axis and is
offered only when a curated row names one for that species. Magikarp is
Dynamax, from the Forever Forward season page, and can carry the Dynamax
Trails special background. It has no Dynamax costume.

A variant with no allowed source is `unknown`, not unavailable. The
checkbox stays, labelled not yet verified, and the API accepts the row.
Lucky on an untradable species stays rejected, because the Help Center
trade rule is a source. A background string that was never sourced stays
rejected. Explorer's broad tag filters still mean verified only, so
"show Gigantamax" does not return the whole dex.

Rejected: **asking for a timezone.** Raid apps collect trainer name, level,
and a friend code, and they do not ask for a zone. Rejected: **hiding an
unsourced Dynamax box.** That is what marked Magikarp as unable to Dynamax.
Rejected: **calling the Trails background "dark skies" in the data.** The
post names a Special Background. "Darkens the sky" is the Eternamax
Eternatus battle, and that form cannot be caught.

## 14. Pikachu checklist is free, and totals count verified rows

Decided 19 November 2026, when Thomas approved a Pikachu slice of phases I
and J from `plan-next.md`.

Checklists are free for now and are likely to move to a paid tier later.
Every collection route goes through `checklists_open` in
`services/collections.py`. That function returns true. There is no
entitlement column yet, because Stripe is still unbuilt. When Thomas turns
the gate on, the change is that function, not a new page.

A collection total counts approved curated rows only. A draft is not part
of Y. The first release is Pikachu costumes and Pikachu backgrounds. At
launch the same model should cover every Pokémon: another definition in
`data/collections.json` plus more approved rows, not a second checklist
page.

Hand-checked Pikachu rows are inserted as approved, with `verified_by`
`hand-seed`, the same way the earlier seed is. Thomas can reject a row in
`/curate`, and the count drops. A paste from the curation form still lands
as a draft. Shiny on a costume is its own fact (`costume_shiny`) when the
official post states it. A background encounter that can be shiny is
`background_shiny`.

Rejected: **gating the checklist in this build.** Thomas said free for now.
Rejected: **counting unknown costumes inside Y.** He said totals count
verified entries only. Rejected: **a Pikachu-only table.** The collection
id, species, and fact kinds live in data.

## 16. Community-sourced drafts are allowed, pending a lawyer

Decided 19 November 2026, when Thomas asked for a public list of every
costume and form variant and for a manual importer. Applied 20 November
2026.

The importer reads one file, the pokemon-go-api pokedex JSON at
`https://pokemon-go-api.github.io/pokemon-go-api/api/pokedex.json`. That
file is a structured list of costume ids and costume-like form ids,
including Pop Star, Rock Star, and Doctor, which is the Ph.D. costume.
It has no location backgrounds. Every asset carries a shiny image URL,
including costumes that were not released shiny, so the importer does not
write shiny flags from it.

The host has no robots.txt. The request returned 404. The importer still
sends a named User-Agent, waits a second between requests, and caches the
body. A second run reads the cache and does not add a duplicate row.

New rows are status `draft`, `source_type` `community`, with that JSON URL
and the fetch date. An existing official row with the same species, kind,
and slug is not overwritten. The importer only fills `community_source_url`.
`/curate` labels each draft Community or Official. No images and no
announcement prose are stored.

Rejected for this import:

- **ScrapedDuck.** AGPL-3.0, and its own terms say an application of the
  data cannot sit behind a paywall or ads. The published JSON is events
  and raids, not a costume index.
- **PokeMiners game master.** The upstream of the chosen file. About 19 MB,
  no license, and the asset repo says educational use only. This import
  does not download it.
- **pogo_assets.** Sprites and sounds. Not stored.
- **Bulbapedia.** HTML under CC BY-NC-SA. Used earlier as a name checklist
  only.
- **pogoapi.net.** All rights reserved, and the public files that were
  reviewed are release lists, not costumes.
- **Pokémon GO Hub.** No costume JSON from that site was opened.

These drafts are not a commercial grant. A lawyer reviews this source
before anyone is charged. Until then the drafts stay off Explorer and off
checklist totals.

## 17. A repeated community code is an alias, not a second costume

Decided 20 November 2026, when Thomas asked `/curate` to filter the queue,
show readable names, approve in bulk, and stop listing the same costume
twice.

Some ids in the pokemon-go-api pokedex are the game's code for a costume
the official seed already names. `hoenn-2020-noevolve` is the Rayquaza hat.
`wcs-2022` is World Championships 2022. `horizons` is Cap's hat.
`holiday-2016` is the festive hat. The full list is
`data/costume_aliases.py`. A pair is on that list only when the official
row's own notes, restated from pokemongolive.com, name that costume.

The official row keeps its slug, source link, and status.
`community_aliases` stores the game id. The community row becomes
`merged`, and `merged_into` points at the official slug. `/curate` hides
merged rows unless that status is selected. Approving a merged row is
refused, so the costume cannot be published twice. A later import still
sees the row and does not insert it again.

Community drafts that are not aliases stay drafts. An admin approves or
rejects them one at a time or in a batch. A batch writes the same
`verified_by` email a single approval writes. Shiny is `confirmed` only
when a `costume_shiny` or `background_shiny` row already exists, and
`unknown` otherwise. A shiny image URL in the pokedex file is still not
confirmation, which is decision 16.

Rejected: **deleting the community row.** The next import would add it
back as a new draft. Rejected: **marking every asset shiny** because the
file includes a shiny image for costumes that were not released shiny.

## 18. The verifier approves a costume when two sources agree

Decided 20 November 2026, when Thomas said he does not want to go through
and confirm every draft. The verifier should be able to tell whether a
costume or variant is real.

This supersedes the manual-approval part of decision 16, and the same
requirement as restated in decision 17. Community costume drafts no longer
wait for a person when the evidence agrees. The log has no decision 15.
The rule this replaces is decision 16's "these drafts stay drafts until
they are approved", which decision 17 repeated. Decision 11 still applies
to a row pasted on `/curate`: that paste stays a draft until an admin
approves it.

A lawyer still reviews community-sourced data before anyone is charged.
That part of decision 16 is unchanged. An auto-approved row does count on
a checklist. A checklist total is verified rows, and this verifier is the
check.

The script is `uv run python -m tools.verify_costumes`, run from
`commercial/backend`. A second run reads the cache and does not fetch.
The checklist site asks for a five-second crawl delay, and the script
waits that long between requests. It reads the event-form list to check
an id or a name. It does not copy the page's sentences or images into
the database. Each judged row stores the sources checked, their URLs,
the check date, a one-line reason, and a confidence. `verified_by` is
`auto-verifier`, which is not an admin email.

An official draft that already cites pokemongolive.com is approved from
that post. A community draft is approved when its code is in the
pokemon-go-api pokedex import and the same species and code, or the same
costume name, is on the event-form list. One source, or two sources that
do not point at one costume, stays a draft for Thomas. Codes that are
battle forms or internal ids are rejected: normal, shadow, purified,
regional forms, test ids, and a bare `costume-1` style slot. Those rows
do not count on a checklist. A shiny image URL is still not a shiny
release.

An admin can return any approved row to draft. That writes the admin
email into `verified_by`, and a later run leaves the row alone.

On 21 November 2026 the same script grew a second pass. It reads
official Pokémon GO posts and keeps only the species name and the
costume phrase. A leftover draft is approved when one of those posts
names that species in that costume. A game id is merged into the
official row when that same post is the one the official row cites and
the id's year does not contradict the post. A second internal slot is
merged only when it is the same costume: a `noevolve` suffix, or an
`-a-02` suffix whose icon matches the primary icon. Numbered balloon
and shirt ids stay drafts, because the posts name the colors and do not
number the files. The post text and its images are not stored.

Rejected: **approving every pokedex id as fully verified.** That file
includes assets that were not released, so a pokedex id alone is not an
auto-verified row. Rejected: **storing checklist sentences or images.**
The URL is the citation. Rejected: **guessing that a lettered game id is
a named trainer costume** when the two codes are not the same.

On 22 November 2026 Thomas asked the leftover drafts to count, labelled
as lower confidence. A pokedex costume that no post corroborated is now
approved with verdict `game_data_only`, confidence `low`, and the reason
"present in game data; no official post found". The evidence URL is the
pokedex import. `verified_by` is `auto-verifier`. The status is `approved`,
so a checklist counts it the same way it counts any other approved row.
`/curate` shows a Game data only badge, separate from Auto-verified, and
a filter for that verdict. The public checklist adds a small "from game
data" note. An admin can still return the row to draft, which writes the
admin email and keeps a later run from changing it.

A row stays a draft only when sources name different costumes for the
same id. The two placeholder slots, `pikachu` `costume-1` and `raichu`
`costume-1`, stay rejected. A shiny image URL is still not a shiny
release, and this pass does not write a shiny row. The same script
applies the rule on the next import: a post or a second list entry is
auto-verified, a pokedex id alone is game_data_only, a battle form or
placeholder is rejected, and a conflict stays a draft.
