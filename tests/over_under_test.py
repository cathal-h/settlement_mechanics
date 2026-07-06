import importlib.util
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "over_under", Path(__file__).parent.parent / "over_under.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

Contract, Mark = m.Contract, m.Mark
Comparator = m.Comparator
find_outcome_range = m.find_outcome_range
build_outcome_vector = m.build_outcome_vector


def mk(unit, over, price=Decimal("0.4"), stake=Decimal(100), push_possible=False):
    comparator = Comparator.GREATER_THAN if over else Comparator.LESS_THAN
    return Contract(unit_class_value=Decimal(str(unit)), price=price, position=stake, push_possible=push_possible, comparator=comparator)


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


def test_settlement_exact_total_resolves_yes_only_on_match():
    c = Contract(unit_class_value=Decimal(201), price=Decimal("0.1"), position=Decimal(10),
                 push_possible=False, comparator=Comparator.EQUAL_TO)
    assert c.settlement(200) == Mark.MARK0
    assert c.settlement(201) == Mark.MARK100
    assert c.settlement(202) == Mark.MARK0


def test_settlement_exact_total_never_pushes_even_if_flagged():
    # EQUAL_TO ignores push_possible entirely -- there's no boundary to arbitrate.
    c = Contract(unit_class_value=Decimal(201), price=Decimal("0.1"), position=Decimal(10),
                 push_possible=True, comparator=Comparator.EQUAL_TO)
    assert c.settlement(201) == Mark.MARK100


# --- payouts ---

def test_payout_if_mark100_is_net_pnl():
    c = mk(unit=220, over=True, price=Decimal("0.4"), stake=Decimal(100))
    assert c.payout(Mark.MARK100) == Decimal(60)


def test_payout_if_mark0_is_full_cost_basis_loss():
    c = mk(unit=220, over=True, stake=Decimal(100))
    assert c.payout(Mark.MARK0) == Decimal(-40)


def test_payout_if_push_is_zero():
    assert mk(unit=220, over=True).payout(Mark.PUSH) == Decimal(0)


def test_payout_if_mark100_rejects_price_out_of_range():
    c = mk(unit=220, over=True, price=Decimal("0"))
    try:
        c.payout(Mark.MARK100)
        assert False, "expected ValueError"
    except ValueError:
        pass


# --- aggregation ---

def test_find_outcome_range_pads_by_one_on_each_side():
    contracts = [mk(unit=218, over=True), mk(unit=222, over=False)]
    assert find_outcome_range(contracts) == (217, 223)


def test_build_outcome_vector_single_over():
    c = mk(unit=220.5, over=True, price=Decimal("0.4"), stake=Decimal(100))
    vec = dict(build_outcome_vector([c], 219, 221))
    assert vec == {219: Decimal(-40), 220: Decimal(-40), 221: Decimal(60)}


def test_build_outcome_vector_whole_number_line_with_push():
    c = mk(unit=220, over=True, price=Decimal("0.4"), stake=Decimal(100), push_possible=True)
    vec = dict(build_outcome_vector([c], 219, 221))
    assert vec[219] == Decimal(-40)   # under the line -> MARK0
    assert vec[220] == Decimal(0)     # exactly the line -> PUSH
    assert vec[221] == Decimal(60)    # over the line -> MARK100


def test_build_outcome_vector_hedged_over_and_under():
    # Over 220.5 and Under 222.5 both staked -- overlapping middle band pays both.
    over = mk(unit=220.5, over=True, price=Decimal("0.4"), stake=Decimal(50))
    under = mk(unit=222.5, over=False, price=Decimal("0.4"), stake=Decimal(50))
    contracts = [over, under]

    assert find_outcome_range(contracts) == (219, 224)

    vec = dict(build_outcome_vector(contracts, 219, 224))
    assert vec == {
        219: Decimal(10),   # Over NO: -20 | Under YES: +30
        220: Decimal(10),   # Over NO: -20 | Under YES: +30
        221: Decimal(60),   # Over YES: +30 | Under YES: +30
        222: Decimal(60),   # Over YES: +30 | Under YES: +30
        223: Decimal(10),   # Over YES: +30 | Under NO: -20
        224: Decimal(10),   # Over YES: +30 | Under NO: -20
    }


def test_build_outcome_vector_over_under_and_exact_total():
    # Over 200.5, Under 200.5, and Exact 201 -- Exact only ever coexists with the
    # ordinary Over/Under pair around it, it doesn't replace them.
    over = mk(unit=200.5, over=True, price=Decimal("0.45"), stake=Decimal(45))
    under = mk(unit=200.5, over=False, price=Decimal("0.45"), stake=Decimal(45))
    exact = Contract(unit_class_value=Decimal(201), price=Decimal("0.1"), position=Decimal(10),
                     push_possible=False, comparator=Comparator.EQUAL_TO)
    contracts = [over, under, exact]

    vec = dict(build_outcome_vector(contracts, 200, 202))
    assert vec == {
        200: Decimal("3.5"),   # Under YES: +24.75 | Over NO: -20.25 | Exact NO: -1
        201: Decimal("13.5"),  # Over YES: +24.75 | Under NO: -20.25 | Exact YES: +9
        202: Decimal("3.5"),   # Over YES: +24.75 | Under NO: -20.25 | Exact NO: -1
    }
