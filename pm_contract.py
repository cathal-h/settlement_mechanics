"""
Simplest Python mirror of the real Rust mapping-service output (see
`example_contracts`) -- just the shapes, no settlement logic. That comes next,
as functions from `PmContractState` to a derived outcome state.

`PmContract` here matches what the mapping service actually emits, which has
moved on from the older shape in rust_implementation/contract.rs:

    - `participant: Optional[str]` replaces `key: str` -- `None` for contracts
      with no side (e.g. the draw leg).
    - `unit_class_value` is a tagged union in Rust (`Number(f64)` /
      `String(String)`) -- a plain `Decimal | str` here, since Python doesn't
      need the tag to dispatch on type.

`settlement_mechanic` now carries the comparator AND push behavior directly --
GREATER_THAN/LESS_THAN vs GREATER_THAN_OR_PUSH/LESS_THAN_OR_PUSH -- so there's
no separate `comparator` or `push_possible` field. The mapping stage is
expected to assign the correct mechanic per contract (e.g. a whole-number
handicap leg gets GREATER_THAN_OR_PUSH, a half-point line gets GREATER_THAN).
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import Optional, Union


class PmSettlementMechanic(Enum):
    GREATER_THAN = auto()           # resolves YES when the resolving value > unit_class_value
    LESS_THAN = auto()              # resolves YES when the resolving value < unit_class_value
    GREATER_THAN_OR_PUSH = auto()   # as GREATER_THAN, but a tie at unit_class_value pushes
    LESS_THAN_OR_PUSH = auto()      # as LESS_THAN, but a tie at unit_class_value pushes
    EXACT = auto()                  # resolving value == unit_class_value is the win condition, never pushes
    RANK = auto()                   # resolves on name match against the actual winner (outright winner markets)


UnitClassValue = Union[Decimal, str]  # Number(2.5) or String("draw") from the Rust side


@dataclass
class PmContract:
    fixture_id: str
    market_id: str
    id: str
    name: str
    unit_class_value: UnitClassValue
    settlement_mechanic: PmSettlementMechanic
    participant: Optional[str] = None


@dataclass
class PmContractState:
    contract: PmContract
    position: Decimal
    avg_price: Decimal
    ref_price: Decimal
