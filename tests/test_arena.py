"""Arena scheduling, statistics and reports."""

import pytest

from santase.arena.report import markdown, summarize
from santase.arena.runner import play_deal, run, schedule
from santase.arena.stats import elo, wilson


def test_wilson_interval() -> None:
    low, high = wilson(50, 100)
    assert low == pytest.approx(0.4038, abs=1e-3) and high == pytest.approx(0.5962, abs=1e-3)
    assert wilson(0, 0) == (0.0, 1.0)
    assert wilson(10, 10)[1] == pytest.approx(1.0)


def test_elo_orders_a_stronger_player_first() -> None:
    games = [("a", "b", 1.0)] * 75 + [("a", "b", 0.0)] * 25
    ratings = elo(["a", "b"], games)
    assert ratings["a"] - ratings["b"] == pytest.approx(189, abs=6)  # ~75% with a weak prior
    assert sum(ratings.values()) == pytest.approx(3000)


def test_schedule_mirrors_seats() -> None:
    jobs = schedule(["x", "y", "z"], deals=2)
    assert len(jobs) == 3 * 2 * 2
    assert ("x", "y", "arena:0", 0) in jobs and ("y", "x", "arena:0", 0) in jobs


def test_play_deal_is_reproducible() -> None:
    assert (
        play_deal("greedy", "random", "s", 1).winner == play_deal("greedy", "random", "s", 1).winner
    )


def test_summary_and_markdown() -> None:
    results = run(["random", "greedy"], deals=20)
    summary = summarize(["random", "greedy"], results)
    pair = summary["pairs"][0]  # type: ignore[index]
    assert pair["deals"] == 40
    assert 0 <= pair["ci95"][0] <= pair["win_rate_a"] <= pair["ci95"][1] <= 1
    table = markdown(summary)
    assert "| greedy |" in table and "95% CI" in table


def test_parallel_run_matches_serial() -> None:
    def outcomes(workers: int) -> list[tuple[object, ...]]:
        results = run(["random", "greedy"], deals=4, workers=workers)
        return [(r.seed, r.seats, r.winner, r.game_points, r.moves) for r in results]

    assert outcomes(2) == outcomes(1)  # timings differ, decisions do not


def test_a_crashing_deal_is_recorded_not_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    from santase.arena import runner

    def boom(*_args: object) -> None:
        raise RuntimeError("bot bug")

    monkeypatch.setattr(runner, "play_deal", boom)
    results = runner.run(["random", "greedy"], deals=1)
    assert all(r.reason.startswith("error") for r in results)
    assert len(summarize(["random", "greedy"], results)["errors"]) == 2  # type: ignore[arg-type]


def test_elo_stays_finite_for_a_clean_sweep() -> None:
    ratings = elo(["a", "b"], [("a", "b", 1.0)] * 100)
    assert 400 < ratings["a"] - ratings["b"] < 1500


def test_duplicate_specs_are_rejected() -> None:
    with pytest.raises(ValueError, match="distinct"):
        run(["random", "random"], deals=1)
