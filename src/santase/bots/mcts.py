"""Search bots: determinized MCTS (PIMC) and single-observer ISMCTS.

Both sample full deals consistent with the observation (determinize.py) and search them with
random playouts. Once the talon is exhausted the deal is fully known to the player, so both
switch to the exact endgame solver.

Rewards are signed game points of the deal divided by 3, from the acting player's side.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from santase.bots.base import can_declare
from santase.bots.determinize import determinize
from santase.bots.endgame import EndgameSolver, outcome_value
from santase.bots.knowledge import infer
from santase.engine import (
    Action,
    Close,
    DealState,
    Declare,
    Observation,
    legal_actions,
    step,
)
from santase.engine.state import WIN_THRESHOLD

MAX_GAME_POINTS = 3
EXPLORATION = 1.4  # rewards lie in [-1, 1]


def rollout(state: DealState, rng: random.Random) -> DealState:
    """Random play to the end; declares "out" exactly when the mover has 66.

    Playouts never close the talon: a uniform choice would close on about one lead in eight
    and drag every estimate towards closed-talon outcomes.
    """
    while not state.is_over:
        actions = legal_actions(state)
        if Declare() in actions and state.card_points(state.turn) >= WIN_THRESHOLD:
            state = step(state, Declare())
            continue
        choices = [a for a in actions if a != Declare() and a != Close()]
        state = step(state, rng.choice(choices))
    return state


def reward(state: DealState, player: int) -> float:
    return outcome_value(state, player) / MAX_GAME_POINTS


def _solved(obs: Observation, rng: random.Random) -> Action | None:
    """Exact play when nothing is hidden any more (talon exhausted, R3.1 phase)."""
    if obs.talon_size or obs.closed_by is not None:
        return None
    state = determinize(obs, rng)  # unique: every unseen card is in the opponent's hand
    return EndgameSolver().solve(state)[1]


@dataclass(eq=False, slots=True)
class _Node:
    mover: int | None = None  # who chose the action leading here
    visits: int = 0
    available: int = 0
    total: float = 0.0
    children: dict[Action, _Node] = field(default_factory=dict)  # pyright: ignore[reportUnknownVariableType]

    def ucb(self, parent_visits: int) -> float:
        return self.total / self.visits + EXPLORATION * math.sqrt(
            math.log(parent_visits) / self.visits
        )


def _iterate(root: _Node, world: DealState, rng: random.Random, use_availability: bool) -> None:
    """One select-expand-rollout-backpropagate pass on a fully known world."""
    node, state, path = root, world, [root]
    while not state.is_over:
        actions = legal_actions(state)
        if use_availability:
            for action in actions:
                child = node.children.get(action)
                if child is not None:
                    child.available += 1
        untried = [a for a in actions if a not in node.children]
        if untried:
            action = rng.choice(untried)
            node.children[action] = child = _Node(mover=state.turn, available=1)
            state = step(state, action)
            path.append(child)
            break
        parent_visits = max(node.visits, 1)
        action = max(
            actions,
            key=lambda a: node.children[a].ucb(
                node.children[a].available if use_availability else parent_visits
            ),
        )
        node = node.children[action]
        state = step(state, action)
        path.append(node)
    final = rollout(state, rng)
    for visited in path:
        visited.visits += 1
        if visited.mover is not None:
            visited.total += reward(final, visited.mover)


def _best(root: _Node, legal: tuple[Action, ...]) -> Action:
    return max(legal, key=lambda a: root.children[a].visits if a in root.children else -1)


class DeterminizedMCTS:
    """Perfect-information Monte Carlo: search each sampled world, then let the worlds vote.

    Each world gives one vote, split over its root actions by visit share (UCT) or among
    its best actions (exact solve), so a move is not penalised for being explored more.
    """

    def __init__(self, worlds: int = 20, iterations: int = 600) -> None:
        self.worlds = worlds
        self.iterations = iterations
        self.name = f"pimc-{worlds}x{iterations // worlds}"

    def act(self, obs: Observation, rng: random.Random) -> Action:
        if len(obs.legal_actions) == 1:
            return obs.legal_actions[0]
        knowledge = infer(obs)
        if can_declare(obs, knowledge):
            return Declare()
        solved = _solved(obs, rng)
        if solved is not None:
            return solved
        votes = dict.fromkeys(obs.legal_actions, 0.0)
        per_world = max(self.iterations // self.worlds, 2 * len(obs.legal_actions))
        for _ in range(self.worlds):
            world = determinize(obs, rng, knowledge)
            if world.strict:
                values = EndgameSolver().values(world)
                top = max(values.values())
                best = [a for a, v in values.items() if v == top]
                for action in best:
                    votes[action] += 1 / len(best)
                continue
            root = _Node()
            for _ in range(per_world):
                _iterate(root, world, rng, use_availability=False)
            for action, child in root.children.items():
                votes[action] += child.visits / per_world
        return max(obs.legal_actions, key=lambda a: votes[a])


class ISMCTS:
    """Single-observer information set MCTS (Cowling, Powley and Whitehouse, 2012)."""

    def __init__(self, iterations: int = 1000) -> None:
        self.iterations = iterations
        self.name = f"ismcts-{iterations}"

    def act(self, obs: Observation, rng: random.Random) -> Action:
        if len(obs.legal_actions) == 1:
            return obs.legal_actions[0]
        knowledge = infer(obs)
        if can_declare(obs, knowledge):
            return Declare()
        solved = _solved(obs, rng)
        if solved is not None:
            return solved
        root = _Node()
        for _ in range(self.iterations):
            _iterate(root, determinize(obs, rng, knowledge), rng, use_availability=True)
        return _best(root, obs.legal_actions)
