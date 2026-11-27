"""The endgame solver against plain minimax."""

import time

import pytest
from bot_utils import random_states

from santase.bots.endgame import EndgameSolver, outcome_value
from santase.engine import DealState, legal_actions, step


def minimax(state: DealState, player: int) -> int:
    """Value for `player` with no pruning and no table."""
    if state.is_over:
        return outcome_value(state, player)
    values = [minimax(step(state, a), player) for a in legal_actions(state)]
    return max(values) if state.turn == player else min(values)


def late_strict_states(count: int, max_cards: int) -> list[DealState]:
    found: list[DealState] = []
    seed = 0
    while len(found) < count:
        for state in random_states(seed):
            if state.strict and not state.is_over and len(state.hands[state.turn]) <= max_cards:
                found.append(state)
                break
        seed += 1
    return found


@pytest.mark.parametrize("state", late_strict_states(25, 4))
def test_solver_matches_minimax(state: DealState) -> None:
    value, action = EndgameSolver().solve(state)
    assert value == minimax(state, state.turn)
    assert minimax(step(state, action), state.turn) == value
    for a, v in EndgameSolver().values(state).items():
        assert v == minimax(step(state, a), state.turn)


def test_solver_rejects_open_talon() -> None:
    with pytest.raises(ValueError, match="no more draws"):
        EndgameSolver().solve(random_states(0)[0])


def test_solver_is_fast_enough_on_full_endgames() -> None:
    states = late_strict_states(10, 6)
    start = time.perf_counter()
    for state in states:
        EndgameSolver().solve(state)
    assert (time.perf_counter() - start) / len(states) < 0.5


def test_solver_never_concedes_with_a_wrong_out() -> None:
    from santase.engine import Declare

    checked = 0
    for state in late_strict_states(60, 6):
        if Declare() in legal_actions(state) and state.card_points(state.turn) < 66:
            assert EndgameSolver().solve(state)[1] != Declare()
            checked += 1
    assert checked > 5
