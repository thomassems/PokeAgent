# Monetization research

Status: **research only, not approved.** Nothing here has been decided or
built. Thomas asked for this on 16 November 2026: the app should stay
affordable and avoid licensing and IP problems. Every claim links its source.
Prices were read on 16 November 2026 unless noted. Where a number comes from a
third-party tracker or a search snippet rather than the vendor's own page, it
says so. "Unknown" means it couldn't be found.

## Summary

- **The biggest blocker is our own GO data source, not Nintendo.** ScrapedDuck's
  developer terms say apps using its data "cannot be hidden behind a paywall"
  and "cannot be monetized with advertisements", and must credit ScrapedDuck
  and LeekDuck ([ScrapedDuck README](https://github.com/bigfoott/ScrapedDuck)).
  Phases 1 to 4 and the dashboard all depend on it. Until we get written
  permission or replace it, GO live data has to stay free and ad-free.
- **The Pokémon Company tends to act once a fan project makes money.** Its
  former general counsel said they "wait to see if they get funded ... if they
  get funded then that's when you engage"
  ([VGC](https://www.videogameschronicle.com/news/former-pokemon-lawyer-says-fundraising-and-press-coverage-lead-to-fan-project-takedowns/)).
  Official sprites are its copyright, and the PokeAPI sprites repo says so
  ([LICENCE.txt](https://raw.githubusercontent.com/PokeAPI/sprites/master/LICENCE.txt)).
- **Our hosting plan is non-commercial.** Vercel's Hobby plan is "for your
  personal or non-commercial use" ([Vercel Terms](https://vercel.com/legal/terms)).
  Charging users means Vercel Pro at $20/month
  ([Vercel pricing](https://vercel.com/pricing)).
- **Per-question costs are cents or fractions of a cent** (estimate below).
  Brave web search is the most expensive single call, at $5 per 1,000.
- **Comparable AI Pokémon chat apps charge about $3 to $5 a month.** PokeGPT
  is €2.99/month and Tree Co.'s Dexter Pro is $2.99/month (sources in §1.6).

## 1. How comparable products make money

| Product | Model | Prices found | Source |
| --- | --- | --- | --- |
| LeekDuck | Ads (programmatic). No paid tier found. | Unknown | Ad-network cookies (Prebid, The Trade Desk, Lotame, OpenX) seen on leekduck.com by [F-Cookies](https://f-cookies.org/site/leekduck.com?lang=fr). [About page](https://leekduck.com/about/) lists social, Twitch and YouTube. |
| PokeRaid | Freemium: coins plus subscriptions, ads in the free app | Mega Guest/Host $15.99/month; coins $1.49 to $47.99 | [App Store](https://apps.apple.com/us/app/pokeraid-raid-from-home/id1507659524). Price history (from $9.99 to $15.99, 2025 to 2026) per third-party tracker [AppsLupa](https://appslupa.com/app/pokeraid-raid-from-home/id1507659524). Tiers explained in [r/PokeRaid](https://www.reddit.com/r/PokeRaid/comments/1189op1/pokeraid_introduces_mega_trainer_subscription/). |
| Poke Genie | Freemium: one-time unlock plus raid subscriptions, ads in the free app | Scan Pro + Remove Ads $9.99 one-time; Raid VIP $2.99, Raid Ultra $17.99, Raid Master $47.99 | [App Store](https://apps.apple.com/us/app/poke-genie-remote-raid-iv-pvp/id1143920524). Monthly billing and a revenue estimate of about $200K/month come from a third party, [Adapty](https://adapty.io/paywall-library/poke-genie/), so treat them as an estimate. One-time purchase confirmed by users on [Reddit](https://www.reddit.com/r/PokeGenie/comments/r4iovv/does_the_scan_pro_remove_ads_payment_only_last/). |
| Pokebattler | Freemium: ads for free users, subscription removes ads and unlocks features | Standard $2.99/month, Battler $9.99/month, Champion $19.99/month; 7-day trial | [pokebattler.com/subscription](https://www.pokebattler.com/subscription), [App Store](https://apps.apple.com/us/app/pokebattler-raid-party/id1499435805), [AppPricer](https://apppricer.com/app/1499435805) (third party). |
| Pokémon GO Hub | Ads through a network deal; paid writers; merchandise | Unknown | [Enthusiast Gaming press release, 2021](https://www.enthusiastgaming.com/enthusiast-gaming-adds-nine-new-video-game-fan-communities/), [GO Hub writer program](https://pokemongohub.net/post/featured/can-now-publish-guide-get-payed-go-hub/). |
| Serebii | Ads plus Patreon | Tier prices unknown (Patreon page didn't show them) | [Serebii Patreon](https://www.patreon.com/serebiinet), [ReaderFunded](https://readerfunded.com/site/serebii.net), [Serebii forums on ads](https://forums.serebii.net/threads/possible-ad-change.667436/). |
| Bulbapedia | Ads plus donations; ad-free in-app purchase | RemoveADS €7.99 on the Dutch App Store | [Bulbapedia talk: Privacy policy](https://bulbapedia.bulbagarden.net/wiki/Bulbapedia_talk:Privacy_policy/Archive_1), [App Store NL](https://apps.apple.com/nl/app/bulbapedia-wiki-for-pok%C3%A9mon/id1242159382?l=en-GB). |
| PvPoke | Donations (Patreon) | 364 members, $215.80/month shown on 16 Nov 2026; gift membership $5 | [PvPoke Patreon](https://www.patreon.com/pvpoke), [gift page](https://www.patreon.com/pvpoke/gift), [supporters list](https://pvpoke.com/contact/). |

### 1.5 Pokémon TCG price, scanner and bot products

| Product | Model | Prices found | Source |
| --- | --- | --- | --- |
| TCGplayer affiliate | Affiliate commission through Impact; first-click credit within 48 hours covers the whole cart | Commission reported as 3.5% by a third party; TCGplayer's own doc doesn't state the rate | [TCGplayer docs](https://docs.tcgplayer.com/docs/tcgplayer-affiliate-program), [Lasso](https://getlasso.co/affiliate/tcgplayer/) (third party) |
| Collectr | Freemium subscription | PRO $7.99/month, or $4.99/month billed annually | [getcollectr.com/pro](https://www.getcollectr.com/pro) |
| Dex (TCG) | Freemium subscription (Dex+) | $3.99 or $4.99/month, $34.99 or $44.99/year, $109 lifetime | [App Store](https://apps.apple.com/us/app/dex-for-tcg-collectors/id1555489854), [AppPricer](https://apppricer.com/app/1555489854) (third party) |
| Card Discord bots | Monthly subscriptions | PokeTCG Deals $6/month, Cozy Cards $4/month, Guardian TCG $3.99 and $12.99/month, The PokeGroup $2.99/month. *From search snippets, pages not opened.* | [poketcg.deals](https://www.poketcg.deals/), [Cozy Cards](https://discordbotlist.com/bots/cozy-cards), [Guardian TCG](https://guardiantcg.app/discord-bot/pricing), [The PokeGroup](https://www.thepokegroup.com/pricing) |

### 1.6 Pokémon AI chatbots (closest comparables)

| Product | Model | Prices found | Source |
| --- | --- | --- | --- |
| PokeGPT | Freemium. Free tokens (100,000 at signup, weekly top-up to 50,000), unlimited Premium with fair-use downgrade to a lighter model | €2.99/month, €19.99/year, €1.50 day pass | [FAQ](https://www.pokegpt.org/faq), [Premium](https://www.pokegpt.org/premium) |
| Tree Co. (iOS Pokédex with "Ask Dexter") | Free with 3 AI questions/day; one-time packs; AI subscription | Dexter Pro $2.99/month or $19.99/year; Competitive Pack $4.99 one-time (unlimited Ask Dexter) | [FAQ](https://www.treeco.app/faq/) |
| Questie Pokémon companion | Subscription | $19.99/month *(search snippet, not opened)* | [Questie](https://www.questie.ai/character-ai-chat/pokemon-ai) |

What this shows:
- **Ads plus donations** fund the reference sites (LeekDuck, Serebii, Bulbapedia, GO Hub).
- **Freemium subscriptions** fund the tools (Pokebattler, Poke Genie, PokeRaid).
- **$2.99 to $4.99 a month** is the going rate for AI chat and collector tools.
- **Donations alone are small.** PvPoke, one of the best-known GO tools, shows about $216/month on Patreon.
- Most of these show a "not affiliated with Nintendo / The Pokémon Company" disclaimer. Examples: [Pokebattler's App Store text](https://apps.apple.com/us/app/pokebattler-raid-party/id1499435805) and [PokeGPT's FAQ](https://www.pokegpt.org/faq).

## 2. Legal and IP landscape

*This is research, not legal advice. A short consult with an IP lawyer is
worth it before charging money.*

### 2.1 Nintendo / The Pokémon Company (TPC)

- **Enforcement follows money and attention.** The former TPC general counsel
  said press coverage is how they find projects, and they "wait to see if they
  get funded" before acting
  ([VGC, 2024](https://www.videogameschronicle.com/news/former-pokemon-lawyer-says-fundraising-and-press-coverage-lead-to-fan-project-takedowns/)).
- **Known takedowns:**
  - *Pokémon Uranium*, a fan game, lost its download links after takedown notices (2016) ([WIRED](https://www.wired.com/story/nintendo-takedown-pokemon-uranium/)).
  - *Pokémon Prism*, a ROM hack, got a cease-and-desist (2016) ([Ars Technica](https://arstechnica.com/gaming/2016/12/nintendo-sends-cease-and-desist-notice-to-pokemon-rom-hacker/)).
  - The *Pokémon Essentials* fan-game tool was shut down (2018) ([Ars Technica](https://arstechnica.com/gaming/2018/08/nintendo-shuts-down-tool-used-to-build-pokemon-fan-games/)).
  - The *Pokédroid* app was removed from Android (2011) ([Nolan Lawson](https://nolanlawson.com/2011/05/26/on-pokedroids-removal/)).
  - PokéBeach and Serebii got copyright notices over Black/White screenshots, and PokéBeach was told its registrar had received a DMCA notice (2010) ([Bulbanews](https://bulbanews.bulbagarden.net/wiki/Fansites_served_with_copyright_infringement_notices)).
- **What has been tolerated:** ad- and subscription-funded reference and tool
  sites like Serebii, Bulbapedia, Pokebattler, Poke Genie and PokeGPT
  (§1). That they keep running doesn't mean they have permission; whether they
  do is unknown.
- **The name.** PokéAPI's license states that "Pokémon and Pokémon character
  names are trademarks of Nintendo"
  ([PokeAPI LICENSE](https://raw.githubusercontent.com/PokeAPI/pokeapi/master/LICENSE.md)).
  - Using the trademark in a domain or product name can be challenged, for
    example under a WIPO domain dispute
    ([WIPO DIO2023-0006](https://www.wipo.int/amc/en/domains/decisions/pdf/2023/dio2023-0006.pdf)).
    A disclaimer helps but doesn't remove the risk
    ([Law Stack Exchange](https://law.stackexchange.com/questions/59850/if-i-don-t-profit-in-any-way-and-have-disclaimers-can-i-use-pok%c3%a9mon-names-in-my)).
  - "PokeAgent" uses the "Poke-" prefix, not "Pokémon". Several monetized apps
    do the same (PokeRaid, Poke Genie, Pokebattler, PokeGPT). No enforcement
    against a "Poke-" name turned up in this research, which doesn't prove
    there's none. Risk: low to moderate, unknown.
- **App stores.** A Pokédex app was rejected by Apple over IP
  ([r/iOSProgramming](https://www.reddit.com/r/iOSProgramming/comments/4b1l2s/pokedex_app_rejected_under_85_any_suggestions/)).
  Google Play removes "confusingly similar" apps
  ([Ars Technica](https://arstechnica.com/gaming/2012/08/google-play-cracks-down-on-confusingly-similar-apps/)).
  The web app avoids this. A store app would face it.
- **Sprites and art.** The PokeAPI sprites repo is CC0 only for what its
  authors own. It states "All image contents within are Copyright The Pokémon
  Company"
  ([LICENCE.txt](https://raw.githubusercontent.com/PokeAPI/sprites/master/LICENCE.txt)).
  The 2010 notices above were about images. The planned dashboard shows
  Pokémon sprites for raids and spawns, which puts more TPC art on screen.

### 2.2 Niantic / Scopely (Pokémon GO)

- Scopely bought Niantic's games business, including Pokémon GO, and the deal
  closed on 29 May 2025
  ([Scopely](https://www.scopely.com/en/news/scopely-to-acquire-niantic-games-business-which-includes-pokemon-go-one-of-the-most-successful-mobile-games-of-all-time)).
- Its terms
  ([Scopely Explore ToS, last modified 15 July 2026](https://nianticlabs.com/terms?hl=en))
  prohibit users from doing any of the following:
  - "extract, scrape, or index the Services or Content"
  - using the Services or Content "for any commercial purpose"
  - accessing them through "bots, spiders, crawlers, data mining tools"
- The Content license is "personal, noncommercial". These terms bind players
  of the game.
- **PokeAgent doesn't touch Niantic's servers.** It reads LeekDuck (through
  ScrapedDuck) and PvPoke. The 2016 shutdowns of PokéVision, PokéHound and
  others were about pulling data from Niantic's systems. The letters
  reportedly also cited "using Pokémon content in commercial services", and
  PokéHound charged money
  ([TechCrunch](https://techcrunch.com/2016/08/01/third-party-pokemon-go-tracking-services-get-shut-down/)).
- **Rule:** never call Niantic/Scopely APIs, use game accounts, or show
  live spawn locations. The plan already uses featured event spawns instead of
  wild spawns.

### 2.3 Data sources and vendors

| Source | Commercial use? | Key terms | What to change before monetizing |
| --- | --- | --- | --- |
| **ScrapedDuck / LeekDuck** | **No, as written.** | README: data scraped "with permission" from LeekDuck. Apps "cannot be hidden behind a paywall" and "cannot be monetized with advertisements". Credit ScrapedDuck and LeekDuck. Repo license is AGPL-3.0 ([GitHub API](https://api.github.com/repos/bigfoott/ScrapedDuck)). ([README](https://github.com/bigfoott/ScrapedDuck)) | Keep all GO live features free and ad-free. Add visible credit. Or ask bigfoott and LeekDuck (hello@leekduck.com per [LeekDuck's profile](https://teapawt.net/LeekDuck)) for written permission. Or replace the source. |
| **PokeAPI (data)** | Allowed under a BSD-style license, with a fair-use policy | "Locally cache resources", or risk an IP ban. Calls itself "primarily an educational tool". ([Docs](https://pokeapi.co/docs/v2), [LICENSE](https://raw.githubusercontent.com/PokeAPI/pokeapi/master/LICENSE.md)) | Cache responses (already the pattern). Keep the license notice. |
| **PokeAPI sprites (images)** | **The images are TPC's copyright.** | [LICENCE.txt](https://raw.githubusercontent.com/PokeAPI/sprites/master/LICENCE.txt) | Biggest IP exposure in a paid app. Options: text-only, original or commissioned art, or accept the same risk other paid apps carry. Decision needed. |
| **PvPoke** | Yes, MIT ([GitHub API](https://api.github.com/repos/pvpoke/pvpoke/license)) | Keep the copyright and license notice. The stats reflect game data, and MIT can't grant rights PvPoke doesn't hold. | Keep the MIT notice and credit. Consider supporting its [Patreon](https://www.patreon.com/pvpoke). |
| **Brave Search API** | Yes, paid prepaid credits | $5 per 1,000 Search requests. Storing results or training on them needs a custom plan. ([Brave API](https://brave.com/search/api/)) Each plan includes $5 of monthly credit, about 1,000 searches ([Brave on LinkedIn](https://www.linkedin.com/posts/brave-software_brave-search-api-brave-activity-7429560722956693505-cGsy)). | Don't persist Brave results in a cache or the vector DB. Set a spend limit. |
| **DeepSeek API** | Yes | You may integrate it into services for "external end users". DeepSeek assigns you rights in Outputs. You must "clearly disclose to your end users that the Output content is generated by AI". PRC law governs. ([Open Platform ToS, effective 29 Apr 2026](https://cdn.deepseek.com/policies/en-US/deepseek-open-platform-terms-of-service.html)) Personal data is stored in the PRC ([privacy policy, Chinese](https://cdn.deepseek.com/policies/zh-CN/deepseek-open-platform-privacy-policy.html), as summarized in search results). | Add an "answers are AI-generated" notice. Add a privacy policy that names DeepSeek and China-based processing. Send no user personal data. |
| **Pinecone** | Yes, under the subscription agreement (internal business purposes, no reselling Pinecone itself) ([MSA](https://www.pinecone.io/legal/master-subscription-agreement/), summarized by search) | Starter is free but capped, including only 500 reranks/month for `bge-reranker-v2-m3`, which we use. Builder is $20/month flat, with 1,000 reranks and "additional usage ... blocked". Standard has a $50/month minimum, then reranking costs $2 per 1,000. ([Pricing](https://www.pinecone.io/pricing/), [cost docs](https://docs.pinecone.io/guides/cost/understand-cost)) | Budget for Builder or Standard, or drop or limit reranking. |
| **Vercel** | **Hobby is non-commercial only** | "You shall only use the Services under a Hobby plan for your personal or non-commercial use" ([Terms](https://vercel.com/legal/terms)). A third-party summary says donations aren't commercial use but ads and payments are ([search summary](https://vibeliftoff.com/guides/vercel-hobby-commercial-use/)). Unconfirmed on Vercel's own pages. | Move to Pro ($20/month per developer seat, [pricing](https://vercel.com/pricing)) before charging or running ads. Confirm the donation question with Vercel. |

## 3. Unit economics (estimate)

**This is an estimate, not a measurement.** The token counts are assumptions.
The repo doesn't record real per-run token totals yet. Here's what the code
shows:
- The model is `deepseek-v4-flash` (`backend/agents/custom.py`). DeepSeek says
  that name now bills at the `deepseek-flash` price
  ([pricing](https://api-docs.deepseek.com/quick_start/pricing)).
- Each run is capped at 8,000 output tokens (`MAX_OUTPUT_TOKENS`) and five
  model calls.
- Pinecone retrieval reranks with `bge-reranker-v2-m3`.
- The prompt module plus tool registry is about 47 KB of source. That
  suggests roughly 5 to 8k tokens of fixed prompt and tool schemas per model
  call (an assumption).

**Prices used:**
- DeepSeek Flash, per million tokens:
  - Peak: input $0.30 on a cache miss, $0.006 on a cache hit; output $1.20.
  - Off-peak: half those rates.
  - Source: [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing).
- Brave: $0.005 per search ([Brave](https://brave.com/search/api/)).
- Pinecone Standard ([pricing](https://www.pinecone.io/pricing/)):
  - Rerank $0.002 per request.
  - Read units $16 to $18 per million. A small namespace costs 0.25 RU per query ([docs](https://docs.pinecone.io/guides/cost/understand-cost)).
  - Embedding $0.16 per million tokens.

| Scenario (assumed) | Tokens assumed | DeepSeek (peak, no cache) | DeepSeek (prefix cached) | Brave | Pinecone | **Total per question** |
| --- | --- | --- | --- | --- | --- | --- |
| Quick fact ("what's quick catch?"): 2 model calls, 1 guide lookup | ~16k in, ~0.6k out | ~$0.0055 | ~$0.0014 | $0 | ~$0.002 (rerank) | **~$0.003 to $0.008** |
| Live GO lookup (raids, eggs): 2 calls, 1 cached ScrapedDuck tool | ~18k in, ~0.8k out | ~$0.0064 | ~$0.0022 | $0 | $0 | **~$0.002 to $0.006** |
| Analytical, with web search: 4 calls, 2 Brave searches, 1 retrieval | ~49k in, ~3k out | ~$0.018 | ~$0.010 | $0.010 | ~$0.002 | **~$0.022 to $0.030** |

The cached figures assume DeepSeek's cache hit rate covers the fixed
prompt. Pinecone read units and embeddings come to well under $0.0001 per
query and are rounded away. Off-peak rates cut the DeepSeek column in half.

**Blended assumption:** about $0.01 per question. Per user per month:
- Light, 50 questions: about $0.50.
- Regular, 300 questions: about $3.00.
- Heavy, 1,000 questions: about $10.00.

**Fixed costs once monetized:**

| Item | Monthly cost |
| --- | --- |
| Vercel Pro ([pricing](https://vercel.com/pricing)) | $20 |
| Pinecone Builder or Standard ([pricing](https://www.pinecone.io/pricing/)) | $20 or $50 minimum |
| Brave | $0 for the first ~1,000 searches (monthly credit) |
| Backend hosting, if not on Vercel | Unknown, depends on host |
| **Total** | **About $40 to $70**, plus usage |

**Payment fees** come off each subscription:
- Stripe: 2.9% + 30¢ per domestic card charge ([Stripe](https://stripe.com/pricing)), so about $0.42 on a $3.99 charge.
- Apple: 15% under its Small Business Program, if we ever ship an iOS app ([Apple](https://developer.apple.com/app-store/small-business-program/)).

### Suggested price points

Comparable products charge:
- AI chat: PokeGPT €2.99/month, Tree Co. $2.99/month.
- GO tools: Pokebattler $2.99/month.
- Collector tools: Collectr and Dex $3.99 to $7.99/month.

| Tier | Price | What it includes | Rationale |
| --- | --- | --- | --- |
| **Free** | $0 | All GO live data and dashboard (required by ScrapedDuck's terms as written). About 10 to 15 questions a day, with web search limited to a few a day. | At ~$0.01 a question, a daily-active free user costs about $3 to $4.50 a month at the cap. Most won't hit it. The web-search limit is the main cost control. |
| **Trainer (paid)** | **$3.99/month or $29.99/year** | Higher daily limit (for example 100 questions a day under a fair-use cap), more web searches, deeper analytical answers, saved team-builder history, main-series and PvP extras. Only features that don't depend on ScrapedDuck data. | In line with the market. After Stripe fees about $3.57 net. Covers a "regular" user (~$3) with a small margin. A fair-use cap (like PokeGPT's lighter-model fallback) protects against heavy users. |
| **Supporter** | Pay-what-you-want (Ko-fi, GitHub Sponsors or Patreon), no perks gated on GO data | Thanks, credits page | Lowest risk. Patreon-level income is likely small (PvPoke: ~$216/month). |

Break-even, rough: $40 to $70 a month in fixed costs needs about 15 to 25
paid subscribers, plus enough margin to cover free-tier usage. A $4.99/month
price would leave more room. $3.99 matches the "not super expensive" goal
and the market.

## 4. Recommended path (low risk to higher risk)

1. **Stay free, add a donation link, and fix compliance now.** Lowest risk.
   - Add credit for LeekDuck, ScrapedDuck, PvPoke (MIT) and PokeAPI.
   - Add a "not affiliated with Nintendo, The Pokémon Company, Game Freak,
     Creatures or Scopely/Niantic" disclaimer.
   - Add an "answers are AI-generated" notice (required by DeepSeek's terms).
   - Write a privacy policy that names DeepSeek, Brave and Pinecone.
   - Add a perk-free donation link.
   - Confirm with Vercel that donations are OK on Hobby, or move to Pro.
2. **Ask LeekDuck and ScrapedDuck for written permission** to run a paid tier
   and/or ads. Do this before any paywall, since GO is the app's main draw.
   If they say no, keep GO live data free forever, or plan a replacement
   source (cost and licensing unknown).
3. **Freemium subscription ($3.99/month, $29.99/year) through Stripe.** Medium risk.
   - Paywall only usage limits and features that don't use ScrapedDuck data:
     main-series analysis, team-builder extras, PvPoke-based extras, higher
     limits.
   - Requires Vercel Pro, a Pinecone paid plan, terms of service, a refund
     policy and tax handling.
   - Decide on sprites first (see open questions).
4. **Affiliate links (TCGplayer), if a card feature is ever added.** Medium risk.
   - TCGplayer runs its program through Impact
     ([docs](https://docs.tcgplayer.com/docs/tcgplayer-affiliate-program)).
   - Ambiguity: ScrapedDuck's ad ban may be read to include affiliate links.
     Keep them off GO screens.
5. **Display ads.** Higher risk, not recommended.
   - Ads break ScrapedDuck's terms as written and need Vercel Pro.
   - They would bring in little at our traffic.
   - They put official sprites next to ad revenue, the "commercial use" TPC
     has acted on.
6. **App store release with official art, or "Pokémon" in the name.**
   Highest risk. Apple and Google can reject or remove the app over IP. It also
   raises the profile that TPC's former counsel said draws attention.

## Open questions for Thomas

1. **GO data permission.** Should we email LeekDuck and ScrapedDuck to ask
   about a paid tier? If they say no, are you OK keeping GO live data free
   forever?
2. **Sprites.** The dashboard plan shows Pokémon images. For a paid version,
   pick one:
   - keep official sprites and accept the risk,
   - go text-only or icon-only,
   - commission original art (cost unknown).
3. **Name.** Keep "PokeAgent" (low to moderate, unknown risk) or pick a name
   without "Poke"?
4. **Price.** $3.99/month and $29.99/year, or $4.99/month for more margin?
   Would you offer a day pass like PokeGPT's €1.50?
5. **Free-tier limit.** How many questions a day, and how many web searches?
6. **Hosting.** Are you OK moving to Vercel Pro ($20/month) and a Pinecone paid
   plan ($20 to $50/month) once money comes in? Or keep reranking under
   Starter's 500/month?
7. **DeepSeek data location.** Are you comfortable with user questions being
   processed in China, disclosed in a privacy policy? Or should a paid tier
   use a different model provider (cost not researched here)?
8. **Legal review.** Should we budget for a one-time IP lawyer consult
   before launch (cost unknown)?
