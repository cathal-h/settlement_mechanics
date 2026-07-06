# Settlement Mechanics — Prototype Notes (for the Rust port)

`multi_runner.py`, `over_under.py`, `score_differential.py` are a working prototype of
the settlement logic that needs to land in `rust_implementation/contract.rs`. This doc
leads with how the prototype maps onto the Rust types, since that's the part that
wasn't clear from the code alone, then covers the design decisions behind it.

## 1. Mapping onto `contract.rs`

`PmContract`'s fields already match the prototype's `Contract` field-for-field —
`id`, `key`, `name`, `alias`, `unit_class`, `unit_class_value: String` all mirror
directly (`unit_class_value` stays a plain string on both sides on purpose: it holds a
team name, a margin like `"2.5"`, or a total, depending on `unit_class` — no need to
split it into a typed union yet).

What each `PmSettlementMechanic` should resolve to:

| Rust mechanic | Prototype file | `unit_class` | Status |
|---|---|---|---|
| `Diff` | `score_differential.py` | `HandicapMargin` | Fully prototyped, including 3-way head-to-head (see §2) |
| `Over` | `over_under.py` | `Total` | Fully prototyped (file predates the `Over`/`Total` naming — flag if we want to rename one to match) |
| `Rank` | `multi_runner.py` | `Participant` | Any N ≥ 2 outcome winner market, including two-outcome head-to-head — see §3.4. Dead-heat/partial-settlement not yet prototyped |

**`PmSettlementMechanic::TwoWay` should be retired.** A two-outcome head-to-head
market is just `Rank`/Participant with two contracts, not a distinct mechanic — see
§3.4 for the reasoning and the one case that still isn't Participant (Draw No Bet).

One thing exists in the prototype with no Rust counterpart yet:

- **`Comparator` (`GreaterThan` / `LessThan` / `EqualTo`)** — lives in
  `score_differential.py`, shared by `over_under.py`. This is what lets a contract's
  tie behavior be "push" vs. "this is a real winning outcome" (see §3.2) — it needs to
  exist before `Diff`/`Over` contracts can settle correctly.
- **`push_possible: bool`** — currently modeled as a market-level flag on
  `PmProperties`. It needs to move to per-contract, because two products can share a
  market and a `unit_class_value` but disagree on tie behavior (Draw No Bet vs. 1X2 —
  see §3.2).

## 2. Answering the `test_moneyline` question directly

