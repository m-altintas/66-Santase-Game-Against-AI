"""Builders for hand-made deal states."""

from santase.engine import Card, DealState, Suit, cards
from santase.engine.state import TrumpTurned


def make_state(
    hand0: str,
    hand1: str,
    talon: str,
    *,
    leader: int = 0,
    trump: Suit | None = None,
    trick: str = "",
    tricks_played: int = 1,
    tricks_won: tuple[int, int] = (1, 1),
    trick_points: tuple[int, int] = (0, 0),
    marriage_points: tuple[int, int] = (0, 0),
    closed_by: int | None = None,
    dealer: int = 1,
) -> DealState:
    talon_cards = cards(talon)
    led = cards(trick)
    if trump is None:
        trump = talon_cards[-1].suit
    return DealState(
        hands=(tuple(sorted(cards(hand0))), tuple(sorted(cards(hand1)))),
        talon=talon_cards,
        trump_suit=trump,
        dealer=dealer,
        leader=leader,
        turn=leader if not led else 1 - leader,
        trick=led,
        tricks_played=tricks_played,
        trick_points=trick_points,
        marriage_points=marriage_points,
        tricks_won=tricks_won,
        closed_by=closed_by,
        history=(TrumpTurned(talon_cards[-1]),) if talon_cards else (),
    )


def c(text: str) -> Card:
    return Card.parse(text)
