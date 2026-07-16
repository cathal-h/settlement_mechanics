"""
Minimal contract-state -> outcome transformation for over/under (totals)
markets. No error handling or typing -- just the mechanics.
"""

import math

from pm_contract import PmSettlementMechanic
from mark import Mark


def payout(state, mark):
    if mark == Mark.PUSH:
        return 0
    outcome_value = 1 if mark == Mark.MARK100 else 0
    return state.position * (outcome_value - state.avg_price)


def settlement(state, score):
    contract = state.contract
    value = contract.unit_class_value
    mechanic = contract.settlement_mechanic

    if mechanic == PmSettlementMechanic.EXACT:
        return Mark.MARK100 if score == value else Mark.MARK0
    if mechanic in (PmSettlementMechanic.GREATER_THAN_OR_PUSH, PmSettlementMechanic.LESS_THAN_OR_PUSH) and score == value:
        return Mark.PUSH
    if mechanic in (PmSettlementMechanic.GREATER_THAN, PmSettlementMechanic.GREATER_THAN_OR_PUSH):
        return Mark.MARK100 if score > value else Mark.MARK0
    else:
        return Mark.MARK100 if score < value else Mark.MARK0


def find_outcome_range(contract_states):
    values = [s.contract.unit_class_value for s in contract_states]
    d_min = min(values)
    d_max = max(values)
    lo = math.floor(d_min)
    hi = math.ceil(d_max)
    return (lo - 1 if lo == d_min else lo), (hi + 1 if hi == d_max else hi)


def build_outcome_vector(contract_states, lo, hi):
    for score in range(lo, hi + 1):
        pnl = sum(payout(s, settlement(s, score)) for s in contract_states)
        yield score, pnl
