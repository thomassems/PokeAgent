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
- No Bulbapedia text.
- No scraping of official Scopely or Niantic sites, including
  pokemongolive.com.
- No LeekDuck or ScrapedDuck data.
- No reading of game accounts.

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
