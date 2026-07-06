import importlib.util
from decimal import Decimal
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "settlement", Path(__file__).parent.parent / "score_differential.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

Contract, Mark = m.Contract, m.Mark
Comparator = m.Comparator
find_outcome_range = m.find_outcome_range
build_outcome_vector = m.build_outcome_vector


def mk(unit, price=Decimal("0.4"), stake=Decimal(100), push_possible=False, key="team_1", comparator=Comparator.GREATER_THAN):
    return Contract(unit_class_value=Decimal(str(unit)), price=price, position=stake, push_possible=push_possible, key=key, comparator=comparator)


def scores(own, other, key="team_1", opponent="team_2"):
    """A two-team raw score mapping where own - other == d for `key`."""
    return {key: own, opponent: other}


# --- settlement ---

def test_settlement_mark100_when_d_plus_unit_positive():
    assert mk(unit=0).settlement(scores(1, 0)) == Mark.MARK100


def test_settlement_mark0_when_d_plus_unit_negative():
    assert mk(unit=0).settlement(scores(0, 1)) == Mark.MARK0


def test_settlement_mark0_at_zero_without_push():
    assert mk(unit=0, push_possible=False).settlement(scores(0, 0)) == Mark.MARK0


def test_settlement_push_at_zero_when_push_possible():
    assert mk(unit=0, push_possible=True).settlement(scores(0, 0)) == Mark.PUSH


def test_settlement_half_point_line_never_pushes():
    c = mk(unit=-2.5, push_possible=True)
    assert c.settlement(scores(0, 2)) == Mark.MARK0
    assert c.settlement(scores(3, 0)) == Mark.MARK100


def test_settlement_uses_own_key_not_a_canonical_side():
    # Same underlying game (team_1 wins by 1); each contract resolves from its own key,
    # not from a shared home/away-style convention.
    game = scores(1, 0)  # team_1: 1, team_2: 0
    assert mk(unit=0, key="team_1").settlement(game) == Mark.MARK100
    assert mk(unit=0, key="team_2").settlement(game) == Mark.MARK0


def test_settlement_equal_to_resolves_yes_only_on_exact_match():
    # A draw leg: backable outcome, not a push. push_possible is irrelevant here.
    c = mk(unit=0, key="team_1", comparator=Comparator.EQUAL_TO, push_possible=True)
    assert c.settlement(scores(1, 0)) == Mark.MARK0
    assert c.settlement(scores(0, 0)) == Mark.MARK100
    assert c.settlement(scores(0, 1)) == Mark.MARK0


# --- payouts ---

def test_payout_if_mark100_is_net_pnl():
    c = mk(unit=0, price=Decimal("0.4"), stake=Decimal(100))
    assert c.payout(Mark.MARK100) == Decimal(60)


def test_payout_if_mark0_is_full_cost_basis_loss():
    c = mk(unit=0, price=Decimal("0.4"), stake=Decimal(100))
    assert c.payout(Mark.MARK0) == Decimal(-40)


def test_payout_if_push_is_zero():
    assert mk(unit=0).payout(Mark.PUSH) == Decimal(0)


# --- aggregation ---

def test_find_outcome_range_pads_by_one_when_bounds_are_integers():
    contracts = [mk(unit=-2), mk(unit=2)]
    assert find_outcome_range(contracts) == (-3, 3)


def test_find_outcome_range_no_pad_when_bounds_non_integer():
    contracts = [mk(unit=-2.5), mk(unit=2.5)]
    assert find_outcome_range(contracts) == (-3, 3)


def test_build_outcome_vector_single_contract():
    # unit=0, no push: resolves MARK100 for d>0, MARK0 for d<=0.
    # Only one key is in play -- build_outcome_vector synthesizes a placeholder opponent.
    c = mk(unit=0, price=Decimal("0.4"), stake=Decimal(100), push_possible=False)
    vec = dict(build_outcome_vector([c], -1, 1))
    assert vec == {-1: Decimal(-40), 0: Decimal(-40), 1: Decimal(60)}


def test_build_outcome_vector_whole_number_handicap_with_push():
    c = mk(unit=-2, price=Decimal("0.4"), stake=Decimal(100), push_possible=True)
    vec = dict(build_outcome_vector([c], 1, 3))
    assert vec[1] == Decimal(-40)    # d=1: 1-2=-1 -> MARK0
    assert vec[2] == Decimal(0)      # d=2: push
    assert vec[3] == Decimal(60)     # d=3: 1 -> MARK100


