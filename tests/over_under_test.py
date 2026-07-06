import importlib.util
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "over_under", Path(__file__).parent.parent / "over_under.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

Contract, Mark = m.Contract, m.Mark
find_outcome_range = m.find_outcome_range
build_outcome_vector = m.build_outcome_vector


def mk(unit, over, price=Decimal("0.5"), stake=Decimal(100), push_possible=False):
    return Contract(unit=unit, price=price, stake=stake, push_possible=push_possible, over=over)


# --- settlement ---

def test_over_resolves_mark100_when_score_above_unit():
    assert mk(unit=220.5, over=True).settlement(221) == Mark.MARK100


def test_over_resolves_mark0_when_score_below_unit():
    assert mk(unit=220.5, over=True).settlement(220) == Mark.MARK0


def test_under_resolves_mark100_when_score_below_unit():
    assert mk(unit=220.5, over=False).settlement(220) == Mark.MARK100


def test_under_resolves_mark0_when_score_above_unit():
    assert mk(unit=220.5, over=False).settlement(221) == Mark.MARK0


def test_settlement_mark0_at_unit_without_push():
    assert mk(unit=220, over=True, push_possible=False).settlement(220) == Mark.MARK0


def test_settlement_push_at_unit_when_push_possible():
    assert mk(unit=220, over=True, push_possible=True).settlement(220) == Mark.PUSH


def test_settlement_half_point_line_never_pushes():
    c = mk(unit=220.5, over=True, push_possible=True)
    assert c.settlement(220) == Mark.MARK0
    assert c.settlement(221) == Mark.MARK100


# --- payouts ---

def test_payout_if_mark100_is_net_pnl():
    c = mk(unit=220, over=True, price=Decimal("0.5"), stake=Decimal(100))
    assert c.payout_if_mark100() == Decimal(100)


def test_payout_if_mark0_is_full_stake_loss():
    c = mk(unit=220, over=True, stake=Decimal(100))
    assert c.payout_if_mark0() == Decimal(-100)


def test_payout_if_push_is_zero():
    assert mk(unit=220, over=True).payout_if_push() == Decimal(0)


def test_payout_if_mark100_rejects_price_out_of_range():
    c = mk(unit=220, over=True, price=Decimal("0"))
    try:
        c.payout_if_mark100()
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- aggregation ---

def test_find_outcome_range_pads_by_one_on_each_side():
    contracts = [mk(unit=218, over=True), mk(unit=222, over=False)]
    assert find_outcome_range(contracts) == (217, 223)


def test_build_outcome_vector_single_over():
    c = mk(unit=220.5, over=True, price=Decimal("0.5"), stake=Decimal(100))
    vec = dict(build_outcome_vector([c], 219, 221))
    assert vec == {219: Decimal(-100), 220: Decimal(-100), 221: Decimal(100)}


def test_build_outcome_vector_whole_number_line_with_push():
    c = mk(unit=220, over=True, price=Decimal("0.5"), stake=Decimal(100), push_possible=True)
    vec = dict(build_outcome_vector([c], 219, 221))
    assert vec[219] == Decimal(-100)  # under the line -> MARK0
    assert vec[220] == Decimal(0)     # exactly the line -> PUSH
    assert vec[221] == Decimal(100)   # over the line -> MARK100


def test_build_outcome_vector_hedged_over_and_under():
    # Over 220.5 and Under 222.5 both staked -- overlapping middle band pays both.
    over = mk(unit=220.5, over=True, price=Decimal("0.5"), stake=Decimal(50))
    under = mk(unit=222.5, over=False, price=Decimal("0.5"), stake=Decimal(50))
    contracts = [over, under]

    assert find_outcome_range(contracts) == (219, 224)

    vec = dict(build_outcome_vector(contracts, 219, 224))
    assert vec == {
        219: Decimal(0),     # Over NO: -50 | Under YES: +50
        220: Decimal(0),     # Over NO: -50 | Under YES: +50
        221: Decimal(100),   # Over YES: +50 | Under YES: +50
        222: Decimal(100),   # Over YES: +50 | Under YES: +50
        223: Decimal(0),     # Over YES: +50 | Under NO: -50
        224: Decimal(0),     # Over YES: +50 | Under NO: -50
    }
