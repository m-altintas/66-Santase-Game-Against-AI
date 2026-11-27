"""What one player knows: the only view of a deal that bots and the UI receive.

It holds the player's own hand and everything that happened in public. It holds no running
score (R8.1, R8.1b); a player who wants one keeps count from `history`.
"""

from __future__ import annotations

from dataclasses import dataclass

from santase.engine.actions import Action
from santase.engine.cards import Card, Suit
from santase.engine.rules import legal_actions
from santase.engine.state import (
    CardPlayed,
    DealOutcome,
    DealState,
    Event,
    MarriageAnnounced,
    TrickTaken,
)


@dataclass(frozen=True, slots=True)
class Observation:
    player: int
    hand: tuple[Card, ...]
    trump_suit: Suit
    trump_card: Card | None  # face up on the table, if still there
    talon_size: int
    opponent_hand_size: int
    dealer: int
    leader: int
    turn: int
    trick: tuple[Card, ...]
    closed_by: int | None
    announced: Suit | None
    history: tuple[Event, ...]
    legal_actions: tuple[Action, ...]  # empty unless it is this player's turn
    outcome: DealOutcome | None


def observe(state: DealState, player: int) -> Observation:
    return Observation(
        player=player,
        hand=state.hands[player],
        trump_suit=state.trump_suit,
        trump_card=state.trump_card,
        talon_size=len(state.talon),
        opponent_hand_size=len(state.hands[1 - player]),
        dealer=state.dealer,
        leader=state.leader,
        turn=state.turn,
        trick=state.trick,
        closed_by=state.closed_by,
        announced=state.announced,
        history=state.history,
        legal_actions=legal_actions(state) if state.turn == player else (),
        outcome=state.outcome,
    )


def count_points(history: tuple[Event, ...], player: int) -> int:
    """A player's card points, counted from public events the way a player keeps count.

    For bots only. The UI must never display it during a deal (R8.1, R8.1b).
    """
    total = 0
    pending: list[Card] = []
    for event in history:
        if isinstance(event, CardPlayed):
            pending.append(event.card)
        elif isinstance(event, TrickTaken):
            if event.winner == player:
                total += sum(card.points for card in pending)
            pending = []
        elif isinstance(event, MarriageAnnounced) and event.player == player:
            total += event.points
    return total