def test_build_outcome_vector_hedged_multi_contract_position():
    # team_1 -1 whole-number handicap (push at d=1), team_1 -0.5 zero-line handicap
    # (no push), and team_2's own +2.5 spread -- computed off team_2's own key, not
    # team_1's d mirrored by hand.
    home_handicap = mk(unit=-1, price=Decimal("0.4"), stake=Decimal(50), push_possible=True, key="team_1")
    zero_line = mk(unit=-0.5, price=Decimal("0.45"), stake=Decimal(45), push_possible=False, key="team_1")
    away_spread = mk(unit=2.5, price=Decimal("0.65"), stake=Decimal(65), push_possible=False, key="team_2")
    contracts = [zero_line, away_spread, home_handicap]

    assert find_outcome_range(contracts) == (-2, 3)

    # d is team_1 - team_2. Per-leg payouts: home_handicap (price .4, stake 50) ->
    # YES +30 / NO -20; zero_line (price .45, stake 45) -> YES +24.75 / NO -20.25;
    # away_spread (price .65, stake 65) -> YES +22.75 / NO -42.25.
    vec = dict(build_outcome_vector(contracts, -3, 3))
    assert vec == {
        -3: Decimal("-17.5"),  # team_2 wins by 3. -1 HC NO | 0-line NO | team_2 +2.5 YES
        -2: Decimal("-17.5"),  # team_2 wins by 2. -1 HC NO | 0-line NO | team_2 +2.5 YES
        -1: Decimal("-17.5"),  # team_2 wins by 1. -1 HC NO | 0-line NO | team_2 +2.5 YES
        0: Decimal("-17.5"),   # Draw.             -1 HC NO | 0-line NO | team_2 +2.5 YES
        1: Decimal("47.5"),    # team_1 wins by 1. -1 HC PUSH: 0 | 0-line YES | team_2 +2.5 YES
        2: Decimal("77.5"),    # team_1 wins by 2. -1 HC YES | 0-line YES | team_2 +2.5 YES
        3: Decimal("12.5"),    # team_1 wins by 3. -1 HC YES | 0-line YES | team_2 +2.5 NO
    }


def test_three_way_head_to_head_maps_onto_diff():
    # A 3-way market (e.g. France/Draw/Morocco) is NOT a multi-runner/Participant
    # market -- all three legs settle off one shared d = team_1 - team_2. The draw
    # leg uses EQUAL_TO: it's a genuine backable outcome, not a push (push_possible
    # stays False -- see NOTES.md #2/#4). The draw leg's `key` can be either team's,
    # since d==0 is symmetric regardless of whose perspective computes it.
    team_1_win = mk(unit=0, price=Decimal("0.40"), stake=Decimal(40), key="team_1")
    draw = mk(unit=0, price=Decimal("0.30"), stake=Decimal(30), key="team_1", comparator=Comparator.EQUAL_TO)
    team_2_win = mk(unit=0, price=Decimal("0.35"), stake=Decimal(35), key="team_2")
    contracts = [team_1_win, draw, team_2_win]

    vec = dict(build_outcome_vector(contracts, -2, 2))
    # Exactly one of the three legs pays YES per outcome; the other two pay NO.
    # Per-leg payouts: team_1_win (price .40, stake 40) -> YES +24 / NO -16;
    # draw (price .30, stake 30) -> YES +21 / NO -9; team_2_win (price .35, stake 35)
    # -> YES +22.75 / NO -12.25. A sanity check that all three resolve correctly
    # across the whole range, not just at the boundary.
    assert vec == {
        -2: Decimal("-2.25"),  # team_2 wins by 2. team_1 NO | draw NO | team_2 YES
        -1: Decimal("-2.25"),  # team_2 wins by 1. team_1 NO | draw NO | team_2 YES
        0: Decimal("-7.25"),   # draw.             team_1 NO | draw YES | team_2 NO
        1: Decimal("2.75"),    # team_1 wins by 1. team_1 YES | draw NO | team_2 NO
        2: Decimal("2.75"),    # team_1 wins by 2. team_1 YES | draw NO | team_2 NO
    }
