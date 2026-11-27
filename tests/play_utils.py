"""Random legal play for tests."""

import random

from santase.engine import Action, MatchState, legal_actions, match_step, new_match


def random_match(seed: int, target: int = 11) -> tuple[MatchState, list[Action]]:
    rng = random.Random(seed)
    match = new_match(seed, target)
    actions: list[Action] = []
    while not match.is_over:
        action = rng.choice(legal_actions(match.deal))
        actions.append(action)
        match = match_step(match, action)
    return match, actions
