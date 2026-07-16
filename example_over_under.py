"""
python3 example_over_under.py
"""

from decimal import Decimal

from pm_contract import PmContract, PmContractState, PmSettlementMechanic
from pm_over_under import find_outcome_range, build_outcome_vector, payout, settlement

FIXTURE_ID = "f1"
MARKET_ID = "f1_tot"

contract_states = [
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "tot_o2.5", "Over 2.5", Decimal("2.5"), PmSettlementMechanic.GREATER_THAN),
        position=Decimal(10),
        avg_price=Decimal("0.60"),
        ref_price=Decimal("0.60"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "tot_u2.5", "Under 2.5", Decimal("2.5"), PmSettlementMechanic.LESS_THAN),
        position=Decimal(5),
        avg_price=Decimal("0.40"),
        ref_price=Decimal("0.40"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "tot_o1.5", "Over 1.5", Decimal("1.5"), PmSettlementMechanic.GREATER_THAN),
        position=Decimal(-10),
        avg_price=Decimal("0.80"),
        ref_price=Decimal("0.80"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "tot_u1.5", "Under 1.5", Decimal("1.5"), PmSettlementMechanic.LESS_THAN),
        position=Decimal(200),
        avg_price=Decimal("0.20"),
        ref_price=Decimal("0.20"),
    ),
]

if __name__ == "__main__":
    lo, hi = find_outcome_range(contract_states)
    for score, pnl in build_outcome_vector(contract_states, lo, hi):
        print(score, pnl)
        for state in contract_states:
            mark = settlement(state, score)
            print("   ", state.contract.name, mark, payout(state, mark))
