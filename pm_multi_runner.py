"""
Minimal contract-state -> outcome transformation, ported from multi_runner.py
onto PmContract/PmContractState. No error handling or typing -- just the mechanics.
"""

from mark import Mark


def payout(state, mark):
    outcome_value = 1 if mark == Mark.MARK100 else 0
    return state.position * (outcome_value - state.avg_price)


def settlement(state, winner):
    return Mark.MARK100 if winner == state.contract.participant else Mark.MARK0


def possible_outcomes(contract_states):
    return sorted({s.contract.participant for s in contract_states})


def build_outcome_vector(contract_states, outcomes):
    for winner in outcomes:
        pnl = sum(payout(s, settlement(s, winner)) for s in contract_states)
        yield winner, pnl