`test_moneyline` builds France / Draw / Morocco as three `PmUnitClass::Binary`
contracts under `PmSettlementMechanic::TwoWay`
([contract.rs:192-262](rust_implementation/contract.rs#L192-L262)) — but the struct
it's meant to populate, `PmOutcomeState`
([contract.rs:126-132](rust_implementation/contract.rs#L126-L132)), has fields
`all_more / win_by_2 / win_by_1 / draw / all_less` — a differential-bucket shape.
Those two don't fit together: `Binary`/`TwoWay` describes independent yes/no outcomes
with no shared axis, but the output shape assumes all three legs settle off one shared
score differential. That mismatch is the source of the confusion.

The fix: a 3-way market is a **`Diff`** market, not `TwoWay`/`Rank`. All three legs
settle off the same `d = score_1 - score_2`:

- `france` leg: `HandicapMargin`, `unit_class_value = "0"`, `GreaterThan`, no push.
- `morocco` leg: same `d`, its own perspective (`score_2 - score_1`) — a real contract
  with its own price, not a mirror of `france`'s.
- `draw` leg: `unit_class_value = "0"`, `EqualTo` — `d == 0` is this contract's
  *winning* condition, not a push (see §3.2).

`test_three_way_head_to_head_maps_onto_diff` in `score_differential_test.py` proves
this mapping end to end with real numbers and is the intended template for rewriting
`test_moneyline`. `PmOutcomeState`'s fixed five buckets should also generalize to a
swept range (`{d: pnl}`, same as `build_outcome_vector`'s output) rather than fixed
named fields — the current struct only has room for margins up to 2, and doesn't
extend to arbitrary handicap lines.

## 3. Design decisions carried over from the prototype

### 3.1 No canonical side — each contract computes its own differential

Earlier drafts tried a canonical home/away `d` with the away side represented as a
short position, and later as a fully mirrored contract. Both were rejected: the first
because `payout(PUSH) = 0` regardless of position sign only makes short-vs-mirror
equivalent if `price_home + price_away == 1` exactly, which isn't true for
independently-priced order books; the second because it doesn't remove the underlying
sign-convention bug, it just relocates it.

**Resolution, implemented in `score_differential.py`:** a contract carries its own
`key` (e.g. `"team_1"`) and computes `d = scores[self.key] - scores[other_key]`
itself from a raw `{key: score}` mapping. There's no shared sign convention to get
backwards. This fixed a real bug in the old model: an "away +2.5" contract expressed
against a home-oriented `d` resolved backwards at the extremes.

`over_under.py` never had this problem — `score_1 + score_2` is order-independent, so
Over/Under was always self-contained. `multi_runner.py` never had a side to begin
with.

### 3.2 Push vs. exact-outcome are different comparators, not a tie-behavior flag

- **Push** = stake refunded, pnl = 0. A tie voids the bet (spreads, Draw No Bet).
- **Exact-outcome** = the tie *is* the winning condition, full payout like any other
  YES (1X2 draw leg, "exactly 201 points").

These must not be conflated — a market can offer both at once (DNB and 1X2 share the
same `d`, same `unit_class_value = 0`, opposite tie behavior).

Rather than a 3-state `TieBehavior` discriminator layered on top of ordinary
contracts, an exact-outcome contract is just an ordinary contract using a third
comparator, `EqualTo`, alongside `GreaterThan`/`LessThan`. It resolves plain
MARK100/MARK0 — there's no boundary to arbitrate, equality *is* the whole condition.
`push_possible` only applies to the ordering comparators; `EqualTo` ignores it
entirely, since there's nothing to push.

`push_possible` stays an explicit, caller-supplied bool — it can't be derived from the
value alone (DNB vs. 1X2 at the same `unit_class_value = 0` need different tie
behavior on identical numbers).

### 3.3 Outcome-vector shape differs by mechanism, and that's fine

`Diff`/`Total` contracts share one continuous "value → pnl" sweep. `Participant`
contracts fundamentally can't — there's no ordering over outcome names. Decision: keep
the discrete-label vector (`multi_runner.build_outcome_vector`) separate from the
continuous-range vector (`score_differential`/`over_under`'s), rather than forcing one
shape to fit both.

### 3.4 Two-way head-to-head is Participant, not a separate mechanic

If the underlying event has exactly two possible results (tennis, basketball — no
draw is possible at all), "who won" is the entire market: it's `multi_runner.py`'s
shape with two contracts, no line, no margin, no push. There's no reason to also model
it as a `Diff` contract pair at `±0.5` — that was an equivalent but unnecessary
encoding, and it's what `PmSettlementMechanic::TwoWay` was standing in for. Retire
`TwoWay`; this is just `Rank` with `number_of_winners = 1` and two contracts.

**The one exception: Draw No Bet.** DNB only ever lists two contracts, but a draw is a
real possible outcome of the underlying event (soccer) — "who won" alone can't express
"there was no winner, refund." DNB still needs the score differential and
`push_possible` at `d == 0`, so it stays a `Diff` market (§3.2), same as 3-way,
despite having only two backable outcomes.

**Rule of thumb:** if a draw is a real possible outcome of the underlying event — even
if it's not separately backable (DNB) — the market is `Diff`. Only if the underlying
event truly has no draw is it `Participant`, regardless of how many contracts it has.

### 3.5 Both sides are always real contracts — where that stays separate vs. combines

Decided: we always create two real, independently-priced contracts for a two-sided
market (e.g. Home −0.5 and Away +0.5) rather than deriving one side's price as
`1 - other side's price`. `price` means "what this specific holder actually paid" —
synthesizing it would fabricate data that may not match reality, and separately-listed
order books don't actually guarantee `price_a + price_b == 1` anyway.

That split shows up differently at different layers:

- **Stay separate:** pricing, order books, and positions. Each contract has its own
  `id`, its own `price`, its own held `position`. Nothing about settlement should ever
  need to reconcile one contract's price against the other's.
- **Combine:** settlement and aggregation. Both contracts settle off the *same*
  underlying score/differential, so `build_outcome_vector` walks one shared range and
  sums every contract's payout against it in a single pass (§3.1's self-describing
  `key` is what makes this possible without a reconciliation step). The combining
  happens at aggregation time, purely as a read over already-independent contracts —
  never by having one contract's data depend on the other's.

## 4. Lexicon

Terms that have drifted across code/notes — use these going forward:

| Term | Means |
|---|---|
| **Contract** | One backable outcome: `key`, `price`, `position`, resolves to a `Mark`. |
| **Mark** | `MARK100` (YES) / `MARK0` (NO) / `PUSH` (refund) — how a contract resolves. |
| **Mechanism** | `Diff`, `Total`, or `Participant` — the three settlement mechanics. |
| **`key`** | The subject a contract is about (e.g. a team). Lets a contract compute its own differential with no canonical side (§3.1). |
| **`d`** | Score differential from a contract's own `key`'s perspective (`self_score - opponent_score`). `Diff` mechanism only. |
| **`unit_class_value`** | The value a contract's resolving number/name is compared against — a margin, a total line, or a participant name. Stays a string regardless of mechanism, for Rust parity. |
| **`Comparator`** | `GreaterThan` / `LessThan` / `EqualTo` — how the resolving value relates to `unit_class_value`. |
| **`push_possible`** | Per-contract flag: does a tie at the boundary refund the stake? Only meaningful with `GreaterThan`/`LessThan`. |
| **Exact-outcome contract** | A contract using `EqualTo` — the tie *is* its win condition, not a push (e.g. a draw leg). |
| **`position`** | Signed number of contracts held — not a dollar stake. |
| **`price`** | The real average price this holder paid for this specific contract. |
| **payout / pnl** | `position * (outcome_value - price)`. |
| **Diff market** | Settles off a shared score differential — handicaps, 3-way head-to-head, DNB. |
| **Total market** | Settles a total score against a line — Over/Under, exact totals. |
| **Participant market** | Settles on which name won — any N ≥ 2 outcomes with no draw possible, including two-way head-to-head (§3.4). |

**Avoid:**
- *"moneyline"* — ambiguous between two-way (Participant) and 3-way-with-draw (Diff).
  Say "two-way head-to-head" or "3-way head-to-head" instead.
- *"side" / "home" / "away"* as a canonical axis — use `key`; there is no canonical
  side (§3.1).

## Open questions for eng

1. Beyond DNB-vs-1X2, is there another case where the same numeric value needs
   different `push_possible` behavior across concurrently-offered products? Want
   §3.2's resolution to cover the general case, not just this one example.
2. `Rank`/dead-heat markets (multiple winners, partial settlement) aren't prototyped
   at all yet — `multi_runner.py` only covers single-winner Participant markets.
