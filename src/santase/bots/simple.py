"""Baselines: a rule-aware random bot and a one-trick greedy bot."""

from __future__ import annotations

import random
from collections.abc import Callable

from santase.bots.base import can_declare, without_declare
from santase.bots.knowledge import infer
from santase.engine import Action, Announce, Card, Declare, Exchange, Observation, Play, Rank
from santase.engine.rules import trick_winner


class RandomBot:
    """Random legal moves. Declares "out" only when it really has 66, never by accident."""

    name = "random"

    def act(self, obs: Observation, rng: random.Random) -> Action:
        if can_declare(obs, infer(obs)):
            return Declare()
        return rng.choice(without_declare(obs.legal_actions))


class GreedyBot:
    """The university bot's idea, kept simple: win the current trick if possible.

    Leads its median card, follows with its strongest winning card or dumps its weakest,
    always exchanges the 9 and announces marriages, never closes.
    """

    name = "greedy"

    def act(self, obs: Observation, rng: random.Random) -> Action:
        if can_declare(obs, infer(obs)):
            return Declare()
        legal = obs.legal_actions
        if Exchange() in legal:
            return Exchange()
        marriages = [a for a in legal if isinstance(a, Announce)]
        if marriages:
            return max(marriages, key=lambda a: a.suit == obs.trump_suit)
        plays = [a.card for a in legal if isinstance(a, Play)]
        if obs.trick:
            return Play(self._follow(plays, obs.trick[0], obs))
        ordered = sorted(plays, key=_strength(obs))
        return Play(ordered[len(ordered) // 2])

    @staticmethod
    def _follow(plays: list[Card], led: Card, obs: Observation) -> Card:
        winners = [c for c in plays if trick_winner(led, c, obs.trump_suit)]
        if winners:
            return max(winners, key=lambda c: c.points)
        return min(plays, key=_strength(obs))


def _strength(obs: Observation) -> Callable[[Card], tuple[bool, int, Rank]]:
    return lambda card: (card.suit == obs.trump_suit, card.points, card.rank)
