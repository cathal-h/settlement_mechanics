"""
Prototype: converting individual contracts into a single
aggregated `outcome_state`.

Each contract is self-describing: it knows its own subject via `key` (e.g. a team
name) and derives its own resolving differential from a raw per-team score mapping,
e.g. {"team_1": 3, "team_2": 1}. There is no canonical side/POV -- a contract with
key="team_1" computes scores["team_1"] - scores["team_2"]; a contract with
key="team_2" computes the mirror. Assumes exactly two distinct keys are present in
`scores`.

    d      = self_score - opponent_score      (each contract computes its own)
    unit_class_value = signed number applied to this contract's own margin
                   0      -> pick'em / zero-line handicap
                   -2.5   -> this side must win by MORE than 2.5 to resolve YES
                   +1.5   -> this side resolves YES as long as it doesn't lose by 2+
                   -2     -> whole-number line, so PUSH is possible at d == 2

Every contract resolves one of three ways:

    mark100  -> contract resolves YES  (full payout)
    mark0    -> contract resolves NO   (total loss of stake)
    push     -> stake returned, pnl = 0 (whole-number lines only)

That's the whole model. Zero-line handicaps, spreads, and exact-differential props are
all the same function with different (unit_class_value, push_possible) inputs.

This module only covers markets where a draw is a real possible outcome of the
underlying event: zero-line/whole-number handicaps, 3-way head-to-head (see
NOTES.md), and Draw No Bet. A two-way head-to-head market where a draw *can't*
happen (e.g. tennis, basketball) has nothing to compute a differential against --
it's a Participant market, see multi_runner.py, not a special case of a handicap
here. A backable draw leg is a special case of an exact-differential prop with
d = 0 -- distinct from push_possible, which is stake-back on a tied whole-number
line, not a resolvable outcome in its own right.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from typing import Dict, Iterator, List, Tuple
import math
import uuid


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

class Mark(Enum):
    MARK100 = auto()   # contract resolves YES
    MARK0 = auto()      # contract resolves NO
    PUSH = auto()        # stake returned, pnl = 0


class UnitClass(Enum):
    """Mirrors Rust's PmUnitClass -- kept here for parity, not consumed by settlement()."""
    BINARY = auto()
    HANDICAP_MARGIN = auto()
    PARTICIPANT = auto()
    TOTAL = auto()


class Comparator(Enum):
    """How a contract's own resolving value relates to unit_class_value.
    GREATER_THAN/LESS_THAN carry an ordinary win/loss/push boundary; EQUAL_TO is a
    plain backable outcome (a draw leg, an exact-differential prop) -- it never
    pushes, there's no boundary to arbitrate, equality *is* the whole condition."""
    GREATER_THAN = auto()
    LESS_THAN = auto()
    EQUAL_TO = auto()


@dataclass
class Contract:
    unit_class_value: str  # the value which the differential is compared against to determine if the contract resolves YES or NO
    price: Decimal          # avg price paid, as a probability in [0, 1]
    position: Decimal       # signed position size: positive = long, negative = short
    push_possible: bool     # True for two-way head-to-head markets where a draw refunds the stake. (sport specific)
                            # False when a draw is its own backable outcome (see module docstring).
                            # True for whole-number spreads (tie = stake back).
                            # Ignored when comparator is EQUAL_TO -- see Comparator.
    id: uuid.UUID = field(default_factory=uuid.uuid4)  # mirrors PmContract.id; not used by settlement()
    key: str = ""           # mirrors PmContract.key -- the subject (e.g. team) this contract is about
    name: str = ""          # mirrors PmContract.name, e.g. "Home -1.5"
    alias: str = ""         # mirrors PmContract.alias, e.g. "h-1.5"
    unit_class: UnitClass = UnitClass.HANDICAP_MARGIN  # mirrors PmContract.unit_class
    comparator: Comparator = Comparator.GREATER_THAN  # LESS_THAN is never needed here --
                                                        # self-describing `key` already gives
                                                        # the mirrored side its own GREATER_THAN.

    def payout(self, mark: Mark) -> Decimal:
        """pnl = position * (outcome_value - price); position is the signed number of
        contracts held, not a dollar stake. A negative position (short) flips the sign
        of the result automatically. PUSH is always breakeven, regardless of position
        or price."""
        if mark == Mark.PUSH:
            return Decimal(0)
        if not (Decimal(0) < self.price <= Decimal(1)):
            raise ValueError(f"price must be in (0, 1], got {self.price}")
        outcome_value = Decimal(1) if mark == Mark.MARK100 else Decimal(0)
        return self.position * (outcome_value - self.price)

    def settlement(self, scores: Dict[str, int]) -> Mark:
        """Determine how this contract resolves given each team's raw score.
        Assumes exactly two keys in `scores`: this contract's own key, and the other."""
        other_key = next(k for k in scores if k != self.key)
        d = scores[self.key] - scores[other_key]
        if self.comparator == Comparator.EQUAL_TO:
            return Mark.MARK100 if d + self.unit_class_value == 0 else Mark.MARK0
        if self.push_possible and d + self.unit_class_value == 0:
            return Mark.PUSH
        elif d + self.unit_class_value > 0:
            return Mark.MARK100
        else:
            return Mark.MARK0


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def find_outcome_range(contracts: List[Contract]) -> Tuple[int, int]:
    d_min = min((c.unit_class_value for c in contracts), default=0)
    d_max = max((c.unit_class_value for c in contracts), default=0)
    lo = math.floor(d_min)
    hi = math.ceil(d_max)
    return (lo - 1 if lo == d_min else lo), (hi + 1 if hi == d_max else hi)

def build_outcome_vector(contracts: List[Contract], d_min: int, d_max: int) -> Iterator[Tuple[int, Decimal]]:
    """Walks a single 1-D range of `d` and translates each candidate value into a
    two-key scores mapping so contracts can resolve themselves via their own `key`.
    If only one key appears across `contracts`, a placeholder opponent key is used --
    no contract references it, it just fills the "other side" slot."""
    keys = sorted({c.key for c in contracts})
    if len(keys) == 0:
        return
    if len(keys) == 1:
        key_a, key_b = keys[0], f"{keys[0]}__opponent"
    elif len(keys) == 2:
        key_a, key_b = keys
    else:
        raise ValueError(f"build_outcome_vector requires at most two distinct contract keys, got {keys}")

    for i in range(d_min, d_max + 1):
        scores = {key_a: i, key_b: 0}
        pnl = sum(c.payout(c.settlement(scores)) for c in contracts)
        yield i, pnl
