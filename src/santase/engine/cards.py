"""Cards, ranks and points (rules R1.1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    @property
    def letter(self) -> str:
        return "CDHS"[self]


class Rank(IntEnum):
    """Ordered low to high as in R1.1: 9, J, Q, K, 10, A."""

    NINE = 0
    JACK = 1
    QUEEN = 2
    KING = 3
    TEN = 4
    ACE = 5

    @property
    def points(self) -> int:
        return _POINTS[self]

    @property
    def label(self) -> str:
        return _LABELS[self]


_POINTS = {
    Rank.NINE: 0,
    Rank.JACK: 2,
    Rank.QUEEN: 3,
    Rank.KING: 4,
    Rank.TEN: 10,
    Rank.ACE: 11,
}
_LABELS = {
    Rank.NINE: "9",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
    Rank.TEN: "10",
    Rank.ACE: "A",
}
_RANK_BY_LABEL = {label: rank for rank, label in _LABELS.items()} | {"T": Rank.TEN}
_SUIT_BY_LETTER = {suit.letter: suit for suit in Suit}


@dataclass(frozen=True, slots=True, order=True)
class Card:
    suit: Suit
    rank: Rank

    @property
    def points(self) -> int:
        return self.rank.points

    def __str__(self) -> str:
        return f"{self.rank.label}{self.suit.letter}"

    @staticmethod
    def parse(text: str) -> Card:
        """Parse "AH", "10S" or "TS" (rank label, then suit letter)."""
        text = text.strip().upper()
        rank = _RANK_BY_LABEL.get(text[:-1])
        suit = _SUIT_BY_LETTER.get(text[-1:])
        if rank is None or suit is None:
            raise ValueError(f"not a Santase card: {text!r}")
        return Card(suit, rank)


def cards(text: str) -> tuple[Card, ...]:
    """Parse a space-separated card list, for example "AH 10H KS"."""
    return tuple(Card.parse(token) for token in text.split())


FULL_DECK: tuple[Card, ...] = tuple(Card(suit, rank) for suit in Suit for rank in Rank)
TOTAL_CARD_POINTS = sum(card.points for card in FULL_DECK)
