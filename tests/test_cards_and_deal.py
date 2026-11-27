"""R1: cards and deal."""

import pytest
from helpers import c

from santase.engine import FULL_DECK, Card, Play, Rank, cards, deal_from_order, new_deal
from santase.engine.actions import parse_action
from santase.engine.cards import TOTAL_CARD_POINTS


def test_r1_1_deck_ranks_and_points() -> None:
    assert len(FULL_DECK) == 24
    assert len(set(FULL_DECK)) == 24
    assert [r.label for r in sorted(Rank)] == ["9", "J", "Q", "K", "10", "A"]
    assert {r.label: r.points for r in Rank} == {"9": 0, "J": 2, "Q": 3, "K": 4, "10": 10, "A": 11}
    assert TOTAL_CARD_POINTS == 120


def test_card_text_round_trip() -> None:
    for card in FULL_DECK:
        assert Card.parse(str(card)) == card
    assert Card.parse("TS") == c("10S")
    assert str(parse_action("play:10s")) == "play:10S"


ORDER = cards(
    "9C JC QC KC 10C AC "  # first two packets
    "9D JD QD KD 10D AD "  # last two packets
    "9H "  # 13th card: trump
    "JH QH KH 10H AH 9S JS QS KS 10S AS"
)


def test_r1_2_packets_of_three_then_trump() -> None:
    state = deal_from_order(ORDER, dealer=1)
    assert state.hands[0] == tuple(sorted(cards("9C JC QC 9D JD QD")))  # non-dealer first
    assert state.hands[1] == tuple(sorted(cards("KC 10C AC KD 10D AD")))
    assert state.trump_suit == c("9H").suit
    assert state.talon[-1] == c("9H")  # trump card at the bottom, drawn last
    assert state.talon[0] == c("JH")
    assert len(state.talon) == 12


def test_r1_2_dealer_one_gets_second_packets() -> None:
    state = deal_from_order(ORDER, dealer=0)
    assert state.hands[1] == tuple(sorted(cards("9C JC QC 9D JD QD")))


def test_r1_3_non_dealer_leads() -> None:
    state = deal_from_order(ORDER, dealer=1)
    assert state.leader == 0 and state.turn == 0
    assert state.trick == ()


def test_seeded_deal_is_reproducible() -> None:
    assert new_deal("abc", 0) == new_deal("abc", 0)
    assert new_deal("abc", 0) != new_deal("abd", 0)


def test_first_lead_offers_only_plays() -> None:
    from santase.engine import legal_actions

    state = deal_from_order(ORDER, dealer=1)
    assert legal_actions(state) == tuple(Play(card) for card in state.hands[0])


@pytest.mark.parametrize("text", ["", "X", "1H", "AZ", "10"])
def test_bad_card_text_is_rejected(text: str) -> None:
    with pytest.raises(ValueError, match="not a Santase card"):
        Card.parse(text)


def test_deal_needs_a_full_deck() -> None:
    with pytest.raises(ValueError, match="permutation"):
        deal_from_order(ORDER[:-1], dealer=0)
