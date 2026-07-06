"""
Prototype: over/under (totals) settlement.

Simpler sibling of score_differential.py: instead of comparing a signed
line against a score differential, the total score is compared directly
against the line.

    score  = the final total being settled against
    unit   = the total line (e.g. 220.5, or 221 for a push-eligible whole number)
    over   = True for Over contracts, False for Under

Over resolves YES when score > unit, NO when score < unit.
Under resolves YES when score < unit, NO when score > unit.
Push (whole-number lines only) when score == unit.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterator, List, Tuple
import math

from score_differential import Mark


@dataclass
class Contract:
    unit: str  # the total line the score is compared against
    price: Decimal  # avg price paid, as a probability in [0, 1]
    stake: Decimal  # amount of money risked on this contract
    push_possible: bool  # True for whole-number lines (tie = stake back)
    over: bool  # True for Over contracts, False for Under

    def payout_if_mark100(self) -> Decimal:
        if not (Decimal(0) < self.price <= Decimal(1)):
            raise ValueError(f"price must be in (0, 1], got {self.price}")
        return self.stake / self.price - self.stake

    def payout_if_mark0(self) -> Decimal:
        return -self.stake

    def payout_if_push(self) -> Decimal:
        return Decimal(0)

    def settlement(self, score: int) -> Mark:
        """Determine how this contract resolves given the final score."""
        if self.push_possible and score == self.unit:
            return Mark.PUSH
        resolves_yes = score > self.unit if self.over else score < self.unit
        return Mark.MARK100 if resolves_yes else Mark.MARK0


def find_outcome_range(contracts: List[Contract]) -> Tuple[int, int]:
    lo = min((c.unit for c in contracts), default=0)
    hi = max((c.unit for c in contracts), default=0)
    return math.floor(lo) - 1, math.ceil(hi) + 1


def build_outcome_vector(contracts: List[Contract], lo: int, hi: int) -> Iterator[Tuple[int, Decimal]]:
    for score in range(lo, hi + 1):
        pnl = sum(
            c.payout_if_mark100() if c.settlement(score) == Mark.MARK100 else
            c.payout_if_mark0() if c.settlement(score) == Mark.MARK0 else
            c.payout_if_push()
            for c in contracts
        )
        yield score, pnl
