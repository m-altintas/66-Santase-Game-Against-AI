"""The bot interface and shared decision helpers."""

from __future__ import annotations

import random
from typing import Protocol

from santase.bots.knowledge import Knowledge
from santase.engine import Action, Declare, Observation
from santase.engine.state import WIN_THRESHOLD


class Bot(Protocol):
    name: str

    def act(self, obs: Observation, rng: random.Random) -> Action:
        """Choose one of obs.legal_actions. Must use nothing but obs and rng."""
        ...


def can_declare(obs: Observation, knowledge: Knowledge) -> bool:
    """A correct "out" is available: the player counts 66 or more (R8.1)."""
    return Declare() in obs.legal_actions and knowledge.points(obs.player) >= WIN_THRESHOLD


def without_declare(actions: tuple[Action, ...]) -> list[Action]:
    return [a for a in actions if a != Declare()]
