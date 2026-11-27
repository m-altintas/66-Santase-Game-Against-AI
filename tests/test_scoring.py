"""R5.3 to R5.5, R7, R8: end of the deal and game points."""

from typing import Any

import pytest
from helpers import c, make_state

from santase.engine import (
    Announce,
    DealOutcome,
    Declare,
    EndReason,
    Play,
    Suit,
    legal_actions,
    step,
)

H = Suit.HEARTS


def declare(**kwargs: Any) -> tuple[int | None, int, EndReason]:
    state = make_state("AC", "9C", "QD JD AS", **kwargs)
    outcome = step(state, Declare()).outcome
    assert outcome is not None
    return outcome.winner, outcome.game_points, outcome.reason


@pytest.mark.parametrize(
    ("points", "won", "game_points"),
    [
        ((66, 40), (3, 2), 1),
        ((70, 33), (3, 2), 1),  # 33 is not "fewer than 33"
        ((70, 32), (3, 2), 2),
        ((80, 0), (4, 0), 3),
    ],
)
def test_r8_1_correct_declaration(
    points: tuple[int, int], won: tuple[int, int], game_points: int
) -> None:
    assert declare(trick_points=points, tricks_won=won) == (0, game_points, EndReason.DECLARED_OUT)


@pytest.mark.parametrize(("won", "game_points"), [((3, 2), 2), ((3, 0), 3)])
def test_r8_1a_wrong_declaration(won: tuple[int, int], game_points: int) -> None:
    result = declare(trick_points=(65, 10), tricks_won=won)
    assert result == (1, game_points, EndReason.WRONG_DECLARATION)


def test_r8_1_marriage_counts_and_declare_right_after_it() -> None:
    state = make_state("KH QH", "9C", "QD JD AS", trick_points=(50, 30), tricks_won=(2, 1))
    state = step(state, Announce(H))
    assert Declare() in legal_actions(state)
    outcome = step(state, Declare()).outcome
    assert outcome is not None
    assert (outcome.winner, outcome.game_points) == (0, 2)
    assert outcome.card_points == (70, 30)


def test_r8_1_declaring_is_optional_and_needs_the_lead() -> None:
    state = make_state("AC KD", "9C JD", "QD JD AS", trick_points=(70, 0), tricks_won=(3, 0))
    assert Declare() in legal_actions(state)
    state = step(state, Play(c("AC")))  # plays on instead
    assert state.outcome is None
    assert Declare() not in legal_actions(state)  # the follower cannot declare
    assert Declare() not in legal_actions(make_state("AC", "9C", "QD JD AS", tricks_played=0))


def test_r5_3_closer_declares_correctly() -> None:
    result = declare(trick_points=(70, 40), tricks_won=(3, 2), closed_by=0)
    assert result == (0, 1, EndReason.CLOSER_WON)


def test_r5_4_closer_declares_wrong() -> None:
    result = declare(trick_points=(60, 40), tricks_won=(3, 2), closed_by=0)
    assert result == (1, 2, EndReason.CLOSER_FAILED)


def test_r5_4_opponent_of_closer_reaches_66_first() -> None:
    result = declare(trick_points=(70, 30), tricks_won=(3, 1), closed_by=1)
    assert result == (0, 2, EndReason.CLOSER_FAILED)


def test_r8_1a_opponent_of_closer_declares_wrong() -> None:
    result = declare(trick_points=(50, 30), tricks_won=(2, 1), closed_by=1)
    assert result == (1, 2, EndReason.WRONG_DECLARATION)


def play_last_trick(**kwargs: Any) -> DealOutcome | None:
    state = make_state("AH", "9H", "", trump=Suit.SPADES, **kwargs)
    return step(step(state, Play(c("AH"))), Play(c("9H"))).outcome


def test_r5_4_closer_fails_when_cards_run_out() -> None:
    outcome = play_last_trick(closed_by=0, trick_points=(40, 0), tricks_won=(2, 0))
    assert outcome is not None
    assert (outcome.winner, outcome.game_points, outcome.reason) == (1, 3, EndReason.CLOSER_FAILED)
    assert outcome.card_points == (51, 0)  # R5.5: no last-trick bonus after a close


def test_r5_3_closer_with_66_at_the_end_wins() -> None:
    outcome = play_last_trick(closed_by=0, trick_points=(60, 40), tricks_won=(3, 2))
    assert outcome is not None
    assert (outcome.winner, outcome.game_points, outcome.reason) == (0, 1, EndReason.CLOSER_WON)


def test_r7_1_last_trick_bonus() -> None:
    outcome = play_last_trick(trick_points=(50, 49), tricks_won=(5, 6))
    assert outcome is not None
    assert outcome.card_points == (71, 49)
    assert (outcome.winner, outcome.game_points) == (0, 1)


def test_r8_2_more_points_wins_when_cards_run_out() -> None:
    outcome = play_last_trick(trick_points=(20, 89), tricks_won=(5, 6))
    assert outcome is not None
    assert outcome.card_points == (41, 89)
    assert (outcome.winner, outcome.game_points, outcome.reason) == (
        1,
        1,
        EndReason.CARDS_EXHAUSTED,
    )


def test_r8_2_equal_points_is_a_draw() -> None:
    outcome = play_last_trick(trick_points=(44, 65), tricks_won=(5, 6))
    assert outcome is not None
    assert outcome.card_points == (65, 65)
    assert (outcome.winner, outcome.game_points, outcome.reason) == (None, 0, EndReason.DRAW)
