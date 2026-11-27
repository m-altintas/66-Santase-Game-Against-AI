"""Sample a full deal state consistent with what one player knows.

Unseen cards are split between the opponent's hand and the face-down talon, uniformly over all
splits that respect the known cards and the strict-play constraints.
"""

from __future__ import annotations

import random

from santase.bots.knowledge import Knowledge, infer
from santase.engine import Card, DealState, Observation


def determinize(
    obs: Observation, rng: random.Random, knowledge: Knowledge | None = None
) -> DealState:
    k = knowledge or infer(obs)
    me, opp = obs.player, 1 - obs.player
    opp_slots = obs.opponent_hand_size - len(k.opponent_known)
    allowed = sorted(c for c in k.unseen if k.opponent_may_hold(c))
    forbidden = sorted(c for c in k.unseen if not k.opponent_may_hold(c))
    if opp_slots < 0 or len(allowed) < opp_slots:
        raise ValueError("observation is inconsistent with the inferred constraints")
    rng.shuffle(allowed)
    opp_hand = (*k.opponent_known, *allowed[:opp_slots])
    talon_rest = [*allowed[opp_slots:], *forbidden]
    rng.shuffle(talon_rest)
    talon: tuple[Card, ...] = ()
    if obs.talon_size:
        assert k.bottom_card is not None
        talon = (*talon_rest, k.bottom_card)
    if len(talon) != obs.talon_size:
        raise ValueError("talon size does not match the unseen cards")

    hands: list[tuple[Card, ...]] = [(), ()]
    hands[me] = obs.hand
    hands[opp] = tuple(sorted(opp_hand))
    return DealState(
        hands=(hands[0], hands[1]),
        talon=talon,
        trump_suit=obs.trump_suit,
        dealer=obs.dealer,
        leader=obs.leader,
        turn=obs.turn,
        trick=obs.trick,
        tricks_played=k.tricks_played,
        trick_points=k.trick_points,
        marriage_points=k.marriage_points,
        tricks_won=k.tricks_won,
        closed_by=obs.closed_by,
        announced=obs.announced,
        last_trick_winner=k.last_trick_winner,
        history=obs.history,
    )
