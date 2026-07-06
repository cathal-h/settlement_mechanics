"""
Prototype: converting individual contracts into a single
aggregated `outcome_state`.

Everything below is framed from a single side's perspective on input (e.g. Home Team):

    d          = home_score - away_score      (the one variable everything settles off)
    home_line  = signed number applied to home's margin
                   0      -> pick'em / moneyline
                   -2.5   -> home must win by MORE than 2.5 to resolve YES
                   +1.5   -> home resolves YES as long as it doesn't lose by 2+
                   -2     -> whole-number line, so PUSH is possible at d == 2

Every contract resolves one of three ways:

    mark100  -> contract resolves YES  (full payout)
    mark0    -> contract resolves NO   (total loss of stake)
    push     -> stake returned, pnl = 0 (whole-number lines only)

That's the whole model. Moneyline, spreads, and exact-differential props are
all the same function with different (home_line, resolves_yes_if, push_possible) inputs.

Moneyline is just a special case of a handicaps where home to win = -0.5 and away to win = +0.5.
The Draw Moneyline is a special case of an exact-differential prop with d = 0.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import Iterator, List, Tuple
import math


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

class Mark(Enum):
    MARK100 = auto()   # contract resolves YES
    MARK0 = auto()      # contract resolves NO
    PUSH = auto()        # stake returned, pnl = 0


@dataclass
class Contract:
    unit: str # the value which the differential is compared against to determine if the contract resolves YES or NO
    price: Decimal          # avg price paid, as a probability in [0, 1]
    stake: Decimal         # amount of money risked on this contract
    push_possible: bool     # True for two-way moneylines where a draw is possible. (sport specific)
                            # False for three-way moneylines.
                            # True for whole-number spreads (tie = stake back).

    def payout_if_mark100(self) -> Decimal:
        if not (Decimal(0) < self.price <= Decimal(1)):
            raise ValueError(f"price must be in (0, 1], got {self.price}")
        # stake buys (stake / price) contracts, each paying $1 on mark100
        return self.stake / self.price - self.stake

    def payout_if_mark0(self) -> Decimal:
        return -self.stake  # total loss of stake
    
    def payout_if_push(self) -> Decimal:
        return Decimal(0)  # stake returned, pnl = 0

    def settlement(self, d: int) -> Mark:
        """Determine how this contract resolves given the final score differential d."""
        if self.push_possible and d + self.unit == 0:
            return Mark.PUSH
        elif d + self.unit > 0:
            return Mark.MARK100
        else:
            return Mark.MARK0


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def find_outcome_range(contracts: List[Contract]) -> Tuple[int, int]:
    d_min = min((c.unit for c in contracts), default=0)
    d_max = max((c.unit for c in contracts), default=0)
    lo = math.floor(d_min)
    hi = math.ceil(d_max)
    return (lo - 1 if lo == d_min else lo), (hi + 1 if hi == d_max else hi)

def build_outcome_vector(contracts: List[Contract], d_min: int, d_max: int) -> Iterator[Tuple[int, Decimal]]:
    for i in range(d_min, d_max + 1):
        pnl = sum(
            c.payout_if_mark100() if c.settlement(i) == Mark.MARK100 else
            c.payout_if_mark0() if c.settlement(i) == Mark.MARK0 else
            c.payout_if_push()
            for c in contracts
        )
        yield i, pnl
