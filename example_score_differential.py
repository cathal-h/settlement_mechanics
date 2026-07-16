"""
python3 example_score_differential.py
"""

from decimal import Decimal

from pm_contract import PmContract, PmContractState, PmSettlementMechanic
from pm_score_differential import find_outcome_range, build_outcome_vector, payout, settlement

FIXTURE_ID = "f1"
MARKET_ID = "f1_hc"

contract_states = [
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "hc_arg_+3.5", "Argentina +3.5", Decimal("3.5"), PmSettlementMechanic.GREATER_THAN, participant="argentina"),
        position=Decimal(10),
        avg_price=Decimal("0.70"),
        ref_price=Decimal("0.70"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "hc_arg_-1.5", "Argentina -1.5", Decimal("-1.5"), PmSettlementMechanic.GREATER_THAN, participant="argentina"),
        position=Decimal(5),
        avg_price=Decimal("0.30"),
        ref_price=Decimal("0.30"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "hc_eng_+1.5", "England +1.5", Decimal("1.5"), PmSettlementMechanic.GREATER_THAN, participant="england"),
        position=Decimal(-8),
        avg_price=Decimal("0.30"),
        ref_price=Decimal("0.30"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "hc_eng_-1.5", "England -1.5", Decimal("-1.5"), PmSettlementMechanic.GREATER_THAN, participant="england"),
        position=Decimal(20),
        avg_price=Decimal("0.70"),
        ref_price=Decimal("0.70"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "hc_draw", "Draw", Decimal("0"), PmSettlementMechanic.EXACT, participant="argentina"),
        position=Decimal(15),
        avg_price=Decimal("0.25"),
        ref_price=Decimal("0.25"),
    ),
]

def describe(d):
    if d > 0:
        return f"argentina wins by {d}"
    elif d < 0:
        return f"england wins by {-d}"
    else:
        return "draw"


if __name__ == "__main__":
    participant_a, participant_b = sorted({s.contract.participant for s in contract_states})
    d_min, d_max = find_outcome_range(contract_states)
    for d, pnl in build_outcome_vector(contract_states, d_min, d_max):
        print(d, describe(d), pnl)
        scores = {participant_a: d, participant_b: 0}
        for state in contract_states:
            mark = settlement(state, scores)
            print("   ", state.contract.name, mark, payout(state, mark))
