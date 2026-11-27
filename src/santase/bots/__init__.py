"""Bots. Each one decides from an Observation only and never sees hidden cards."""

from santase.bots.base import Bot
from santase.bots.mcts import ISMCTS, DeterminizedMCTS
from santase.bots.simple import GreedyBot, RandomBot


def make_bot(spec: str) -> Bot:
    """Build a bot from a name such as "random", "greedy", "pimc:20:600" or "ismcts:1000"."""
    name, *args = spec.split(":")
    numbers = [int(a) for a in args]
    match name, numbers:
        case "random", []:
            return RandomBot()
        case "greedy", []:
            return GreedyBot()
        case "pimc", []:
            return DeterminizedMCTS()
        case "pimc", [worlds, iterations]:
            return DeterminizedMCTS(worlds, iterations)
        case "ismcts", []:
            return ISMCTS()
        case "ismcts", [iterations]:
            return ISMCTS(iterations)
        case _:
            raise ValueError(f"unknown bot {spec!r}")


__all__ = ["ISMCTS", "Bot", "DeterminizedMCTS", "GreedyBot", "RandomBot", "make_bot"]
