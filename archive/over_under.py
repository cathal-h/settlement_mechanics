"""
Prototype: over/under (totals) settlement.

Simpler sibling of score_differential.py: instead of comparing a signed
line against a score differential, the total score is compared directly
against the line.

    score       = the final total being settled against
    unit        = the total line (e.g. 220.5, or 221 for a push-eligible whole number)
    comparator  = GREATER_THAN (Over), LESS_THAN (Under), or EQUAL_TO (exact total --
                  a genuine backable outcome, e.g. "exactly 201 points", never pushes)

Over resolves YES when score > unit, NO when score < unit.
Under resolves YES when score < unit, NO when score > unit.
Push (whole-number lines only) when score == unit -- GREATER_THAN/LESS_THAN only.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterator, List, Tuple
import math
import uuid

from score_differential import Comparator, Mark, UnitClass


@dataclass
class Contract:
    unit_class_value: str  # the total line the score is compared against
    price: Decimal  # avg price paid, as a probability in [0, 1]
    position: Decimal  # signed position size: positive = long, negative = short
    push_possible: bool  # True for whole-number lines (tie = stake back); ignored when comparator is EQUAL_TO
    comparator: Comparator  # GREATER_THAN (Over), LESS_THAN (Under), or EQUAL_TO (exact total)
    id: uuid.UUID = field(default_factory=uuid.uuid4)  # mirrors PmContract.id; not used by settlement()
    key: str = ""           # mirrors PmContract.key -- the subject this contract is about
    name: str = ""          # mirrors PmContract.name, e.g. "Over 220.5"
    alias: str = ""         # mirrors PmContract.alias, e.g. "o220.5"
    unit_class: UnitClass = UnitClass.TOTAL  # mirrors PmContract.unit_class

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

    def settlement(self, score: int) -> Mark:
        """Determine how this contract resolves given the final score."""
        if self.comparator == Comparator.EQUAL_TO:
            return Mark.MARK100 if score == self.unit_class_value else Mark.MARK0
        if self.push_possible and score == self.unit_class_value:
            return Mark.PUSH
        resolves_yes = score > self.unit_class_value if self.comparator == Comparator.GREATER_THAN else score < self.unit_class_value
        return Mark.MARK100 if resolves_yes else Mark.MARK0


def find_outcome_range(contracts: List[Contract]) -> Tuple[int, int]:
    lo = min((c.unit_class_value for c in contracts), default=0)
    hi = max((c.unit_class_value for c in contracts), default=0)
    return math.floor(lo) - 1, math.ceil(hi) + 1


def build_outcome_vector(contracts: List[Contract], lo: int, hi: int) -> Iterator[Tuple[int, Decimal]]:
    for score in range(lo, hi + 1):
        pnl = sum(c.payout(c.settlement(score)) for c in contracts)
        yield score, pnl
