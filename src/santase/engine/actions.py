"""Player actions and their text form (used by replays and the CLI)."""

from __future__ import annotations

from dataclasses import dataclass

from santase.engine.cards import Card, Suit


@dataclass(frozen=True, slots=True)
class Play:
    """Lead or follow with a card."""

    card: Card

    def __str__(self) -> str:
        return f"play:{self.card}"


@dataclass(frozen=True, slots=True)
class Announce:
    """Announce a marriage (K and Q) in a suit before leading (R6)."""

    suit: Suit

    def __str__(self) -> str:
        return f"marriage:{self.suit.letter}"


@dataclass(frozen=True, slots=True)
class Exchange:
    """Exchange the 9 of trumps for the trump card (R4)."""

    def __str__(self) -> str:
        return "exchange"


@dataclass(frozen=True, slots=True)
class Close:
    """Close the talon (R5)."""

    def __str__(self) -> str:
        return "close"


@dataclass(frozen=True, slots=True)
class Declare:
    """Declare "out": claim 66 or more card points (R8.1)."""

    def __str__(self) -> str:
        return "out"


Action = Play | Announce | Exchange | Close | Declare

_SUIT_BY_LETTER = {suit.letter: suit for suit in Suit}


def parse_action(text: str) -> Action:
    """Inverse of str(action)."""
    head, _, arg = text.strip().lower().partition(":")
    match head, arg:
        case "play", card if card:
            return Play(Card.parse(card))
        case "marriage", letter if letter.upper() in _SUIT_BY_LETTER:
            return Announce(_SUIT_BY_LETTER[letter.upper()])
        case "exchange", "":
            return Exchange()
        case "close", "":
            return Close()
        case "out", "":
            return Declare()
        case _:
            raise ValueError(f"not an action: {text!r}")
