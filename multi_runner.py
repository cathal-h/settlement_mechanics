"""
Prototype: multi-runner (outright winner) settlement.

Simpler sibling of score_differential.py: there's no ordering or line here,
just a name. A contract resolves YES if the winner matches its unit.

    winner = the name of whatever actually won (equivalent of d)
    unit   = the name this contract is betting on

No push: exactly one runner wins.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterator, List, Tuple
import uuid

from score_differential import Mark, UnitClass


@dataclass
class Contract:
    unit_class_value: str  # the name this contract resolves YES for
    price: Decimal  # avg price paid, as a probability in [0, 1]
    position: Decimal  # signed position size: positive = long, negative = short
    id: uuid.UUID = field(default_factory=uuid.uuid4)  # mirrors PmContract.id; not used by settlement()
    key: str = ""           # mirrors PmContract.key -- redundant with unit_class_value here, kept for parity
    name: str = ""          # mirrors PmContract.name, e.g. "Lions to win"
    alias: str = ""         # mirrors PmContract.alias, e.g. "lions"
    unit_class: UnitClass = UnitClass.PARTICIPANT  # mirrors PmContract.unit_class

    def payout(self, mark: Mark) -> Decimal:
        """pnl = position * (outcome_value - price); position is the signed number of
        contracts held, not a dollar stake. A negative position (short) flips the sign
        of the result automatically."""
        if not (Decimal(0) < self.price <= Decimal(1)):
            raise ValueError(f"price must be in (0, 1], got {self.price}")
        outcome_value = Decimal(1) if mark == Mark.MARK100 else Decimal(0)
        return self.position * (outcome_value - self.price)

    def settlement(self, winner: str) -> Mark:
        """Determine how this contract resolves given the actual winner."""
        return Mark.MARK100 if winner == self.unit_class_value else Mark.MARK0


def possible_outcomes(contracts: List[Contract]) -> List[str]:
    return sorted({c.unit_class_value for c in contracts})


def build_outcome_vector(contracts: List[Contract], outcomes: List[str]) -> Iterator[Tuple[str, Decimal]]:
    for winner in outcomes:
        pnl = sum(c.payout(c.settlement(winner)) for c in contracts)
        yield winner, pnl
