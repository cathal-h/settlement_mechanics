"""
Minimal contract-state -> outcome transformation for score-differential
markets (handicaps, 3-way head-to-head, Draw No Bet). No error handling or
typing -- just the mechanics.
"""

import math

from pm_contract import PmSettlementMechanic
from mark import Mark


def payout(state, mark):
    if mark == Mark.PUSH:
        return 0
    outcome_value = 1 if mark == Mark.MARK100 else 0
    return state.position * (outcome_value - state.avg_price)


def settlement(state, scores):
    contract = state.contract
    other_participant = next(k for k in scores if k != contract.participant)
    d = scores[contract.participant] - scores[other_participant]
    value = contract.unit_class_value
    mechanic = contract.settlement_mechanic

    if mechanic == PmSettlementMechanic.EXACT:
        return Mark.MARK100 if d + value == 0 else Mark.MARK0
    if mechanic in (PmSettlementMechanic.GREATER_THAN_OR_PUSH, PmSettlementMechanic.LESS_THAN_OR_PUSH) and d + value == 0:
        return Mark.PUSH
    if mechanic in (PmSettlementMechanic.GREATER_THAN, PmSettlementMechanic.GREATER_THAN_OR_PUSH):
        return Mark.MARK100 if d + value > 0 else Mark.MARK0
    else:
        return Mark.MARK100 if d + value < 0 else Mark.MARK0


def find_outcome_range(contract_states):
    # settlement flips at d = -value (from d + value R 0), not at d = value
    thresholds = [-s.contract.unit_class_value for s in contract_states]
    d_min = min(thresholds)
    d_max = max(thresholds)
    lo = math.floor(d_min)
    hi = math.ceil(d_max)
    return (lo - 1 if lo == d_min else lo), (hi + 1 if hi == d_max else hi)


def build_outcome_vector(contract_states, d_min, d_max):
    participant_a, participant_b = sorted({s.contract.participant for s in contract_states})
    for i in range(d_min, d_max + 1):
        scores = {participant_a: i, participant_b: 0}
        pnl = sum(payout(s, settlement(s, scores)) for s in contract_states)
        yield i, pnl
