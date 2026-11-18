# Trainermon: next plan

Status: **proposed, not built.** Decisions 4 to 10 in `decisions.md`
(17 November 2026) are the constraints. This file is the order to approve
before any of it is implemented. The licensing review is
`licensing-data-review.md`. The personal app is out of this plan.

Nothing here asks LeekDuck, ScrapedDuck, Pokebattler, or pogoapi.net for a
licence. Decision 5 closed that for now.

## Size words

- **Small:** a few commercial UI files. No new table.
- **Medium:** one new module, an additive table, and tests.
- **Large:** a new product surface across the API and the UI.

These are build size, not a calendar.

## Suggested order

1. **A. Compact rows.** Already approved. No new data and no contact between
   users. It is the smallest visible change.
2. **B. Base catalog import.** Already approved. Species identity comes from
   PvPoke and PokéAPI before anyone curates shiny or Dynamax on top.
3. **C. Curated GO layer.** Needs B's species ids. Thomas still has to name
   who approves rows.
4. **G. Age gate and policy drafts.** Before the app is offered to the
   public, and before any feature that shows a friend code. Drafts only.
   A lawyer still has to read them before charging (phase H).
5. **D. User reports.** Needs a catalog row to report against, and the age
   gate, so reports are not the first thing a child can submit.
6. **F. Stripe in test mode.** Needs the tier table below confirmed. No live
   charges. Raid priority needs a real entitlement, so F lands before E.
7. **E. Remote-raid matchmaking.** The first paid feature. Needs F's
   entitlements, G's age gate, and opt-in friend codes.
8. **H. Open items before charging.** Not a build. Lawyer, trademark search,
   sprites stay off. Live Stripe is the switch after Thomas says H is done.

A and B can be reviewed as separate later PRs. Do not start C's admin page
before B's ids exist. Do not start E before F and G.

## Feature by tier

Prices are decided. Annual amounts are not. What the middle tier adds beyond
raid priority is a proposal: Thomas confirms it in phase F before products
are created in Stripe.

| Feature | Free | $4.99 / month | $9.99 / month |
| --- | --- | --- | --- |
| Want and have lists | Yes | Yes | Yes |
| Trade search (no model, no friend code) | Yes | Yes | Yes |
| Explorer | Yes | Yes | Yes |
| Assistant | Yes, with a cap Thomas sets | Same assistant, higher cap (proposal) | Same assistant, higher cap (proposal) |
| Remote raids: see open lobbies | Yes | Yes | Yes |
| Remote raids: queue | Back of the queue | Ahead of Free | Ahead of $4.99 and Free |
| Trade alerts | No | Not in this plan | Not in this plan |
| Collection sims | No | No | No |
| In-app chat | No | No | No |
| Official sprites | Off | Off | Off |
| Annual plan | No | Price not set | Price not set |

Trading stays free. Both paid tiers are "paying users" for decision 7. The
table puts $9.99 ahead of $4.99 so the higher price buys a shorter wait.
Thomas can collapse those two paid bands into one priority. That is an
approval question in phase F, not a silent default.

## A. Compact rows

**Scope.** In `commercial/` only, replace the large initial cards on lists,
trade results, and Explorer with compact text rows.

- Dex-number badge, for example `#0131 Lapras`. Until phase B, the hand seed
  has no dex number, so this phase may show the name and a placeholder badge
  and phase B fills the number. Do not invent numbers.
- Type labels are our own colours and our own words. Not the official type
  symbols.
- Variant chips: Shiny, Dynamax, Gigantamax, costume, Lucky, Shadow.
- A config flag for official sprites, default off. Off means the row has no
  image slot. No sprite files are added.

**Acceptance.**

- Lists, trades, and Explorer render rows, not the large letter cards.
- A row's type label is text. No official type icon is in the markup.
- With the flag off, the page requests no sprite URL.
- Footer still says the app is not affiliated with Nintendo, The Pokémon
  Company, Game Freak, or Scopely/Niantic, and that there is no official art.

**Size.** Small.

**Thomas approves.** Nothing new if the chips match decision 6. A screenshot
of one list row and one Explorer row is the review.

## B. Base catalog import

**Scope.** Replace the hand seed's species list with a generated catalog:

- PvPoke gamemaster (MIT): species, forms, types, stats, moves, and the tags
  it actually has (regional, legendary, mythical, shadow, and the incomplete
  untradable tag).
- PokéAPI (BSD): national dex number and the main-series types and names
  used to label a row.
- A refresh script a human runs. It downloads those two sources only. It
  does not fetch PokeMiners, Bulbapedia, LeekDuck, ScrapedDuck, or any
  Scopely or Niantic site.
- An "Open-source data" credit with the MIT and BSD notices and links.
- The current GO flags on the seed (shiny, Dynamax, Gigantamax, costume)
  move to the curated layer in phase C. Until C lands, those flags can stay
  on the overlapping species so Explorer does not go blank. They are marked
  as the old seed, not as the new import.

**Acceptance.**

