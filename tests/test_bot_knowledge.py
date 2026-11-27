"""Inference and determinization from an observation."""

import random

from bot_utils import random_states
from helpers import c, make_state
from hypothesis import given
from hypothesis import strategies as st

from santase.bots.determinize import determinize
from santase.bots.knowledge import infer
from santase.engine import Close, Play, Suit, observe, step
from santase.engine.state import CardPlayed, TrickTaken

seeds = st.integers(min_value=0, max_value=2**32)


@given(seeds, st.integers(min_value=0, max_value=1))
def test_determinized_world_matches_the_observation(seed: int, player: int) -> None:
    rng = random.Random(seed)
    for state in random_states(seed):
        if state.is_over:
            break
        obs = observe(state, player)
        world = determinize(obs, rng)
        assert observe(world, player) == obs
        assert world.trick_points == state.trick_points
        assert world.marriage_points == state.marriage_points
        assert world.tricks_won == state.tricks_won


@given(seeds)
def test_the_true_deal_satisfies_the_inferred_constraints(seed: int) -> None:
    for state in random_states(seed):
        for player in (0, 1):
            k = infer(observe(state, player))
            opponent_hand = set(state.hands[1 - player])
            assert k.opponent_known <= opponent_hand
            assert all(k.opponent_may_hold(card) for card in opponent_hand)
            assert opponent_hand - k.opponent_known <= k.unseen


def test_strict_follow_reveals_voids_and_ceilings() -> None:
    closed = step(make_state("QH KC", "9H 10S", "JC QD AS"), Close())
    state = step(step(closed, Play(c("QH"))), Play(c("9H")))  # 9H < QH: nothing above Q
    k = infer(observe(state, 0))
    assert not k.opponent_may_hold(c("AH")) and not k.opponent_may_hold(c("KH"))
    assert k.opponent_may_hold(c("JH"))
    closed = step(make_state("QH KC", "9C 10D", "JC QD AS"), Close())
    state = step(step(closed, Play(c("QH"))), Play(c("9C")))  # no heart, no trump
    k = infer(observe(state, 0))
    assert Suit.HEARTS in k.opponent_void and Suit.SPADES in k.opponent_void


def test_closing_keeps_the_trump_card_known() -> None:
    state = step(make_state("AH KC", "9H JC", "QC JD AS"), Close())
    k = infer(observe(state, 0))
    assert k.bottom_card == c("AS")
    assert c("AS") not in k.unseen


def test_points_are_counted_from_history() -> None:
    state = make_state("AH", "10H", "QC JD AS", tricks_played=0, tricks_won=(0, 0))
    state = step(step(state, Play(c("AH"))), Play(c("10H")))
    assert isinstance(state.history[-1], TrickTaken)
    assert any(isinstance(e, CardPlayed) for e in state.history)
    k = infer(observe(state, 1))
    assert k.points(0) == 21 and k.tricks_won == (1, 0)
