import importlib.util
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "settlement", Path(__file__).parent.parent / "score_differential.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

Contract, Mark = m.Contract, m.Mark
find_outcome_range = m.find_outcome_range
build_outcome_vector = m.build_outcome_vector


def mk(unit, price=Decimal("0.5"), stake=Decimal(100), push_possible=False):
    return Contract(unit=unit, price=price, stake=stake, push_possible=push_possible)


# --- settlement ---

def test_settlement_mark100_when_d_plus_unit_positive():
    assert mk(unit=0).settlement(1) == Mark.MARK100


def test_settlement_mark0_when_d_plus_unit_negative():
    assert mk(unit=0).settlement(-1) == Mark.MARK0


def test_settlement_mark0_at_zero_without_push():
    assert mk(unit=0, push_possible=False).settlement(0) == Mark.MARK0


def test_settlement_push_at_zero_when_push_possible():
    assert mk(unit=0, push_possible=True).settlement(0) == Mark.PUSH


def test_settlement_half_point_line_never_pushes():
    c = mk(unit=-2.5, push_possible=True)
    assert c.settlement(2) == Mark.MARK0
    assert c.settlement(3) == Mark.MARK100


# --- payouts ---

def test_payout_if_mark100_is_net_pnl():
    c = mk(unit=0, price=Decimal("0.5"), stake=Decimal(100))
    assert c.payout_if_mark100() == Decimal(100)


def test_payout_if_mark0_is_full_stake_loss():
    c = mk(unit=0, stake=Decimal(100))
    assert c.payout_if_mark0() == Decimal(-100)


def test_payout_if_push_is_zero():
    assert mk(unit=0).payout_if_push() == Decimal(0)


# --- aggregation ---

def test_find_outcome_range_pads_by_one_when_bounds_are_integers():
    contracts = [mk(unit=-2), mk(unit=2)]
    assert find_outcome_range(contracts) == (-3, 3)


def test_find_outcome_range_no_pad_when_bounds_non_integer():
    contracts = [mk(unit=-2.5), mk(unit=2.5)]
    assert find_outcome_range(contracts) == (-3, 3)


def test_build_outcome_vector_single_moneyline():
    # unit=0, no push: resolves MARK100 for d>0, MARK0 for d<=0
    c = mk(unit=0, price=Decimal("0.5"), stake=Decimal(100), push_possible=False)
    vec = dict(build_outcome_vector([c], -1, 1))
    assert vec == {-1: Decimal(-100), 0: Decimal(-100), 1: Decimal(100)}


def test_build_outcome_vector_whole_number_handicap_with_push():
    c = mk(unit=-2, price=Decimal("0.5"), stake=Decimal(100), push_possible=True)
    vec = dict(build_outcome_vector([c], 1, 3))
    assert vec[1] == Decimal(-100)   # d=1: 1-2=-1 -> MARK0
    assert vec[2] == Decimal(0)      # d=2: push
    assert vec[3] == Decimal(100)    # d=3: 1 -> MARK100


def test_build_outcome_vector_hedged_multi_contract_position():
    # moneyline home (unit=0.5, no push), away +2.5 spread (unit=2.5), and a
    # whole-number home -1 handicap that can push at d=1.
    home_handicap = mk(unit=-1, price=Decimal("0.5"), stake=Decimal(50), push_possible=True)
    moneyline = mk(unit=-0.5, price=Decimal("0.45"), stake=Decimal(45), push_possible=False)
    away_spread = mk(unit=Decimal("2.5"), price=Decimal("0.65"), stake=Decimal(65), push_possible=False)
    contracts = [moneyline, away_spread, home_handicap]

    assert find_outcome_range(contracts) == (-2, 3)

    vec = dict(build_outcome_vector(contracts, -3, 3))
    assert vec == {
        -3: Decimal(-160), # Away wins by 3+. |-1 Spread NO: -50| ML NO: -45| +2.5 Spread NO: -65|
        -2: Decimal(-60),  # Away wins by 2.  |-1 Spread NO: -50| ML NO: -45| +2.5 Spread YES: +35|
        -1: Decimal(-60),  # Away wins by 1.  |-1 Spread NO: -50| ML NO: -45| +2.5 Spread YES: +35|
        0: Decimal(-60),   # Draw.            |-1 Spread NO: -50| ML NO: -45| +2.5 Spread YES: +35|
        1: Decimal(90),    # Home wins by 1.  |-1 Spread PUSH: 0| ML YES: +55| +2.5 Spread YES: +35|
        2: Decimal(140),   # Home wins by 2.  |-1 Spread YES: +50| ML YES: +55| +2.5 Spread YES: +35|
        3: Decimal(140),   # Home wins by 3.  |-1 Spread YES: +50| ML YES: +55| +2.5 Spread YES: +35|
    }
