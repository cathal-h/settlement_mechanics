"""
Prototype: multi-runner (outright winner) settlement.

Simpler sibling of score_differential.py: there's no ordering or line here,
just a name. A contract resolves YES if the winner matches its unit.

    winner = the name of whatever actually won (equivalent of d)
    unit   = the name this contract is betting on

No push: exactly one runner wins.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterator, List, Tuple

from score_differential import Mark


@dataclass
class Contract:
    unit: str  # the name this contract resolves YES for
    price: Decimal  # avg price paid, as a probability in [0, 1]
    stake: Decimal  # amount of money risked on this contract

    def payout_if_mark100(self) -> Decimal:
        if not (Decimal(0) < self.price <= Decimal(1)):
            raise ValueError(f"price must be in (0, 1], got {self.price}")
        return self.stake / self.price - self.stake

    def payout_if_mark0(self) -> Decimal:
        return -self.stake

    def settlement(self, winner: str) -> Mark:
        """Determine how this contract resolves given the actual winner."""
        return Mark.MARK100 if winner == self.unit else Mark.MARK0


def possible_outcomes(contracts: List[Contract]) -> List[str]:
    return sorted({c.unit for c in contracts})


def build_outcome_vector(contracts: List[Contract], outcomes: List[str]) -> Iterator[Tuple[str, Decimal]]:
    for winner in outcomes:
        pnl = sum(
            c.payout_if_mark100() if c.settlement(winner) == Mark.MARK100 else c.payout_if_mark0()
            for c in contracts
        )
        yield winner, pnl
