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


def mk(unit, price=Decimal("0.5"), stake=Decimal(100)):
    return Contract(unit=unit, price=price, stake=stake)


# --- settlement ---

def test_settlement_mark100_when_winner_matches_unit():
    assert mk(unit="Lions").settlement("Lions") == Mark.MARK100


def test_settlement_mark0_when_winner_differs():
    assert mk(unit="Lions").settlement("Tigers") == Mark.MARK0


# --- payouts ---

def test_payout_if_mark100_is_net_pnl():
    c = mk(unit="Lions", price=Decimal("0.5"), stake=Decimal(100))
    assert c.payout_if_mark100() == Decimal(100)


def test_payout_if_mark0_is_full_stake_loss():
    c = mk(unit="Lions", stake=Decimal(100))
    assert c.payout_if_mark0() == Decimal(-100)


def test_payout_if_mark100_rejects_price_out_of_range():
    c = mk(unit="Lions", price=Decimal("0"))
    try:
        c.payout_if_mark100()
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- aggregation ---

def test_possible_outcomes_is_sorted_unique_units():
    contracts = [mk(unit="Tigers"), mk(unit="Lions"), mk(unit="Lions")]
    assert possible_outcomes(contracts) == ["Lions", "Tigers"]


def test_build_outcome_vector_single_contract():
    c = mk(unit="Lions", price=Decimal("0.5"), stake=Decimal(100))
    vec = dict(build_outcome_vector([c], ["Lions", "Tigers"]))
    assert vec == {"Lions": Decimal(100), "Tigers": Decimal(-100)}


def test_build_outcome_vector_multi_contract_position():
    lions = mk(unit="Lions", price=Decimal("0.5"), stake=Decimal(50))
    tigers = mk(unit="Tigers", price=Decimal("0.25"), stake=Decimal(25))
    bears = mk(unit="Bears", price=Decimal("0.25"), stake=Decimal(30))
    contracts = [lions, tigers, bears]

    outcomes = possible_outcomes(contracts)
    assert outcomes == ["Bears", "Lions", "Tigers"]

    vec = dict(build_outcome_vector(contracts, outcomes))
    assert vec == {
        "Bears": Decimal(15),    # Bears YES: +90 | Lions NO: -50 | Tigers NO: -25
        "Lions": Decimal(-5),    # Bears NO: -30 | Lions YES: +50 | Tigers NO: -25
        "Tigers": Decimal(-5),   # Bears NO: -30 | Lions NO: -50 | Tigers YES: +75
    }
