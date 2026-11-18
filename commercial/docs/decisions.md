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
fields. The comparison is in `docs/go-data-sources.md`.

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
