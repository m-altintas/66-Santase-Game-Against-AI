"""R9 match, replay records."""

import random

import pytest
from play_utils import random_match

from santase.engine import legal_actions, match_step, new_match
from santase.replay import MatchRecord, ReplayError, record_actions, replay


def test_r9_1_match_ends_at_target() -> None:
    match, _ = random_match(seed=3)
    assert match.winner is not None
    assert match.scores[match.winner] >= 11
    assert match.scores[1 - match.winner] < 11


def test_r9_2_winner_deals_next_and_draw_keeps_the_dealer() -> None:
    checked = 0
    for seed in range(30):
        rng = random.Random(seed)
        match = new_match(seed)
        while not match.is_over:
            after = match_step(match, rng.choice(legal_actions(match.deal)))
            if after.deal_index != match.deal_index:
                outcome = after.last_outcome
                assert outcome is not None
                expected = match.deal.dealer if outcome.winner is None else outcome.winner
                assert after.deal.dealer == expected
                assert after.deal.leader == 1 - expected  # R1.3
                gained = [after.scores[p] - match.scores[p] for p in (0, 1)]
                if outcome.winner is None:
                    assert gained == [0, 0]
                else:
                    assert gained[outcome.winner] == outcome.game_points
                    assert gained[1 - outcome.winner] == 0
                checked += 1
            match = after
    assert checked > 100


def test_replay_reproduces_the_final_state() -> None:
    for seed in range(20):
        final, actions = random_match(seed)
        record = record_actions(seed, 11, actions)
        assert replay(MatchRecord.from_json(record.to_json())) == final


def test_replay_rejects_illegal_actions() -> None:
    _, actions = random_match(0)
    record = record_actions(0, 11, actions)
    bad = MatchRecord(0, 11, ("play:AS", "play:AS", *record.actions))
    with pytest.raises(ReplayError):
        replay(bad)
    with pytest.raises(ReplayError):
        replay(MatchRecord(0, 11, ("dance",)))


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{}",
        '{"seed": 1, "target": 0, "actions": [], "rules_version": 1}',
        '{"seed": true, "target": 11, "actions": [], "rules_version": 1}',
        '{"seed": 1, "target": 11, "actions": [3], "rules_version": 1}',
    ],
)
def test_malformed_records_are_rejected(text: str) -> None:
    with pytest.raises(ReplayError):
        MatchRecord.from_json(text)


def test_unknown_rules_version_is_rejected() -> None:
    with pytest.raises(ReplayError):
        replay(MatchRecord(0, 11, (), rules_version=99))


def test_int_and_string_seeds_give_different_matches() -> None:
    assert new_match(3).deal != new_match("3").deal