- A test loads Lapras (or another species present in both sources) and
  checks dex number, name, and types against a fixture committed from a
  recorded download, not against a live call.
- The script fails if pointed at a PokeMiners, Bulbapedia, or pokemongolive
  URL.
- Credits render the MIT copyright line and the BSD notice.
- `untradeable` from PvPoke is stored as a hint, not as the only block.
  Mythical blocking stays an explicit curated rule (phase C), because that
  tag is incomplete.

**Size.** Medium. A script, a generated JSON file, a credits page, tests.

**Thomas approves.** The field list above, and that refresh is manual.

## C. Curated GO layer

**Scope.** A table Trainermon owns, one row per fact, not a copied
announcement.

Suggested columns: species id, fact kind (shiny, dynamax, gigantamax,
costume, raid, event, trade rule), the value, `source_url`, `verified_at`,
`verified_by`, and status (`draft`, `approved`, `rejected`).

Curation flow:

1. A signed-in curator pastes announcement text. The app does not fetch the
   URL.
2. The assistant drafts rows from that paste only. It does not browse.
3. A human approves, edits, or rejects each row. Drafts are not visible on
   Explorer, lists, or raids.
4. Approved rows carry the source link and the verified date on the admin
   screen. The public row can show "checked on {date}" without copying the
   announcement.

Seed: a first set of current shinies and Dynamax entries, each with a source
link and a verified date, written in our words. Thomas, or a person he
names, approves that seed in the same flow. An AI draft of the seed is
allowed only from text he pastes.

Trade-rule rows (mythical block, Good Friends, Forever Friends, shadow not
remote) are curated facts too. Meltan and Melmetal stay an open check: the
review did not confirm the in-person exception on an official page. Do not
ship a Meltan trade-rule row until that page is pasted and approved.

**Acceptance.**

- A pasted paragraph can produce a draft row, and the draft is invisible to
  a normal user.
- Approving it makes it readable. The stored row has `source_url` and
  `verified_at`.
- A test rejects a row with an empty source or an empty date.
- No code path HTTP-fetches pokemongolive.com, nianticlabs.com, or a
  LeekDuck host.
- The comparison agents are unchanged. Drafting is a separate call with a
  curation prompt, not a change to how the assistant answers trainers.

**Size.** Large. Schema, admin screen, draft endpoint, seed file, tests.

**Thomas approves.** Who may approve rows (himself, or a named moderator).
The seed does not ship until that person has approved it. Also the column
list, if he wants raids and events in the first seed or only shiny and
Dynamax.

## D. User reports

**Scope.** A signed-in trainer can report an error on a catalog or curated
row: "this shiny flag is wrong", "this costume is missing", with a short
note. Reports are text and tags. No images in this phase (that needs a DMCA
agent, which is not in scope).

A moderator queue shows the report. Confirming it does not edit the row by
itself. It opens a draft for the phase C approval flow. Rejecting it hides
it. Reports do not auto-publish.

No bot submissions: the route requires a session, and a per-user cap is
enforced in code.

**Acceptance.**

- A stranger gets 401.
- A report stores the user, the row, the note, and a timestamp.
- The public Explorer does not change until a curator approves a new fact.
- A test covers the cap.

**Size.** Medium.

**Thomas approves.** Who moderates (can be the same person as phase C), and
that reports never auto-publish.

## E. Remote-raid matchmaking

**Scope.** The first paid feature. Plain lobbies, not an assistant.

- A host opens a lobby: boss (a catalog species), start time, and optional
  city. Toronto can be the default city, matching lists.
- The host's friend code is attached only if they have opted in. Otherwise
  the create action fails with a message that says opt in first.
- A joiner asks for a seat. The queue orders by tier (see the table), then
  by request time.
- When the host accepts a joiner, each person in that pair sees the other's
  friend code if both opted in. Trade search still does not show codes.
- Lobby status is a fixed set: open, full, started, cancelled. No free-text
  chat. Decision 9.
- A report action flags a lobby that offers an account, coins, or paid
  hosting. A moderator can close it.

Scopely terms, as acceptance constraints:

- The app never reads a game account, a game token, or game traffic.
- The app never sends a bot into a raid. Joining the raid stays in the
  official app, after the trainers add each other.
- The app does not sell hosting and does not pay a host. Priority is a
  shorter wait, not a paid raid-host service.
- The app does not sell remote-raid passes and does not claim to raise the
  daily remote-raid limit. Lobby copy says the limit is the player's to
  follow. We cannot see their count, because we do not read the account.
- Account trading stays banned. A lobby note that sells an account is a
  report reason.

**Acceptance.**

- Two free users and one $9.99 user request the same lobby in that order.
  The paid user is offered first. A test uses a fake entitlement, not a
  live card.
- A host who has not opted in cannot create a lobby.
- A joiner who has not opted in cannot be accepted.
- The lobby payload has no email address.
- No route takes a game username or a session token from Pokémon GO.

**Size.** Large.

**Thomas approves.** Whether $4.99 and $9.99 are two priority bands or one.
Whether lobbies are city-scoped at launch (Toronto only, or any city).
The max lobby size. That we do not pay hosts.

