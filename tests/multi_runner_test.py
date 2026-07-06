import importlib.util
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "multi_runner", Path(__file__).parent.parent / "multi_runner.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

Contract, Mark = m.Contract, m.Mark
possible_outcomes = m.possible_outcomes
build_outcome_vector = m.build_outcome_vector


def mk(unit, price=Decimal("0.4"), stake=Decimal(100)):
    return Contract(unit_class_value=unit, price=price, position=stake)


# --- settlement ---

def test_settlement_mark100_when_winner_matches_unit():
    assert mk(unit="Lions").settlement("Lions") == Mark.MARK100


def test_settlement_mark0_when_winner_differs():
    assert mk(unit="Lions").settlement("Tigers") == Mark.MARK0


# --- payouts ---

def test_payout_if_mark100_is_net_pnl():
    c = mk(unit="Lions", price=Decimal("0.4"), stake=Decimal(100))
    assert c.payout(Mark.MARK100) == Decimal(60)


def test_payout_if_mark0_is_full_cost_basis_loss():
    c = mk(unit="Lions", stake=Decimal(100))
    assert c.payout(Mark.MARK0) == Decimal(-40)


def test_payout_if_mark100_rejects_price_out_of_range():
    c = mk(unit="Lions", price=Decimal("0"))
    try:
        c.payout(Mark.MARK100)
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- aggregation ---

def test_possible_outcomes_is_sorted_unique_units():
    contracts = [mk(unit="Tigers"), mk(unit="Lions"), mk(unit="Lions")]
    assert possible_outcomes(contracts) == ["Lions", "Tigers"]


def test_build_outcome_vector_single_contract():
    c = mk(unit="Lions", price=Decimal("0.4"), stake=Decimal(100))
    vec = dict(build_outcome_vector([c], ["Lions", "Tigers"]))
    assert vec == {"Lions": Decimal(60), "Tigers": Decimal(-40)}


def test_build_outcome_vector_multi_contract_position():
    lions = mk(unit="Lions", price=Decimal("0.4"), stake=Decimal(50))
    tigers = mk(unit="Tigers", price=Decimal("0.25"), stake=Decimal(25))
    bears = mk(unit="Bears", price=Decimal("0.25"), stake=Decimal(30))
    contracts = [lions, tigers, bears]

    outcomes = possible_outcomes(contracts)
    assert outcomes == ["Bears", "Lions", "Tigers"]

    vec = dict(build_outcome_vector(contracts, outcomes))
    assert vec == {
        "Bears": Decimal("-3.75"),   # Bears YES: +22.5 | Lions NO: -20 | Tigers NO: -6.25
        "Lions": Decimal("16.25"),   # Bears NO: -7.5 | Lions YES: +30 | Tigers NO: -6.25
        "Tigers": Decimal("-8.75"),  # Bears NO: -7.5 | Lions NO: -20 | Tigers YES: +18.75
    }
