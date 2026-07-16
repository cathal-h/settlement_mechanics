"""
Runnable example: the fg_hc contracts from `example_contracts`, wrapped as
PmContractState so settlement mechanics can be tried against them directly.

    python3 example_pm_contract.py
"""

from decimal import Decimal

from pm_contract import PmContract, PmContractState, PmSettlementMechanic

FIXTURE_ID = "20260715021E93D8"
MARKET_ID = "20260715021E93D8_fg_hc"

contract_states = [
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_2.5",
            participant="argentina",
            name="Argentina +2.5",
            unit_class_value=Decimal("2.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_2.5",
            participant="england",
            name="England +2.5",
            unit_class_value=Decimal("2.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_1.5",
            participant="england",
            name="England +1.5",
            unit_class_value=Decimal("1.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_-1.5",
            participant="england",
            name="England -1.5",
            unit_class_value=Decimal("-1.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_-2.5",
            participant="argentina",
            name="Argentina -2.5",
            unit_class_value=Decimal("-2.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_-1.5",
            participant="argentina",
            name="Argentina -1.5",
            unit_class_value=Decimal("-1.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_-2.5",
            participant="england",
            name="England -2.5",
            unit_class_value=Decimal("-2.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_1.5",
            participant="argentina",
            name="Argentina +1.5",
            unit_class_value=Decimal("1.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_england",
            participant="england",
            name="England",
            unit_class_value=Decimal("-0.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_argentina",
            participant="argentina",
            name="Argentina",
            unit_class_value=Decimal("-0.5"),
            settlement_mechanic=PmSettlementMechanic.GREATER_THAN,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
    PmContractState(
        contract=PmContract(
            fixture_id=FIXTURE_ID,
            market_id=MARKET_ID,
            id=f"{MARKET_ID}_draw",
            participant=None,
            name="Draw",
            unit_class_value="draw",
            settlement_mechanic=PmSettlementMechanic.EXACT,
        ),
        position=Decimal(10),
        avg_price=Decimal("0.50"),
        ref_price=Decimal("0.50"),
    ),
]

if __name__ == "__main__":
    for state in contract_states:
        print(state)
