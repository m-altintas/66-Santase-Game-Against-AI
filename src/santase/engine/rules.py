"""Legal actions and state transitions (rules R2 to R6, R8.1).

A lead is a sequence of optional actions in the order of R5.2: exchange the 9, close,
announce a marriage, then play a card. "Out" may be declared at any point of a lead before the
card is played, except on the first trick of the deal. R8.1 allows it right after winning a
trick or announcing a marriage; an exchange or close in between changes no points.
"""

from __future__ import annotations

from dataclasses import replace

from santase.engine.actions import Action, Announce, Close, Declare, Exchange, Play
from santase.engine.cards import Card, Rank, Suit
from santase.engine.scoring import score_declaration, score_exhausted
from santase.engine.state import (
    CardPlayed,
    DealState,
    MarriageAnnounced,
    OutDeclared,
    TalonClosed,
    TrickTaken,
    TrumpCardTaken,
    TrumpExchanged,
    other,
)

MIN_TALON_FOR_EXCHANGE_OR_CLOSE = 3  # "more than 2 cards" (R4.1, R5.1)
MARRIAGE_POINTS = 20
TRUMP_MARRIAGE_POINTS = 40


class IllegalActionError(ValueError):
    pass


def trick_winner(led: Card, follow: Card, trump: Suit) -> bool:
    """True if the follower's card wins the trick (R2.1)."""
    if follow.suit == led.suit:
        return follow.rank > led.rank
    return follow.suit == trump


def legal_follows(hand: tuple[Card, ...], led: Card, trump: Suit, strict: bool) -> tuple[Card, ...]:
    """Cards the follower may play (R2.2, R3.1)."""
    if not strict:
        return hand
    same = tuple(c for c in hand if c.suit == led.suit)
    if same:
        higher = tuple(c for c in same if c.rank > led.rank)
        return higher or same
    trumps = tuple(c for c in hand if c.suit == trump)
    return trumps or hand


def _marriage_suits(hand: tuple[Card, ...]) -> tuple[Suit, ...]:
    return tuple(
        suit for suit in Suit if Card(suit, Rank.KING) in hand and Card(suit, Rank.QUEEN) in hand
    )


def _can_exchange_or_close(state: DealState) -> bool:
    return (
        state.tricks_played > 0
        and state.announced is None
        and state.closed_by is None
        and len(state.talon) >= MIN_TALON_FOR_EXCHANGE_OR_CLOSE
    )


def legal_actions(state: DealState) -> tuple[Action, ...]:
    if state.is_over:
        return ()
    hand = state.hands[state.turn]
    if state.trick:
        follows = legal_follows(hand, state.trick[0], state.trump_suit, state.strict)
        return tuple(Play(c) for c in follows)

    actions: list[Action] = []
    if state.tricks_played > 0:
        actions.append(Declare())
    if _can_exchange_or_close(state):
        if Card(state.trump_suit, Rank.NINE) in hand:
            actions.append(Exchange())
        actions.append(Close())
    if state.announced is None:
        if state.tricks_played > 0:
            actions.extend(Announce(s) for s in _marriage_suits(hand))
        actions.extend(Play(c) for c in hand)
    else:
        actions.extend(Play(c) for c in hand if c.suit == state.announced and c.rank in _KQ)
    return tuple(actions)


_KQ = (Rank.KING, Rank.QUEEN)


def step(state: DealState, action: Action) -> DealState:
    """Apply a legal action and return the new state. The input is never modified."""
    if action not in legal_actions(state):
        raise IllegalActionError(f"{action} is not legal here")
    player = state.turn
    match action:
        case Declare():
            state = replace(state, history=(*state.history, OutDeclared(player)))
            return score_declaration(state, player)
        case Exchange():
            return _exchange(state, player)
        case Close():
            return replace(state, closed_by=player, history=(*state.history, TalonClosed(player)))
        case Announce(suit=suit):
            return _announce(state, player, suit)
        case Play(card=card):
            return _play(state, player, card)


def _exchange(state: DealState, player: int) -> DealState:
    nine = Card(state.trump_suit, Rank.NINE)
    taken = state.talon[-1]
    hand = tuple(sorted((*_without(state.hands[player], nine), taken)))
    return replace(
        state,
        hands=_with_hand(state.hands, player, hand),
        talon=(*state.talon[:-1], nine),
        history=(*state.history, TrumpExchanged(player, nine, taken)),
    )


def _announce(state: DealState, player: int, suit: Suit) -> DealState:
    points = TRUMP_MARRIAGE_POINTS if suit == state.trump_suit else MARRIAGE_POINTS
    marriage = list(state.marriage_points)
    marriage[player] += points
    return replace(
        state,
        announced=suit,
        marriage_points=(marriage[0], marriage[1]),
        history=(*state.history, MarriageAnnounced(player, suit, points)),
    )


def _play(state: DealState, player: int, card: Card) -> DealState:
    hands = _with_hand(state.hands, player, _without(state.hands[player], card))
    history = (*state.history, CardPlayed(player, card))
    if not state.trick:
        return replace(
            state, hands=hands, trick=(card,), turn=other(player), announced=None, history=history
        )
    led = state.trick[0]
    winner = player if trick_winner(led, card, state.trump_suit) else state.leader
    points = list(state.trick_points)
    points[winner] += led.points + card.points
    won = list(state.tricks_won)
    won[winner] += 1
    state = replace(
        state,
        hands=hands,
        trick=(),
        tricks_played=state.tricks_played + 1,
        trick_points=(points[0], points[1]),
        tricks_won=(won[0], won[1]),
        leader=winner,
        turn=winner,
        last_trick_winner=winner,
        history=(*history, TrickTaken(winner)),
    )
    if state.closed_by is None and state.talon:
        state = _draw(state, winner)
    if not state.hands[0] and not state.hands[1]:
        return score_exhausted(state)
    return state


def _draw(state: DealState, winner: int) -> DealState:
    """Winner draws first, then the loser (R2.3)."""
    loser = other(winner)
    first, second, *rest = state.talon
    hands = _with_hand(state.hands, winner, tuple(sorted((*state.hands[winner], first))))
    hands = _with_hand(hands, loser, tuple(sorted((*hands[loser], second))))
    history = state.history
    if not rest:
        history = (*history, TrumpCardTaken(loser, second))
    return replace(state, hands=hands, talon=tuple(rest), history=history)


def _without(hand: tuple[Card, ...], card: Card) -> tuple[Card, ...]:
    return tuple(c for c in hand if c != card)


def _with_hand(
    hands: tuple[tuple[Card, ...], tuple[Card, ...]], player: int, hand: tuple[Card, ...]
) -> tuple[tuple[Card, ...], tuple[Card, ...]]:
    return (hand, hands[1]) if player == 0 else (hands[0], hand)
