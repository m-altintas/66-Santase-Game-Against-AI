"""R2 tricks and drawing, R3 strict play."""

import pytest
from helpers import c, make_state

from santase.engine import IllegalActionError, Play, Suit, cards, legal_actions, step
from santase.engine.rules import legal_follows, trick_winner
from santase.engine.state import TrickTaken, TrumpCardTaken

S = Suit.SPADES


@pytest.mark.parametrize(
    ("led", "follow", "follower_wins"),
    [
        ("KH", "AH", True),  # higher card of the led suit
        ("10H", "KH", False),  # 10 outranks K
        ("AH", "9S", True),  # trump beats any non-trump
        ("JS", "QS", True),  # higher trump
        ("AS", "10S", False),
        ("9H", "AC", False),  # neither trump nor led suit always loses
    ],
)
def test_r2_1_trick_winner(led: str, follow: str, follower_wins: bool) -> None:
    assert trick_winner(c(led), c(follow), S) is follower_wins


def test_r2_2_any_card_while_talon_open() -> None:
    state = make_state("9H", "KH 9C JD", "QC JC 9S", trick="AH", leader=0)
    assert set(legal_actions(state)) == {Play(card) for card in cards("KH 9C JD")}


def test_r2_3_winner_draws_first() -> None:
    state = make_state("AH", "9H", "QC JC 10D AS")
    state = step(step(state, Play(c("AH"))), Play(c("9H")))
    assert state.hands == ((c("QC"),), (c("JC"),))
    assert state.talon == cards("10D AS")


def test_r2_3_loser_takes_the_trump_card_last() -> None:
    state = make_state("AH KC", "9H JC", "QC AS")
    state = step(step(state, Play(c("AH"))), Play(c("9H")))
    assert state.hands == (tuple(sorted(cards("KC QC"))), tuple(sorted(cards("JC AS"))))
    assert state.talon == ()
    assert state.history[-1] == TrumpCardTaken(1, c("AS"))
    assert state.strict


def test_r2_4_trick_winner_leads_next() -> None:
    state = make_state("9H KC", "AH JC", "QC JD 10D AS")
    state = step(step(state, Play(c("9H"))), Play(c("AH")))
    assert TrickTaken(1) in state.history
    assert state.leader == 1 and state.turn == 1
    assert state.tricks_won == (1, 2)
    assert state.trick_points == (0, 11)


def test_illegal_action_is_rejected_and_state_unchanged() -> None:
    state = make_state("AH", "9H", "QC JC 10D AS")
    with pytest.raises(IllegalActionError):
        step(state, Play(c("KD")))
    assert state.hands[0] == (c("AH"),)


@pytest.mark.parametrize(
    ("hand", "led", "allowed"),
    [
        ("9H KH AH 9S", "QH", "KH AH"),  # follow suit and win if able
        ("9H JH 9S", "QH", "9H JH"),  # follow suit, cannot win
        ("9C JS QS", "QH", "JS QS"),  # void: must trump
        ("9C JD", "QH", "9C JD"),  # neither: any card
        ("JS AS 9H", "QS", "AS"),  # trump led: must head it
    ],
)
def test_r3_1_strict_follow(hand: str, led: str, allowed: str) -> None:
    assert set(legal_follows(cards(hand), c(led), S, strict=True)) == set(cards(allowed))


def test_r3_1_applies_when_talon_exhausted() -> None:
    state = make_state("QH", "9H AH 9S", "", trump=S, trick="QH")
    assert set(legal_actions(state)) == {Play(c("AH"))}


def test_r3_1_applies_after_closing() -> None:
    state = make_state("QH", "9H AH 9S", "JC 10D AS", trick="QH", closed_by=0)
    assert set(legal_actions(state)) == {Play(c("AH"))}
