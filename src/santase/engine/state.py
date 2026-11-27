"""Immutable deal state and the public event log.

`DealState` holds hidden information (both hands, the talon order). Only the engine reads it;
players get an `Observation` (see observation.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from santase.engine.cards import Card, Suit

PLAYERS = (0, 1)
HAND_SIZE = 6
WIN_THRESHOLD = 66


def other(player: int) -> int:
    return 1 - player


# Public events: what both players saw happen at the table.


@dataclass(frozen=True, slots=True)
class TrumpTurned:
    card: Card


@dataclass(frozen=True, slots=True)
class CardPlayed:
    player: int
    card: Card


@dataclass(frozen=True, slots=True)
class TrickTaken:
    winner: int


@dataclass(frozen=True, slots=True)
class MarriageAnnounced:
    player: int
    suit: Suit
    points: int


@dataclass(frozen=True, slots=True)
class TrumpExchanged:
    player: int
    nine: Card
    taken: Card


@dataclass(frozen=True, slots=True)
class TalonClosed:
    player: int


@dataclass(frozen=True, slots=True)
class TrumpCardTaken:
    """The loser of the last talon trick takes the face-up trump card (R2.3)."""

    player: int
    card: Card


@dataclass(frozen=True, slots=True)
class OutDeclared:
    player: int


Event = (
    TrumpTurned
    | CardPlayed
    | TrickTaken
    | MarriageAnnounced
    | TrumpExchanged
    | TalonClosed
    | TrumpCardTaken
    | OutDeclared
)


class EndReason(Enum):
    DECLARED_OUT = "declared_out"
    WRONG_DECLARATION = "wrong_declaration"
    CLOSER_FAILED = "closer_failed"
    CLOSER_WON = "closer_won"
    CARDS_EXHAUSTED = "cards_exhausted"
    DRAW = "draw"


@dataclass(frozen=True, slots=True)
class DealOutcome:
    winner: int | None  # None only for a draw (R8.2)
    game_points: int
    reason: EndReason
    card_points: tuple[int, int]


@dataclass(frozen=True, slots=True)
class DealState:
    hands: tuple[tuple[Card, ...], tuple[Card, ...]]
    talon: tuple[Card, ...]  # talon[0] is drawn next; talon[-1] is the trump card
    trump_suit: Suit
    dealer: int
    leader: int
    turn: int
    trick: tuple[Card, ...] = ()  # the led card, while waiting for the follower
    tricks_played: int = 0
    trick_points: tuple[int, int] = (0, 0)
    marriage_points: tuple[int, int] = (0, 0)
    tricks_won: tuple[int, int] = (0, 0)
    closed_by: int | None = None
    announced: Suit | None = None  # marriage announced on the current lead
    last_trick_winner: int | None = None
    history: tuple[Event, ...] = ()
    outcome: DealOutcome | None = None

    @property
    def strict(self) -> bool:
        """R3.1 applies once the talon is closed or exhausted."""
        return self.closed_by is not None or not self.talon

    @property
    def trump_card(self) -> Card | None:
        """The face-up trump card, if it is still on the table."""
        if self.talon and self.closed_by is None:
            return self.talon[-1]
        return None

    def card_points(self, player: int) -> int:
        return self.trick_points[player] + self.marriage_points[player]

    @property
    def is_over(self) -> bool:
        return self.outcome is not None
