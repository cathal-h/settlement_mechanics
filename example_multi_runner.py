"""
python3 example_multi_runner.py
"""

from decimal import Decimal

from pm_contract import PmContract, PmContractState, PmSettlementMechanic
from pm_multi_runner import possible_outcomes, build_outcome_vector, payout, settlement

FIXTURE_ID = "f1"
MARKET_ID = "f1_winner"

contract_states = [
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "win_arg", "Argentina", Decimal("0"), PmSettlementMechanic.RANK, participant="argentina"),
        position=Decimal(10),
        avg_price=Decimal("0.40"),
        ref_price=Decimal("0.40"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "win_eng", "England", Decimal("0"), PmSettlementMechanic.RANK, participant="england"),
        position=Decimal(5),
        avg_price=Decimal("0.25"),
        ref_price=Decimal("0.25"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "win_fra", "France", Decimal("0"), PmSettlementMechanic.RANK, participant="france"),
        position=Decimal(-8),
        avg_price=Decimal("0.20"),
        ref_price=Decimal("0.20"),
    ),
    PmContractState(
        contract=PmContract(FIXTURE_ID, MARKET_ID, "win_bra", "Brazil", Decimal("0"), PmSettlementMechanic.RANK, participant="brazil"),
        position=Decimal(20),
        avg_price=Decimal("0.15"),
        ref_price=Decimal("0.15"),
    ),
]

if __name__ == "__main__":
    for winner, pnl in build_outcome_vector(contract_states, possible_outcomes(contract_states)):
        print(winner, pnl)
        for state in contract_states:
            mark = settlement(state, winner)
            print("   ", state.contract.name, mark, payout(state, mark))
