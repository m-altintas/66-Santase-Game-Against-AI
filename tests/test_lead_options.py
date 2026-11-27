"""R4 trump exchange, R5 closing, R6 marriages."""

from helpers import c, make_state

from santase.engine import (
    Announce,
    Close,
    Declare,
    Exchange,
    Play,
    Suit,
    cards,
    legal_actions,
    step,
)
from santase.engine.state import MarriageAnnounced, TrumpExchanged

H, S = Suit.HEARTS, Suit.SPADES


def test_r4_1_exchange_the_nine() -> None:
    state = make_state("9S KH", "JC", "QC JD AS")
    assert Exchange() in legal_actions(state)
    after = step(state, Exchange())
    assert after.hands[0] == tuple(sorted(cards("AS KH")))
    assert after.talon == cards("QC JD 9S")
    assert after.trump_card == c("9S")
    assert after.history[-1] == TrumpExchanged(0, c("9S"), c("AS"))
    assert Exchange() not in legal_actions(after)


def test_r4_1_exchange_not_allowed() -> None:
    assert Exchange() not in legal_actions(make_state("9S KH", "JC", "QC JD AS", tricks_played=0))
    assert Exchange() not in legal_actions(make_state("9S KH", "JC", "JD AS"))  # talon of 2
    assert Exchange() not in legal_actions(make_state("9S KH", "JC", "QC JD AS", closed_by=1))
    follower = make_state("JC", "9S KH", "QC JD AS", trick="JC")
    assert Exchange() not in legal_actions(follower)


def test_r5_1_close_stops_drawing() -> None:
    state = make_state("AH KC", "9H JC", "QC JD AS")
    assert Close() in legal_actions(state)
    state = step(state, Close())
    assert state.closed_by == 0 and state.strict
    assert state.trump_card is None  # turned face down
    state = step(step(state, Play(c("AH"))), Play(c("9H")))
    assert state.hands == ((c("KC"),), (c("JC"),))
    assert state.talon == cards("QC JD AS")


def test_r5_1_close_not_allowed() -> None:
    assert Close() not in legal_actions(make_state("AH", "9H", "QC JD AS", tricks_played=0))
    assert Close() not in legal_actions(make_state("AH", "9H", "JD AS"))
    assert Close() not in legal_actions(make_state("AH", "9H", "QC JD AS", closed_by=0))


def test_r5_2_order_exchange_close_marriage_play() -> None:
    state = make_state("9S KH QH", "JC", "QC JD AS")
    state = step(state, Exchange())
    state = step(state, Close())
    assert Exchange() not in legal_actions(state)
    state = step(state, Announce(H))
    assert Close() not in legal_actions(state)
    assert set(legal_actions(state)) == {Declare(), Play(c("KH")), Play(c("QH"))}


def test_r6_1_marriage_points_and_lead() -> None:
    state = make_state("KH QH 9C", "JC", "QC JD AS")
    state = step(state, Announce(H))
    assert state.marriage_points == (20, 0)
    assert state.history[-1] == MarriageAnnounced(0, H, 20)
    assert Play(c("9C")) not in legal_actions(state)
    state = step(state, Play(c("QH")))
    assert state.announced is None


def test_r6_1_trump_marriage_is_forty() -> None:
    state = step(make_state("KS QS", "JC", "QC JD AS"), Announce(S))
    assert state.marriage_points == (40, 0)


def test_r6_1_one_marriage_per_lead() -> None:
    state = step(make_state("KS QS KH QH", "JC", "QC JD AS"), Announce(H))
    assert not any(isinstance(a, Announce) for a in legal_actions(state))


def test_r6_2_no_marriage_on_first_trick() -> None:
    state = make_state("KH QH", "JC", "QC JD AS", tricks_played=0)
    assert Announce(H) not in legal_actions(state)


def test_r6_3_marriage_after_close_or_exhaustion() -> None:
    assert Announce(H) in legal_actions(make_state("KH QH", "JC", "QC JD AS", closed_by=1))
    assert Announce(H) in legal_actions(make_state("KH QH", "JC JD", "", trump=S))
