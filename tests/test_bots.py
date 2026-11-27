"""Bots: legal moves, no hidden information, sensible declarations."""

import random
from dataclasses import replace

import pytest
from bot_utils import random_states

from santase.bots import make_bot
from santase.engine import DealState, Declare, legal_actions, new_deal, observe, step

FAST_SPECS = ["random", "greedy", "pimc:4:40", "ismcts:60"]


def swap_hidden(state: DealState, player: int) -> DealState | None:
    """Same observation for `player`, different hidden cards: swap an opponent card with a
    face-down talon card."""
    opp = 1 - player
    face_down = state.talon[:-1]
    if not face_down or not state.hands[opp]:
        return None
    a, b = state.hands[opp][0], face_down[0]
    hands = list(state.hands)
    hands[opp] = tuple(sorted((*state.hands[opp][1:], b)))
    talon = (a, *state.talon[1:])
    other = replace(state, hands=(hands[0], hands[1]), talon=talon)
    assert observe(other, player) == observe(state, player)
    return other


@pytest.mark.parametrize("spec", FAST_SPECS)
def test_bots_ignore_hidden_information(spec: str) -> None:
    checked = 0
    for seed in range(6):
        for state in random_states(seed)[1:8]:
            if state.is_over:
                continue
            other = swap_hidden(state, state.turn)
            if other is None:
                continue
            bot = make_bot(spec)
            first = bot.act(observe(state, state.turn), random.Random(seed))
            second = bot.act(observe(other, other.turn), random.Random(seed))
            assert first == second
            checked += 1
    assert checked > 10


@pytest.mark.parametrize("spec", FAST_SPECS)
def test_bots_play_legal_moves_to_the_end(spec: str) -> None:
    for seed in range(3):
        state = new_deal(seed, seed % 2)
        bot, rng = make_bot(spec), random.Random(seed)
        while not state.is_over:
            obs = observe(state, state.turn)
            action = bot.act(obs, rng)
            assert action in obs.legal_actions
            state = step(state, action)


def lead_states_with_declare(rich: bool, count: int) -> list[DealState]:
    """Real states where the player on lead may declare, with or without 66 points."""
    found: list[DealState] = []
    seed = 0
    while len(found) < count:
        for state in random_states(seed):
            if Declare() in legal_actions(state) and (state.card_points(state.turn) >= 66) is rich:
                found.append(state)
                break
        seed += 1
    return found


@pytest.mark.parametrize("spec", FAST_SPECS)
def test_bots_declare_with_66_and_never_without(spec: str) -> None:
    bot = make_bot(spec)
    for rich in (True, False):
        for state in lead_states_with_declare(rich, 5):
            chose = bot.act(observe(state, state.turn), random.Random(0)) == Declare()
            assert chose is rich


def test_unknown_bot_spec() -> None:
    with pytest.raises(ValueError, match="unknown bot"):
        make_bot("oracle")