## F. Subscriptions (Stripe, test mode)

**Scope.** Web checkout only. Stripe test keys. No app store product.

- Products: $4.99 monthly, $9.99 monthly, and two annual prices once Thomas
  sets them. A suggestion to react to, not a decision: charge 10 months for
  12. He picks the number before the products exist.
- Free is the absence of a subscription.
- A webhook sets an entitlement on the user: `free`, `plus` ($4.99), or
  `pro` ($9.99). Names can change. The rank is what the queue reads.
- Cancel and the customer portal stay in Stripe's test portal.
- The server rejects a live secret. Test mode is a code check, not only a
  comment. Live keys wait for phase H.
- What each tier unlocks is the table above, after Thomas confirms it.

**Acceptance.**

- A test webhook fixture moves a user from free to pro and back.
- The raid queue test from phase E reads that entitlement.
- The repo has no Stripe secret. `.env.example` lists the key names only.
- Hitting checkout with a live-looking key fails the test.

**Size.** Large. Billing routes, webhook, entitlement column, a pricing
page, tests. No new paid dependency beyond Stripe's HTTP API. If a Stripe
SDK is wanted, that is a dependency ask before the phase starts.

**Thomas approves.** The annual amounts. Whether the two paid tiers share
one raid priority. The assistant cap, if the middle tier should change it
at all. That test mode stays until phase H.

## G. Age gate, privacy, and terms

**Scope.** Drafts and a gate. Not a lawyer's sign-off.

- Signup asks for age. Under 13 cannot create an account. 13 and over can.
  Store a boolean `age_ok`, not a full birth date, unless Thomas wants the
  date. The boolean is the smaller record.
- Existing local accounts are unchanged until this phase. Before a public
  launch, unsigned-in visitors hit the gate.
- `commercial/docs/privacy-draft.md` and `commercial/docs/terms-draft.md`,
  labeled drafts.
- Privacy draft covers: email, password hash, trainer name, city, optional
  friend code, lists, and later raid lobbies. Friend codes stay off other
  people's screens except an opted-in raid lobby. No game account. No sale
  of personal information. City only, not GPS. How to delete the account.
  Subprocessors named in plain language: host, Stripe when billing is on,
  and the model provider if the assistant is still called.
- Children's notes, in the draft, not as advice: the US COPPA rule as
  amended is in force from 22 April 2026, and the simplest compliance with
  decision 9 is not to offer the service to under 13. Canada's OPC
  Children's Privacy Code (20 October 2026) expects parental consent under
  13. The draft says we do not knowingly keep data from under 13 and we do
  not profile children.
- Terms draft covers: not affiliated with the rights holders, no account
  trading, users license us their reports, catalog and AI answers can be
  wrong, and a refund line Thomas fills in before live charges.

**Acceptance.**

- The register API rejects an under-13 flag.
- The two drafts exist and say "draft" in the title.
- The privacy draft does not claim a lawyer has approved it.

**Size.** Medium.

**Thomas approves.** The draft text before it is linked from the app. The
choice of a boolean versus a birth date. The refund sentence, which can
stay a blank he fills in phase H.

## H. Open items before charging

Not a coding phase. Live charges stay off until all of these are done.

1. A consult with a Canadian IP and privacy lawyer, using the drafts from G
   and the data rules from decisions 4 and 6.
2. A trademark search for "Trainermon" in CIPO and USPTO. The review did
   not query those databases.
3. Sprites: stay off unless that consult says otherwise. The flag from
   phase A is the switch. Default remains off. Marketing, the logo, and the
   site icon never use Pokémon art even if the flag is later turned on.
4. Thomas sets annual prices and the refund line, then says test mode may
   become live mode.
5. Hosting: the review notes Vercel Hobby is non-commercial, so a paid host
   plan is part of turning on charges. Confirm the plan before the switch.

**Acceptance.** A short note in `decisions.md` that the consult happened,
the trademark search happened, and Thomas allowed live charges. Until that
note exists, the live-key check from phase F stays in place.

**Size.** No application code.

**Thomas approves.** This whole list, by doing it. The plan does not pick a
lawyer or file a trademark.

## Hard rules for every phase

- No PokeMiners files or assets.
- No Bulbapedia text.
- No LeekDuck or ScrapedDuck data.
- No scraping of Scopely or Niantic sites.
- No game-account access, and no bots.
- No paying users to host or trade.
- No in-app chat.
- Friend codes stay opt-in, and trade search keeps hiding them.
- Sprites stay behind the flag, default off.
- Stripe stays in test mode until phase H is done.

## Still open inside this plan

- Who approves curated rows, and who moderates reports.
- Annual prices, and whether $4.99 and $9.99 are one raid-priority band or
  two.
- Whether the $4.99 tier changes the assistant cap. The table marks that as
  a proposal.
- Meltan and Melmetal, until an official page is pasted and approved.
- Trade-alert and collection-sim ideas from the review. They are not in
  the tier table as commitments.
