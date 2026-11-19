# Trainermon: licensing, data, art and business review

Status: **research, with a subset approved.** Written 17 November 2026
for the commercial edition (`commercial/`). It builds on
`monetization-research.md` (16 Nov), `commercial/docs/go-data-sources.md`
and `commercial/docs/decisions.md`. Thomas approved seven choices from
section 7 on 17 November 2026. Those are logged in `decisions.md`. The rest
of this review is still research, not a build approval.

Every page below was read on 17 November 2026 unless noted.

How to read this:
- Quotes come from the linked page.
- Revenue and user numbers from Sensor Tower, AppMagic, Adapty, Peekly or
  AppRank are **third-party estimates**, not company figures. They often
  disagree with each other, and the doc says so where they do.
- **[uncertain]** marks anything that is a judgment call, came from a search
  summary rather than a page I opened, or needs a lawyer.
- This is not legal advice. A short consult with a Canadian IP and tech lawyer
  is the first thing to buy before charging money (see section 7).

---

## 0. The short version

1. **Data you can sell on.** Game facts are not copyrightable in the US
   ([Feist v. Rural, 499 U.S. 340](https://www.law.cornell.edu/supremecourt/text/499/340)).
   Canada needs "skill and judgment" for originality
   ([CCH v. LSUC, 2004 SCC 13](https://www.canlii.org/en/ca/scc/doc/2004/2004scc13/2004scc13.html)).
   What does block us is **contracts and terms**: ScrapedDuck's no-paywall rule,
   Bulbapedia's NonCommercial license, Scopely's no-scraping terms. The
   commercial-safe route is:
   1. **PvPoke (MIT) plus PokeAPI (BSD)** for species, stats, moves and forms.
   2. **Our own curated GO-availability layer** (shiny, Dynamax, costumes,
      raids, events), restated by hand from official announcements.
   3. **Crowdsourced user reports**, moderated.
   4. Optionally, **a written licence** from LeekDuck/ScrapedDuck or
      Pokebattler.
2. **Art.** Commissioning our own drawings of real Pokémon is **not** a way
   out: they are derivative works of TPC characters. The only zero-risk option
   is text-first rows: Pokédex-number badges, our own type pills and variant
   chips. Official sprites are what every big paid competitor shows, and
   none of them has a public takedown. But TPC has cited sprite images in a
   cease-and-desist against a Pokémon GO companion app (PokiiMap, 2017), and
   in DMCA notices as recently as 2024. Risk: **low probability, high impact.**
3. **Business.** $10/month is at the top of the market for what Trainermon
   offers today. Trading finders (PogoTrades, PoGo Alley, PGT) are free.
   The money in GO tools is in **remote-raid queue priority** (PokeRaid
   $15.99/month, Poke Genie up to $47.99/month), **IV scanning** (Poke Genie
   $9.99 one-time), and **simulations and personal collection tools**
   (Pokebattler $2.99 to $19.99/month). $50k/month is about half of what
   third parties estimate the two category leaders make on iOS, after 6 to 9
   years and over 5 million downloads each.

---

## 1. How monetized Pokémon GO tools actually operate

### 1.1 Summary table

| Product | Model and price | Users / revenue (public or estimated) | Data source | Art | Known takedowns |
| --- | --- | --- | --- | --- | --- |
| **Poke Genie** (Poke Genie Inc.) | Free with ads. Scan Pro + Remove Ads $9.99 one-time. Raid VIP $2.99, Raid Ultra $17.99, Raid Master $47.99 per month ([App Store](https://apps.apple.com/us/app/poke-genie-remote-raid-iv-pvp/id1143920524), [Adapty](https://adapty.io/paywall-library/poke-genie/)) | Claims "over 20,000,000 downloads". Google Play shows 10M+ installs and 529k reviews ([Google Play](https://play.google.com/store/apps/details?hl=en_GB&id=com.cjin.pokegenie.standard)). Estimates: ~$100K/month on iOS ([Peekly](https://peekly.app/apps/6c585d4d-e033-44a5-97ea-e73c8191d9c0), [Adapty](https://adapty.io/paywall-library/poke-genie/), which also cites "$200K") | Game stats (the battle sim and Pokédex need game-master numbers) **[uncertain: not stated]**. Your own Pokémon come from **screenshots and screen recording**: "Relying only on screenshot/screen recording and requiring no logins, Poke Genie is fully compliant with Niantic's terms of service" ([Google Play](https://play.google.com/store/apps/details?hl=en_GB&id=com.cjin.pokegenie.standard)) | Store screenshots show in-game screens and small Pokémon icons in its PvP lists (checked visually) | None found. Disclaimer: "a third-party app made by fans, and is not affiliated with the Pokémon brand, Niantic, Pokemon Go, or Nintendo." |
| **PokeRaid** (Pyde Technologies LTD, London) | Free with ads. Coins $1.49 to $47.99. Mega Guest / Mega Host $15.99 to $16.99/month ([AppRank IAP list](https://apprank.io/pokeraid-raid-from-home-9524)) | "More than 4.5M registered PokeRaid users" (Feb 2024, [r/PokeRaid](https://www.reddit.com/r/PokeRaid/comments/1annhvo/pokeraid_introduces_a_new_revenue_share_model/)). 5,000,000+ on [pyde.tech](https://pyde.tech/). 5M+ Play downloads ([Google Play](https://play.google.com/store/apps/details?hl=en&id=me.pokeraid)). Estimates conflict: $100K/month iOS ([AppRank](https://apprank.io/pokeraid-raid-from-home-9524)) vs $5K/month Google Play ([Peekly](https://peekly.app/apps/4a2c4031-458b-4350-bbb2-41591353a76e)) | **Its own users.** Hosts upload a screenshot of the raid. The app passes friend codes and runs room chat with translation and ratings ([Google Play](https://play.google.com/store/apps/details?hl=en&id=me.pokeraid)) | Store screenshots show GO-style 3D Pokémon renders on raid cards (Lunala, Mega Garchomp, Shadow Giratina) | None found. Note: its **Frontliner** programme pays hosts in gift cards ([Reddit](https://www.reddit.com/r/PokeRaid/comments/1annhvo/pokeraid_introduces_a_new_revenue_share_model/)). Scopely's terms ban "performing services in the Apps in exchange for payment outside the Apps" (section 2.6). Reviews complain it is "becoming more and more of a money grab". |
| **Pokebattler** | Ads for free users. Standard $2.99, Battler $9.99, Champion $19.99 per month; 7-day trial ([subscription](https://www.pokebattler.com/subscription), prior research) | Unknown | Monte Carlo sims on "the game's real damage, energy, and dodging mechanics" ([developers](https://www.pokebattler.com/developers)). Game master derived **[uncertain: not stated on page]** | Store screenshot shows a Pokémon sprite (Duraludon) | None found. Runs a **public API and MCP**: "Attribution to Pokébattler is required", and "If you are building something that needs more than occasional access, get in touch" ([developers](https://www.pokebattler.com/developers)). Its ToS page is JavaScript-rendered and could not be read **[uncertain]**. |
| **PvPoke** | Free, Patreon (~$216/month, prior research) | Unknown users | PokeMiners game master, parsed by the maintainer: "I use the pokeminers file and run `parse.php`" ([issue #269](https://github.com/pvpoke/pvpoke/issues/269)). Code and data MIT ([license](https://github.com/pvpoke/pvpoke/blob/master/LICENSE)) | Text and type colours, no Pokémon art in its rankings UI | None found. |
| **Pokémon GO Hub** | Ads, through Enthusiast Gaming (prior research) | Unknown | Its database is built on the game master. GO Hub publishes guides to decoding it ([GO Hub guide](https://pokemongohub.net/post/guide/guide-decode-pokemon-go-game_master-file/), [database guide](https://pokemongohub.net/post/news/go-hub-guide-to-our-database/)) | Not verified | None found. |
| **LeekDuck** | Programmatic ads (prior research) | Unknown | Hand-written posts from official announcements, data mines and observation **[uncertain]** | Uses GO sprites | None found. Feeds ScrapedDuck, whose README forbids paywalls and ads (prior research). |
| **The Silph Road** (historical) | Volunteer-run with Niantic sponsorship; closed in 2023 | n/a | Its own users: crowdsourced nest and research reports | n/a | Not a takedown. It closed when **Niantic's sponsorship ended** and costs rose ([Dexerto](https://www.dexerto.com/pokemon/the-silph-road-shuts-down-as-niantic-changes-ambassador-program-2144055/), [r/TheSilphRoad](https://www.reddit.com/r/TheSilphRoad/comments/13fs6kx/the_end_of_an_era_after_seven_extraordinary_years/)). Lesson: crowdsourcing at scale costs money, and depending on the publisher is fragile. |
| **Campfire** (first-party) | Free; now Scopely's | n/a | Official | Official | Team Up finds nearby raid groups and sends players into the real lobby ([Campfire help](https://scopelyexplore.helpshift.com/hc/en/13-campfire/faq/324-campfire-team-up/)). It is the first-party competitor to local raid and trade coordination. |
| **Trade finders**: [PogoTrades](https://pogotrades.com/), [PoGo Alley](https://pogoalley.com/), [Pokémon Go Trading (PGT)](https://pokemongotrading.com/) | **Free.** PoGo Alley: "It is free to list". PGT says trading is completely free (search summary **[uncertain]**) | PogoTrades homepage: "1,427 Trainers listing, 18,827 Pokémon offered, 13,718 Wishlist entries" | Their own users' lists | PogoTrades and PoGo Alley show Pokémon images. PoGo Alley says it "matches on the exact sprite (form, shiny status, costume) and on the event background" | None found. **These are Trainermon's direct competitors, and they are free.** PogoTrades also lists raids, an IV checker and a trade cost calculator. |
| **2016 to 2017 maps and trackers** (PokéVision, PokéHound, PokiiMap) | Some charged money | n/a | **Pulled from Niantic's servers** | Official sprites | **Shut down.** TPCi's lawyers (Focal PLLC) sent PokiiMap a C&D and a GitHub DMCA. It names sprite images of Eevee, Nidoran, Pidgey and Weedle with their US copyright registration numbers ([GitHub DMCA, 2017](https://github.com/github/dmca/blob/master/2017/2017-03-09-pokiimap.md)). See also [TechCrunch 2016](https://techcrunch.com/2016/08/01/third-party-pokemon-go-tracking-services-get-shut-down/). |

### 1.2 Patterns

- **What gets enforced:**
  1. Reading Niantic/Scopely servers, the 2016 trackers and maps.
  2. Copying TPC images into a distributed product: PokiiMap 2017,
     [pokereact 2016](https://github.com/github/dmca/blob/master/2016/2016-03-07-Pokemon.md),
     and a [2024 Hugging Face dataset](https://huggingface.co/datasets/huggingface-legal/takedown-notices/raw/main/2024/2024-02-09-Pokemon-Company-International.md)
     taken down through TPCi's brand-protection agent, Tracer.
  3. Fan games and ROM hacks (prior research).
- **What has run for years, unenforced, with money attached:** screenshot
  readers (Poke Genie), user-generated raid coordination (PokeRaid), and
  simulators (Pokebattler). All three show official-looking art and a "not
  affiliated" disclaimer. That they are still up doesn't mean they have
  permission. Whether they hold a licence is unknown.
- **TPC's official position:** "we're not in a position to review requests to
  use the Pokémon intellectual property (including its characters, names, and
  designs). As a result, we ask that you not use it in or associate it with
  your project in any way"
  ([Pokémon Support](https://support.pokemon.com/hc/en-us/articles/360000634094-Can-I-use-Pok%C3%A9mon-images-or-materials)).
  There is **no licensing door** for a small app.
- **TPC uses an outside brand-protection vendor** (Tracer, as in the 2024
  notice). Detection may be partly automated and driven by keywords.
  **[uncertain inference]**

### 1.3 Scopely (owner of Pokémon GO since 29 May 2025)

- The acquisition closed 29 May 2025. Scopely said Pokémon GO had "over 20M
  weekly active players" and "100 million+ unique players in 2024"
  ([Scopely](https://www.scopely.com/en/news/scopely-to-acquire-niantic-games-business-which-includes-pokemon-go-one-of-the-most-successful-mobile-games-of-all-time)).
- **Terms: [Scopely Explore Terms of Service](https://nianticlabs.com/terms?hl=en),
  last modified 15 July 2026.** They cover the apps and "any websites we own or
  operate ('Sites')", so pokemongolive.com news is part of the "Services".
  Relevant prohibitions:
  - "extract, scrape, or index the Services or Content (including information
    about users or gameplay)"
  - "use the Services or Content ... for any commercial purpose ... including
    ... (b) performing services in the Apps in exchange for payment outside
    the Apps, or (c) selling, reselling, or renting the Apps or your Account"
  - Access "through ... automation software, bots, spiders, crawlers, data
    mining tools"
  - "decipher, decompile, disassemble, or reverse engineer"
  - "circumvent any technological measure"
  - Cheating includes "using modified or unofficial third party software",
    "Sharing accounts" and "Selling or trading accounts"
  - Content licence: "personal, noncommercial ... solely for your permitted
    use within the Services"
- **No developer API, data programme or fan-content licence was found.** Fev
  Games: "no official API exists"
  ([Fev Games](https://fevgames.net/walking-a-dangerous-line-pokemon-go-and-unofficial-api-projects/)).
  The [Player Guidelines](https://scopelyexplore.helpshift.com/hc/en/5-pokemon-go/faq/1302-player-guidelines/)
  forbid content that violates IP, "including impersonation or false
  affiliation".
- **Implications for Trainermon:**
  - Never read game accounts, servers or traffic.
  - Never auto-scrape pokemongolive.com, which is part of the "Services".
  - Never pay users to host or trade. That is the PokeRaid Frontliner risk.
  - Never facilitate account sales.
  - User-entered lists and user screenshots stay on the safe side, the same
    line Poke Genie draws.

---

## 2. Data paths, ranked for a paid app

The legal frame:
- **Copyright doesn't cover facts.** Base stats, move power, "Shiny Lapras is
  out from 1 December" are facts.
  - US: "facts are not copyrightable"; only original selection and
    arrangement is protected
    ([Feist](https://www.law.cornell.edu/supremecourt/text/499/340)).
  - Canada: originality needs non-trivial "skill and judgment", and mechanical
    work isn't enough
    ([CCH 2004 SCC 13](https://www.canlii.org/en/ca/scc/doc/2004/2004scc13/2004scc13.html)).
  - Neither country has an EU-style database right. **[uncertain: lawyer to
    confirm]**
- **Copyright does cover:** the game master *file* as part of Niantic/Scopely's
  software, if copied wholesale; text written by LeekDuck, Bulbapedia and
  others; and every image.
- **Anti-circumvention.** Canada's Copyright Act s.41.1 bars circumventing an
  access-control TPM and offering circumvention services
  ([s.41.1](https://laws-lois.justice.gc.ca/eng/acts/C-42/section-41.1.html)).
  The US has DMCA §1201. Data miners who decrypt the client take that risk.
  Using facts they publish is a step removed. **[uncertain: lawyer]**
- **Contracts and terms:** ScrapedDuck's README, Bulbapedia's CC BY-NC-SA, and
  Scopely's ToS bind whoever accepts them.

### 2.1 Ranked table

| Rank | Path | Commercial OK? | Coverage | Effort / cost | Risk |
| --- | --- | --- | --- | --- | --- |
| **1** | **PvPoke gamemaster (MIT) + PokeAPI data (BSD-3)** for species, dex numbers, types, forms, stats, moves, regional/legendary/mythical/shadow tags | **Yes for their compilations.** The MIT and BSD notices must be kept. The underlying numbers are game facts that originally came from PokeMiners, which PvPoke confirms in [issue #269](https://github.com/pvpoke/pvpoke/issues/269). MIT cannot license rights PvPoke doesn't hold, but facts aren't copyrightable. | Battle-relevant species and forms. **No shiny, Dynamax, Gigantamax or costume fields** (go-data-sources.md); `untradeable` is incomplete | Already wired. ~0 cost | **Low.** The same footing Pokebattler and Poke Genie run on. Keep notices. Don't copy PokeMiners' raw file. |
| **2** | **Our own curated GO-availability layer**: shiny released, Dynamax/Gmax, costumes, event and raid schedules, trade rules. A person restates facts in our own words from official announcements, in-game news and official social posts | **Yes.** Facts restated in our own words are ours. Never copy announcement text or images. | Exactly the fields the Explorer and lists need. Quality depends on discipline | **Ongoing labour.** Assumption: a few hours a week, more around big events (not measured). An internal admin form plus an "AI drafts, human approves" step keeps it fast. Fully automated scraping of pokemongolive.com is out (ToS) | **Low** if done by hand. **Medium** if anyone automates fetching official pages. Error risk is the real one: a wrong "tradable" or "shiny" flag. Add a "report an error" link and a last-verified date per row. |
| **3** | **Crowdsourced user reports**: "I hatched a shiny X", raid sightings, Dynamax spots. Votes and moderator confirmation | **Yes.** User-generated, licensed to us in our ToS. Users reporting what they saw by hand isn't scraping. | Grows with users. This is how PokeRaid, PogoTrades and the old Silph Road built their data | Needs moderation tooling, anti-spam and a DMCA agent if users upload images. Silph Road shows the cost at scale | **Low to medium.** Content moderation, minors (section 6), and a possible ToS argument if users bulk-copy in-game data. Don't accept automated or bot submissions. |
| **4** | **Licence from LeekDuck / ScrapedDuck** | **Not as written.** ScrapedDuck: apps "cannot be hidden behind a paywall" or "monetized with advertisements". Code is AGPL-3.0 ([GitHub API](https://api.github.com/repos/bigfoott/ScrapedDuck)). No public commercial licence or partners found | Best live coverage: events, raids, research, eggs, Rocket | One email (Thomas sends; a draft can be prepared). Unknown fee | **Low if a written grant arrives**; otherwise unusable for paid features. Even with a grant, LeekDuck's sprites would still be TPC's. |
| **5** | **Pokebattler API / MCP** | **Unclear.** Public, needs attribution: "Attribution to Pokébattler is required". It invites contact for heavier use. Its ToS couldn't be read (JS page) | Raid counters, live rotation, Max battles, Rocket, Pokédex | Free account and token; heavier use by arrangement | **Medium.** It's a direct competitor that could cut us off. Fine for an "Ask Pokebattler" credit link. Don't build a paid core on it without a written agreement. |
| **6** | **pogoapi.net** | **No grant.** "provided under a fair use clause ... provided as-is", "© 2026 PoGo API. All rights reserved." ([Legal](https://pogoapi.net/Legal/)) | Surprisingly wide: `shiny_pokemon.json`, `released_pokemon.json`, `raid_bosses.json`, `community_days.json`, `mega_pokemon.json` and more ([docs](https://pogoapi.net/documentation/)) | Free | **Medium-high** for a paid app: "all rights reserved" and no licence. Could be asked for permission. |
| **7** | **PokeMiners game master directly** | **No licence offered.** "educational use only. All content found within this repo is the property of The Pokemon Company and Niantic" ([game_masters](https://github.com/PokeMiners/game_masters), no repo licence per the GitHub API) | Complete game rules (not shiny, which is server-side **[uncertain]**) | Free | **Medium-high.** We'd copy a file the publisher claims and the miner disclaims. Extracting individual numeric facts is defensible but adds nothing PvPoke doesn't already give us under MIT. |
| **8** | **PokeMiners `pogo_assets`** (images, sounds, text) | **No.** Same disclaimer. Images are TPC/Niantic copyright | Every sprite | Free | **High.** Distributing these is what PokiiMap was C&D'd for. |
| **9** | **Bulbapedia / Serebii text** | **No.** CC BY-NC-SA ([Bulbapedia:Copyrights](https://bulbapedia.bulbagarden.net/wiki/Bulbapedia:Copyrights)) | Very good | n/a | Licence violation. Reading them for leads and then verifying against official sources is fine. Copying isn't. |
| **10** | **Official Scopely / Niantic data programme** | **None exists** (section 1.3) | n/a | n/a | n/a |

### 2.2 Recommended stack

1. **Base catalog:** generate the Explorer's species, forms and types from
   **PvPoke + PokeAPI**, replacing the hand seed's species list. Keep the MIT
   and BSD notices in an "Open-source data" credits page.
2. **GO layer (the moat):** a `go_availability` table we own. Fields: shiny
   (and since when), dynamax, gigantamax, costume list, tradable /
   special-trade / remote-trade rules, `source_url` (the official post),
   `verified_at` and `verified_by`. Fill it by hand from official posts.
   - An internal admin page can let the AI assistant draft entries from an
     announcement a human pasted in, with the human approving each one.
   - No automated fetching of Scopely Sites.
3. **Community layer:** user reports with votes and moderator confirmation.
   Accept text and tags only at first, and add image uploads later, behind a
   DMCA agent and moderation.
4. **Ask for licences in parallel:** an email to LeekDuck/ScrapedDuck about
   paid use, and optionally Pokebattler and pogoapi.net. If any says yes in
   writing, plug it in as an extra source with attribution.
5. **Hard rules** (add to `commercial/docs/decisions.md`):
   - No PokeMiners files or assets.
   - No Bulbapedia or LeekDuck text.
   - No automated fetching of pokemongolive.com.
   - No game-account access.
   - No paying users to host or trade.

The trade rules for flags, verified on the official help pages:
- "Mythical Pokémon (like Mew) and Pokémon that have previously been traded
  once before cannot be traded"
  ([Trading Pokémon](https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/96-trading-pokemon/?l=en&p=web)).
- Remote Trades exclude "Shadow Pokémon", "Mythical Pokémon", "Fused Pokémon",
  Crowned Zacian and Zamazenta, and others
  ([Trading Remotely](https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/5312-trading-remotely/?l=en&p=web)).
- The Meltan/Melmetal in-person exception came from a search summary only.
  **[uncertain: confirm on the official page before launch]**

---

## 3. Art without letter placeholders

| Option | Allowed? | Cost | Risk | Notes |
| --- | --- | --- | --- | --- |
| **Commission original drawings of real Pokémon** (our own Pikachu icon) | **No.** A redrawn Pikachu is still a reproduction or derivative of a copyrighted character. TPC: fan art gives no right "beyond a personal, noncommercial home use" ([pokemon.com legal](https://www.pokemon.com/jp/legal/information)). Google Play lists "fan art indistinguishable from the original work" as a violation ([Play IP policy](https://support.google.com/googleplay/android-developer/answer/9888072?hl=en)) | Artist fees | **High.** Worse than sprites: we'd be selling new derivative art. | Verified: not a loophole. |
| **Silhouettes / outlines** of real Pokémon | Still copies a recognisable character design **[uncertain: lawyer]** | Low | **Medium** | Not clearly safer than sprites, and they look worse. |
| **Official sprites** (PokeAPI sprites, HOME renders, GO icons) | **No licence.** PokeAPI's repo: "All image contents within are Copyright The Pokémon Company" ([LICENCE.txt](https://raw.githubusercontent.com/PokeAPI/sprites/master/LICENCE.txt)) | 0 | **Low probability, high impact.** Evidence below | What every big competitor shows. |
| **User-uploaded screenshots** (like PokeRaid's raid photo) | User content. Still TPC imagery, but hosted under a notice-and-takedown process | Storage plus moderation | **Medium.** Needs a US DMCA agent and fast takedowns | Useful for trade listings ("here's my shiny"). |
| **Text-first compact rows**: `#0131 Lapras`, our own type pills (coloured text, *not* the official type symbols), variant chips (✨ Shiny, Dynamax, Gigantamax, costume name, Lucky, Shadow/Purified), CP/IV text | **Yes**, all ours | Design time only | **None** | Denser and faster on phones. Matches PvPoke's text-and-colour style. |
| **Original brand mascot or illustrations not depicting Pokémon** (a Trainermon logo, trainer-themed decorations, original backgrounds) | **Yes**, if commissioned under a work-for-hire or assignment | One-off fee (not researched) | None if clearly original and not Pokémon-like | Gives the app personality without TPC art. |

**Enforcement history for sprites (quantified as far as public records go):**
- **TPCi DMCA and C&D notices for images found:**
  - 2010: PokéBeach and Serebii screenshots (prior research).
  - 2011: the Pokédroid app removed (prior research).
  - 2016: the pokereact Chrome extension's images
    ([GitHub DMCA](https://github.com/github/dmca/blob/master/2016/2016-03-07-Pokemon.md)).
  - 2017: PokiiMap, a GO companion, with sprite copyright registration
    numbers ([GitHub DMCA](https://github.com/github/dmca/blob/master/2017/2017-03-09-pokiimap.md)).
  - 2024: a Hugging Face image dataset
    ([notice](https://huggingface.co/datasets/huggingface-legal/takedown-notices/raw/main/2024/2024-02-09-Pokemon-Company-International.md)).
- **No public takedown found** against Poke Genie (since 2016), PokeRaid
  (since 2020), Pokebattler, PogoTrades, PoGo Alley, LeekDuck or GO Hub, all
  of which show Pokémon images. GitHub's public DMCA repo had 13 file names
  containing "Pokemon"/"Nintendo". Most are Nintendo game or emulator notices.
  **[count is file-name based, not exhaustive]**
- My read: TPC enforces where art is the product (datasets, fan games), where
  the app touches game servers, or where something gets press or funding (the
  former TPC general counsel, prior research). Utility apps that show sprites
  as labels have been tolerated for close to a decade. **That is tolerance,
  not permission**, and one notice to a host or app store can remove the
  app overnight.

**Recommendation:**
1. **Now:** text-first rows with Pokédex-number badges, our own type pills
   and variant chips, plus original Trainermon branding. This replaces the big
   letter cards immediately at zero risk. Make the rows compact; the big cards
   are what feel empty.
2. **Optional, behind a feature flag, after a lawyer consult:** show official
   GO-style sprites, small, as identifiers only. Never in the logo, store
   icon, marketing, or anything sold as content. Keep a one-switch fallback to
   text rows if a notice arrives. Risk level if enabled: **medium** (low
   probability, high impact).
3. **Trade listings:** allow an optional user screenshot once a DMCA agent and
   moderation are in place.

---

## 4. Platforms and payments

- **Apple.** 5.2.1: "Don't use protected third-party material such as
  trademarks, copyrighted works ... without permission". 5.2.2: if the app
  "displays content from a third-party service, ensure that you are
  specifically permitted to do so". Authorization may be requested
  ([App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)).
  - With official sprites, an iOS app is exposed to rejection or to removal
    after a complaint. A Pokédex app was rejected over IP (prior research), and
    a Stack Overflow developer reports a rejection for resembling Pokémon
    ([Stack Overflow](https://stackoverflow.com/questions/44771272/app-rejected-for-resembles-pokemon)).
  - Many GO tools are still listed. **[enforcement is inconsistent]**
- **Google Play.** "If your app uses another party's trademarks in a way that
  is likely to cause confusion, your app may be suspended." It also says "the
  safest approach is to create something that's original"
  ([Play IP policy](https://support.google.com/googleplay/android-developer/answer/9888072?hl=en)).
- **Web-first (recommended).** A PWA on our own domain avoids store review and
  store fees.
  - Stripe Canada: 2.9% + C$0.30 per domestic card, plus Stripe Billing 0.7%
    ([Stripe CA](https://stripe.com/en-ca/pricing),
    [Billing](https://stripe.com/en-ca/billing/pricing)).
  - On a $9.99 charge that is about $0.66, so roughly **$9.33 net** before tax
    and FX. The US rate is the same 2.9% + 30¢ (prior research).
  - Sales tax: Canada GST/HST and US state taxes may apply; Stripe Tax is
    extra **[not priced here]**.
- **Store fees if we ever ship native apps:**
  - Apple: 15% under the Small Business Program (prior research).
  - Google: 15% on subscriptions in legacy markets, or "10% plus a 5% billing
    fee" in the US, UK and EEA
    ([Play fees](https://support.google.com/googleplay/android-developer/answer/112622?hl=en)).
  - US link-out purchases: allowed, but Apple's proposed commission (15%, or
    5% for small business) is still in court as of Nov 2026
    ([TechCrunch](https://techcrunch.com/2026/08/14/apple-proposes-to-take-a-15-cut-of-purchases-made-outside-the-app-store/),
    [MacObserver](https://www.macobserver.com/news/app-store-link-out-commission-rate-not-set-us/)).
- **Hosting:** Vercel Hobby is non-commercial only, so Pro ($20/month) is
  needed before charging (prior research).

---

## 5. Business reality check

### 5.1 The market is real

- Scopely: over 20M weekly active players and 100M+ unique players in 2024
  ([Scopely](https://www.scopely.com/en/news/scopely-to-acquire-niantic-games-business-which-includes-pokemon-go-one-of-the-most-successful-mobile-games-of-all-time)).
- Sensor Tower Q4 2025: US weekly active users rose from 6.8M to 7.4M, and
  weekly US revenue spiked to $9.9M in mid-November
  ([Sensor Tower](https://sensortower.com/blog/2025-q4-unified-top-5-pokemon-collector-games-units-us-6089902328293296048c7c1b)).
  Europe reached 4.1M weekly actives
  ([Sensor Tower EU](https://sensortower.com/blog/2025-q4-unified-top-5-pokemon-collector-games-units-europe-6089902328293296048c7c1b)).
- 2025 store spending was about **$745.1M** (AppMagic). Scopely said total
  2025 revenue was over $1B including its web shop. Both via
  [PocketGamer.biz](https://www.pocketgamer.biz/pokmon-go-revenue-skyrockets-towards-a-record-high-during-go-fest-2026-global/),
  search summary **[uncertain: not opened]**.
- Thomas is right that grinders spend. The question is whether they spend on
  **our** features.

### 5.2 What comparable tools make (estimates)

| App | Estimated monthly revenue | Downloads / age |
| --- | --- | --- |
| Poke Genie | ~$100K iOS ([Peekly](https://peekly.app/apps/6c585d4d-e033-44a5-97ea-e73c8191d9c0)); Adapty also cites "$200K" | 10M+ Play installs, since 2016 |
| PokeRaid | $100K iOS ([AppRank](https://apprank.io/pokeraid-raid-from-home-9524)) vs $5K Android ([Peekly](https://peekly.app/apps/4a2c4031-458b-4350-bbb2-41591353a76e)): a 20x spread, so treat as very rough | 5M+ users, since 2020 |
| Pokebattler | Unknown | n/a |
| PvPoke | ~$216/month Patreon | Widely used |
| Trade finders | $0 (free) | PogoTrades: 1,427 listers |

So **$50k/month means roughly half of a category leader**, and the leaders
took 6 to 9 years with millions of downloads.

### 5.3 Conversion math

- RevenueCat's 2026 report: freemium apps convert **2.1%** of downloads to paid
  by day 35, and hard-paywall apps 10.7%
  ([RevenueCat post](https://www.linkedin.com/posts/revenuecat_the-case-for-and-against-hard-paywalls-activity-7515818707886116865-56wS),
  [report](https://www.revenuecat.com/state-of-subscription-apps)).
  The global median is about 2.0%.
- At 2%, **5,000 payers needs about 250,000 sign-ups, and 10,000 needs about
  500,000**, before churn, which makes it higher. Churn was not researched.
- 250,000 is about 3.4% of US weekly GO actives, or around 1% of the global
  weekly base. It is achievable only with a feature people return to weekly.

### 5.4 What grinders demonstrably pay for

1. **Remote raid access and queue priority.** Poke Genie's subscriptions "only
   reduce your wait time" ([r/PokeGenie](https://www.reddit.com/r/PokeGenie/comments/1deuxb3/is_there_even_a_point_in_getting_raid_ultra/),
   search summary). PokeRaid Mega is $15.99/month. Time-limited legendaries
   create real scarcity.
   - Caveat: in 2023 Niantic capped remote raids at 5 a day and raised pass
     prices ([Polygon](https://www.polygon.com/23663732/pokemon-go-remote-raid-pass-price-increase-daily-limit/)).
     The platform owner can shrink this market at will.
2. **Convenience automation within the rules:** IV scanning from screenshots
   and name generators (Poke Genie Scan Pro $9.99 one-time).
3. **Simulation tied to your own collection** (Pokebattler Battler $9.99,
   Champion $19.99).
4. **No ads.** Every freemium GO tool sells ad removal.
5. **Trading:** no evidence anyone pays. All finders found are free. Trading
   is the **growth** feature, not the revenue one.

### 5.5 Honest view on $10/month

- Today's Trainermon features (lists, trade search, Explorer, AI chat) have
  free competitors. At $10 they'd be hard to sell. AI chat comparables are
  $2.99 to $4.99 (prior research).
- $9.99 is defensible only with a hard-value anchor. Options:
  - raid matchmaking with priority and a reliable host pool;
  - instant trade alerts ("someone in Toronto just listed your shiny
    Dynamax Machamp");
  - collection and shiny-dex tracking, with screenshot import done the
    Poke Genie way;
  - personalised raid and Max Battle counters from your own boxes;
  - an AI coach that knows your collection.
- One shape to consider: **Free** (lists, trading, Explorer, ads off or
  minimal), **Plus $4.99** (alerts, unlimited lists, AI), **Pro $9.99** (raid
  priority, collection sims), with **annual plans**.
  **[proposal, not a recommendation to fix prices yet]**

---

## 6. Risks and mitigations

| Risk | Likelihood / impact | Mitigation |
| --- | --- | --- |
| **"Trainermon" trademark conflict** | Unknown, probably low. A web search found only fan uses: a Smogon "TrainerMons" pet mod and a Bulbagarden "Trainermon" cosplay thread ([Smogon](https://www.smogon.com/forums/threads/pet-mods-submission-thread.3657184/page-5), [Bulbagarden](https://bulbagarden.net/threads/tkms-trainermon-cosplay-factory-accepting-requests.80226/)). **USPTO and CIPO databases were not queried** (the USPTO search API refused scripted access). The "-mon" suffix isn't Nintendo's alone (Digimon, and Coromon registered in the EU per [TrademarkElite](https://www.trademarkelite.com/europe/trademark/trademark-detail/019218244/Coromon)). Nintendo has opposed "Poké"-prefix marks, e.g. "Poké Go" in 2017 ([Briffa](https://www.briffa.com/blog/poke-trade-mark-wars/)). | Run a clearance search in [CIPO](https://ised-isde.canada.ca/cipo/trademark-search/srch) and [USPTO](https://tmsearch.uspto.gov/), ideally by a lawyer. Consider filing in Canada (class 9/42). Keep "Pokémon" out of the name, icon and domain. Use Pokémon names only to describe the content (nominative use **[lawyer to confirm for Canada]**). |
| **TPC copyright (art)** | Sprites: low probability, high impact. Original drawings of Pokémon: high | Section 3: text-first now; sprites only behind a flag after a lawyer consult; a takedown runbook. |
| **TPC trademark / false affiliation** | Medium if branding looks official | "Not affiliated" disclaimer, no Poké Ball or official logos, no Pokémon art in store or marketing assets. |
| **Scopely ToS** | High if broken; low if not | No account reading, bots or scraping of Scopely Sites. Don't pay users for in-game services. No account trading or sales. Remove listings that offer accounts or coins for money. |
| **Data licences** | Medium | Stack in section 2.2. Keep MIT/BSD notices. Track `source_url` for every curated fact. |
| **Minors' privacy** | High impact. Pokémon skews young, and Scopely runs "Kids at Scopely Explore" logins (help page above) | US: the amended COPPA Rule is fully in force from **22 April 2026** ([Federal Register](https://www.govinfo.gov/content/pkg/FR-2025-04-22/html/2025-05904.htm), [Finnegan](https://www.finnegan.com/en/insights/articles/coppas-amended-rule-is-now-in-full-effect-what-operators-need-to-know.html)). Canada: the OPC's new **Children's Privacy Code** (20 Oct 2026) expects "parental consent for those under 13", privacy by default, and no profiling of children ([OPC](https://www.priv.gc.ca/en/opc-news/news-and-announcements/2026/nr-c_261020)). Simplest path: **13+ only with an age gate**, minimal data, city-level location only, profiles private by default, no behavioural ads, and a privacy policy naming DeepSeek and China-based processing (prior research). |
| **User-to-user contact safety** | High impact with a young audience | Friend codes behind an explicit opt-in (already off by default). No free-text DMs at launch, or DMs only with report and block, rate limits, link and phone filters, and moderator review. In-person trades get safety tips. PokeRaid hides location. |
| **Platform dependency** | Medium | Scopely can change trading or raid rules, as with the 2023 remote raid cuts. Diversify features. |
| **AI answers** | Medium | AI notice (DeepSeek ToS). Don't let the assistant quote or summarise LeekDuck pages for paying users. Treat web search as research, not republication **[gray area]**. |
| **Payments / tax** | Low-medium | Stripe Billing plus tax registration once thresholds hit. Clear refund and cancel terms. Vercel Pro. |

---

## 7. Decisions Thomas needs to make

1. **Data stack.** Approve PvPoke + PokeAPI base, our own curated GO layer and
   user reports, with the hard rules in section 2.2?
2. **Licence emails.** Send permission requests to LeekDuck/ScrapedDuck (and
   optionally Pokebattler and pogoapi.net)? A draft can be prepared; Thomas
   sends.
3. **Who curates the GO layer.** Thomas, volunteer moderators, or a paid
   part-timer? It's the main ongoing cost.
4. **Art.** Text-first rows now (zero risk), and decide later whether to
   enable official sprites after a lawyer consult?
5. **The paid anchor.** Which $9.99-worthy feature first: raid matchmaking with
   priority (needs contact and safety decisions), trade alerts, or collection
   tools? Trading itself stays free.
6. **Price shape.** A single $9.99 tier, or Free / $4.99 / $9.99 with annual
   plans? Web-first Stripe before any app store?
7. **Age and contact policy.** 13+ only? Friend codes opt-in only? In-app chat
   at launch or not?
8. **Legal budget.** A one-time Canadian IP and privacy lawyer consult plus a
   CIPO/USPTO clearance search for "Trainermon" before launch? (Cost not
   researched.)

## Sources not opened, or limits of this review

- PocketGamer.biz (2025 spending), Adapty's "$200K", PGT's "completely free",
  the Meltan/Melmetal exception, and Poke Genie subscription details came from
  search summaries.
- The Pokebattler ToS page didn't render.
- The USPTO and CIPO databases were not queried.
- GO Hub's and LeekDuck's art and data practices were not verified directly.
