"""States for bot tests: random legal play from a seed, optionally stopped early."""

import random

from santase.engine import DealState, Declare, legal_actions, new_deal, step


def random_states(seed: int, dealer: int = 0) -> list[DealState]:
    """Every state of one deal played by random moves that never declare."""
    rng = random.Random(seed)
    states = [new_deal(seed, dealer)]
    while not states[-1].is_over:
        actions = [a for a in legal_actions(states[-1]) if a != Declare()] or [Declare()]
        states.append(step(states[-1], rng.choice(actions)))
    return states
