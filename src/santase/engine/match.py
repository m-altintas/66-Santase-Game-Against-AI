"""A match: deals until one player has 11 game points (rules R9.1, R9.2)."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from santase.engine.actions import Action
from santase.engine.deal import new_deal
from santase.engine.rules import step
from santase.engine.state import DealOutcome, DealState

MATCH_TARGET = 11


@dataclass(frozen=True, slots=True)
class MatchState:
    seed: int | str
    scores: tuple[int, int]
    deal_index: int
    deal: DealState
    target: int = MATCH_TARGET
    last_outcome: DealOutcome | None = None  # outcome of the previous deal

    @property
    def winner(self) -> int | None:
        for player in (0, 1):
            if self.scores[player] >= self.target:
                return player
        return None

    @property
    def is_over(self) -> bool:
        return self.winner is not None


def deal_seed(match_seed: int | str, index: int) -> str:
    return f"{match_seed!r}:{index}"  # repr keeps int 3 and str "3" apart


def first_dealer(match_seed: int | str) -> int:
    return random.Random(f"{match_seed!r}:dealer").randrange(2)


def new_match(seed: int | str, target: int = MATCH_TARGET) -> MatchState:
    deal = new_deal(deal_seed(seed, 0), first_dealer(seed))
    return MatchState(seed=seed, scores=(0, 0), deal_index=0, deal=deal, target=target)


def match_step(match: MatchState, action: Action) -> MatchState:
    """Apply an action to the current deal; start the next deal when this one ends."""
    if match.is_over:
        raise ValueError("the match is over")
    deal = step(match.deal, action)
    outcome = deal.outcome
    if outcome is None:
        return replace(match, deal=deal)
    scores = list(match.scores)
    next_dealer = deal.dealer  # a draw: the same dealer deals again (R8.2)
    if outcome.winner is not None:
        scores[outcome.winner] += outcome.game_points
        next_dealer = outcome.winner  # R9.2
    finished = replace(match, scores=(scores[0], scores[1]), deal=deal, last_outcome=outcome)
    if finished.is_over:
        return finished
    index = match.deal_index + 1
    return replace(
        finished, deal_index=index, deal=new_deal(deal_seed(match.seed, index), next_dealer)
    )
