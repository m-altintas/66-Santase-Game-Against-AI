"""Hand-checked full deals. Points in the comments were worked out by hand from docs/rules.md."""

from santase.engine import DealState, EndReason, cards, deal_from_order, parse_action, step

# Player 0 (non-dealer) gets AH 10H KH + QH AS 10S, player 1 gets 9C JC QC + KC 10C AC.
# Trump card JS; the talon draws 9D JD QD KD 10D AD 9H JH QS KS 9S, then JS.
ORDER = cards("AH 10H KH 9C JC QC QH AS 10S KC 10C AC JS 9D JD QD KD 10D AD 9H JH QS KS 9S")


def run(actions: list[str]) -> DealState:
    state = deal_from_order(ORDER, dealer=1)
    for text in actions:
        state = step(state, parse_action(text))
    return state


def test_close_marriage_and_declare() -> None:
    state = run(
        [
            "play:AH", "play:9C",  # 0 takes 11; draws 9D, 1 draws JD
            "close", "marriage:H",  # R5.2 order; +20 -> 31
            "play:KH", "play:JC",  # strict, void, no trump: any card; 0 takes 6 -> 37
            "play:10H", "play:QC",  # 0 takes 13 -> 50
            "play:QH", "play:KC",  # 0 takes 7 -> 57
            "play:AS", "play:10C",  # 0 takes 21 -> 78
            "out",
        ]
    )  # fmt: skip
    assert state.hands[0] == tuple(sorted(cards("10S 9D")))
    assert state.talon == cards("QD KD 10D AD 9H JH QS KS 9S JS")  # closed after one draw
    outcome = state.outcome
    assert outcome is not None
    assert outcome.card_points == (78, 0)
    assert (outcome.winner, outcome.game_points, outcome.reason) == (0, 3, EndReason.CLOSER_WON)


def test_early_wrong_declaration() -> None:
    state = run(["play:AH", "play:9C", "out"])  # 11 points is not 66
    outcome = state.outcome
    assert outcome is not None
    assert (outcome.winner, outcome.game_points, outcome.reason) == (
        1,
        3,  # player 1 has no trick
        EndReason.WRONG_DECLARATION,
    )
