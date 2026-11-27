"""Property tests over random legal games (plan phase 1).

Run the long version with: pytest --hypothesis-profile=thorough tests/test_properties.py
"""

import random
from dataclasses import fields

from hypothesis import given
from hypothesis import strategies as st

from santase.engine import (
    Card,
    DealState,
    EndReason,
    Observation,
    legal_actions,
    new_deal,
    observe,
    step,
)
from santase.engine.cards import TOTAL_CARD_POINTS
from santase.engine.observation import count_points
from santase.engine.scoring import LAST_TRICK_BONUS
from santase.engine.state import (
    CardPlayed,
    MarriageAnnounced,
    TrickTaken,
    TrumpCardTaken,
    TrumpExchanged,
    TrumpTurned,
)

MAX_ACTIONS_PER_DEAL = 12 * 2 + 12 * 4  # plays, plus at most a few lead options per trick


def play_deal(seed: int, dealer: int) -> list[DealState]:
    rng = random.Random(seed)
    states = [new_deal(seed, dealer)]
    while not states[-1].is_over:
        assert len(states) <= MAX_ACTIONS_PER_DEAL, "deal did not terminate"
        actions = legal_actions(states[-1])
        assert actions, "a live deal must offer an action"
        states.append(step(states[-1], rng.choice(actions)))
    return states


def played_cards(state: DealState) -> list[Card]:
    return [e.card for e in state.history if isinstance(e, CardPlayed)]


seeds = st.integers(min_value=0, max_value=2**32)
dealers = st.sampled_from([0, 1])


@given(seeds, dealers)
def test_random_play_terminates_and_conserves_cards(seed: int, dealer: int) -> None:
    for state in play_deal(seed, dealer):
        located = [*state.hands[0], *state.hands[1], *state.talon, *played_cards(state)]
        assert sorted(located) == sorted(set(located))
        assert len(located) == 24


@given(seeds, dealers)
def test_trick_points_equal_the_cards_taken(seed: int, dealer: int) -> None:
    final = play_deal(seed, dealer)[-1]
    outcome = final.outcome
    assert outcome is not None
    assert final.trick == ()  # deals end between tricks
    taken = sum(card.points for card in played_cards(final))
    bonus = LAST_TRICK_BONUS if outcome.reason in (EndReason.CARDS_EXHAUSTED, EndReason.DRAW) else 0
    assert sum(final.trick_points) == taken + bonus
    if not final.hands[0] and final.closed_by is None:
        assert sum(final.trick_points) == TOTAL_CARD_POINTS + LAST_TRICK_BONUS


@given(seeds, dealers)
def test_every_trick_has_exactly_one_winner(seed: int, dealer: int) -> None:
    final = play_deal(seed, dealer)[-1]
    played = 0
    for event in final.history:
        if isinstance(event, CardPlayed):
            played += 1
        elif isinstance(event, TrickTaken):
            assert played == 2
            played = 0
    assert played in (0, 1)  # a declaration may stop play mid-lead, never mid-trick
    assert sum(final.tricks_won) == final.tricks_played


PUBLIC_REVEALS = (TrumpTurned, TrumpExchanged, TrumpCardTaken)


def visible_cards(obs: Observation) -> set[Card]:
    """Cards in an observation outside the public trump events."""
    seen = {*obs.hand, *obs.trick}
    if obs.trump_card is not None:
        seen.add(obs.trump_card)
    seen.update(e.card for e in obs.history if isinstance(e, CardPlayed))
    return seen


@given(seeds, dealers)
def test_observation_never_shows_hidden_cards(seed: int, dealer: int) -> None:
    for state in play_deal(seed, dealer):
        for player in (0, 1):
            obs = observe(state, player)
            hidden = set(state.hands[1 - player]) | set(state.talon)
            if state.trump_card is not None:
                hidden.discard(state.trump_card)
            assert not visible_cards(obs) & hidden
            assert all(
                isinstance(e, (CardPlayed, TrickTaken, MarriageAnnounced, *PUBLIC_REVEALS))
                or type(e).__name__ in ("TalonClosed", "OutDeclared")
                for e in obs.history
            )


def test_observation_has_no_running_score() -> None:
    names = {f.name for f in fields(Observation)}
    assert not names & {"trick_points", "marriage_points", "card_points", "scores", "tricks_won"}


@given(seeds, dealers)
def test_count_points_matches_the_engine(seed: int, dealer: int) -> None:
    for state in play_deal(seed, dealer):
        if state.is_over:
            break
        for player in (0, 1):
            assert count_points(observe(state, player).history, player) == state.card_points(player)
