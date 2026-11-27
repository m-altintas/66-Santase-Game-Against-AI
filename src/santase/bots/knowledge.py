"""What a player can infer from an observation: counts, known cards and suit constraints.

Everything here is derived from the public history plus the player's own hand, the way a
player with perfect memory reasons at the table (rules R8.1, "memory is a skill").
"""

from __future__ import annotations

from dataclasses import dataclass

from santase.engine import FULL_DECK, Card, Observation, Rank, Suit
from santase.engine.state import (
    CardPlayed,
    MarriageAnnounced,
    TalonClosed,
    TrickTaken,
    TrumpCardTaken,
    TrumpExchanged,
    TrumpTurned,
)

INITIAL_TALON = 12


@dataclass(frozen=True, slots=True)
class Knowledge:
    player: int
    trick_points: tuple[int, int]
    marriage_points: tuple[int, int]
    tricks_won: tuple[int, int]
    tricks_played: int
    last_trick_winner: int | None
    bottom_card: Card | None  # the trump card under the talon, face up or remembered
    opponent_known: frozenset[Card]  # cards certainly in the opponent's hand
    opponent_void: frozenset[Suit]  # suits the opponent cannot hold (strict play)
    opponent_ceiling: tuple[tuple[Suit, Rank], ...]  # no opponent card above this rank
    unseen: frozenset[Card]  # cards whose location the player does not know

    def points(self, player: int) -> int:
        return self.trick_points[player] + self.marriage_points[player]

    def opponent_may_hold(self, card: Card) -> bool:
        if card.suit in self.opponent_void:
            return False
        return all(card.suit != suit or card.rank <= rank for suit, rank in self.opponent_ceiling)


def infer(obs: Observation) -> Knowledge:
    me, opp = obs.player, 1 - obs.player
    trick_pts = [0, 0]
    marriage_pts = [0, 0]
    won = [0, 0]
    played: set[Card] = set()
    known: set[Card] = set()
    void: set[Suit] = set()
    ceiling: dict[Suit, Rank] = {}
    talon = INITIAL_TALON
    closed = False
    bottom: Card | None = None
    trick: list[tuple[int, Card]] = []
    last_winner: int | None = None

    for event in obs.history:
        match event:
            case TrumpTurned(card=card):
                bottom = card
            case TrumpExchanged(player=p, nine=nine, taken=taken):
                bottom = nine
                if p == opp:
                    known.add(taken)
            case TrumpCardTaken(player=p, card=card):
                bottom = None
                if p == opp:
                    known.add(card)
            case MarriageAnnounced(player=p, suit=suit, points=points):
                marriage_pts[p] += points
                if p == opp:
                    known.update((Card(suit, Rank.KING), Card(suit, Rank.QUEEN)))
            case TalonClosed():
                closed = True
            case CardPlayed(player=p, card=card):
                played.add(card)
                known.discard(card)
                if trick and p == opp and (closed or talon == 0):
                    _constrain(trick[0][1], card, obs.trump_suit, void, ceiling)
                trick.append((p, card))
            case TrickTaken(winner=w):
                trick_pts[w] += sum(card.points for _, card in trick)
                won[w] += 1
                last_winner = w
                trick = []
                if not closed and talon > 0:
                    talon -= 2
            case _:
                pass

    if obs.talon_size == 0:
        bottom = None
    located = set(obs.hand) | played | known | ({bottom} if bottom else set())
    return Knowledge(
        player=me,
        trick_points=(trick_pts[0], trick_pts[1]),
        marriage_points=(marriage_pts[0], marriage_pts[1]),
        tricks_won=(won[0], won[1]),
        tricks_played=won[0] + won[1],
        last_trick_winner=last_winner,
        bottom_card=bottom,
        opponent_known=frozenset(known),
        opponent_void=frozenset(void),
        opponent_ceiling=tuple(sorted(ceiling.items())),
        unseen=frozenset(set(FULL_DECK) - located),
    )


def _constrain(
    led: Card, follow: Card, trump: Suit, void: set[Suit], ceiling: dict[Suit, Rank]
) -> None:
    """Apply R3.1 to an opponent's follow in strict play."""
    if follow.suit == led.suit:
        if follow.rank < led.rank:  # could not head the led card
            ceiling[led.suit] = min(ceiling.get(led.suit, Rank.ACE), led.rank)
        return
    void.add(led.suit)
    if follow.suit != trump:
        void.add(trump)
