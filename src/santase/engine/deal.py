"""Seeded shuffling and the deal (rules R1.2, R1.3)."""

from __future__ import annotations

import random
from collections.abc import Sequence

from santase.engine.cards import FULL_DECK, Card
from santase.engine.state import DealState, TrumpTurned, other


def shuffled_deck(seed: int | str) -> tuple[Card, ...]:
    """A deterministic shuffle. String seeds are stable across Python runs."""
    deck = list(FULL_DECK)
    random.Random(seed).shuffle(deck)
    return tuple(deck)


def deal_from_order(order: Sequence[Card], dealer: int) -> DealState:
    """Deal a deck given top card first, as in R1.2.

    The cut is not modelled: cutting a uniformly shuffled deck leaves it uniform.
    """
    if sorted(order) != sorted(FULL_DECK):
        raise ValueError("order must be a permutation of the 24-card deck")
    non_dealer = other(dealer)
    packets = [tuple(order[i : i + 3]) for i in range(0, 12, 3)]
    hands: list[tuple[Card, ...]] = [(), ()]
    hands[non_dealer] = tuple(sorted(packets[0] + packets[2]))
    hands[dealer] = tuple(sorted(packets[1] + packets[3]))
    trump = order[12]
    return DealState(
        hands=(hands[0], hands[1]),
        talon=(*order[13:], trump),
        trump_suit=trump.suit,
        dealer=dealer,
        leader=non_dealer,
        turn=non_dealer,
        history=(TrumpTurned(trump),),
    )


def new_deal(seed: int | str, dealer: int) -> DealState:
    return deal_from_order(shuffled_deck(seed), dealer)
