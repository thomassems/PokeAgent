# Onboarding research

Checked 19 November 2026. These notes are what the linked pages actually
say. They are not a copy of those apps.

## What the comparable apps ask

**PokeRaid** verifies a trainer from Pokémon GO screenshots, not from a
timezone question. The 0.11 release post says the scan reads trainer name,
level, and friendship code from a profile screenshot and a friendship QR
screenshot. A later 0.11.3 post drops the main-map screenshot and keeps
those two. The developer tells trainers to keep the buddy from covering
the name and the level. A player thread shows the friend code is what the
other trainer copies. Sources:
[release 0.11](https://www.reddit.com/r/PokeRaid/comments/jnlq8a/release_011_profile_verification_new_trainer/),
[0.11.3](https://www.reddit.com/r/PokeRaid/comments/jr72eu/latest_on_profile_verification_release_0113/),
[friend code thread](https://www.reddit.com/r/PokeRaid/comments/iem1be/how_to_add_qcode_to_pokeraid_profile/).
An iMore walkthrough of joining a room also starts from the host's friend
code, not from a city or a zone:
[iMore](https://www.imore.com/pokemon-go-how-use-pokeraid-raid-home).

**Poké Genie** starts with an Apple or Google sign-in, then the in-game
username and friend code. A setup thread adds that the level has to stay
current and the name has to match, including case. The profile write-up
on TheGamer is the same pair: name and friend code. None of these pages
mention a timezone step. Sources:
[YouTube setup](https://www.youtube.com/watch?v=GK22Hor7iH8),
[setup thread](https://www.reddit.com/r/PokeGenie/comments/184k51t/setup_help/),
[TheGamer](https://www.thegamer.com/pokemon-go-poke-genie-guide/).

**Pokémon GO** itself does not ask the player to type a timezone. The
trainer profile already has the name, the team, and the level. The friend
code lives on the friends screen. Campfire, in the official Max Mondays
post, is the map for finding Max Battles and other trainers. That post
does not describe a trainer questionnaire:
[Max Mondays](https://pokemongolive.com/post/dynamax-max-mondays/).

## What we copied

The useful required set is small: a name, a level, and a way to know the
team. The friend code matters for raids later, and every source treats it
as something you can get wrong, so it stays optional and skippable here.
Nobody in these sources asks for a timezone up front, so we store the
browser zone and do not show a picker. City is also absent from these
signup flows. Trade search still needs one later, so it stays on the
profile instead of blocking the first screen.

The shape is three short steps on a phone: account and the 13+
confirmation, then name, team, and level, then friend code with a skip.
Everything else is edited from the profile after that.
