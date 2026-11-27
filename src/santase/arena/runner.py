"""Headless tournaments: every pair of bots plays the same seeded deals from both seats."""

from __future__ import annotations

import itertools
import random
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass

from santase.bots import make_bot
from santase.engine import new_deal, observe, step


@dataclass(frozen=True, slots=True)
class DealResult:
    seed: str
    seats: tuple[str, str]  # bot spec in seat 0 and seat 1
    winner: int | None  # seat
    game_points: int
    reason: str
    seconds: tuple[float, float]
    moves: tuple[int, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def play_deal(seat0: str, seat1: str, seed: str, dealer: int) -> DealResult:
    bots = (make_bot(seat0), make_bot(seat1))
    rngs = (random.Random(f"{seed}:0:{seat0}"), random.Random(f"{seed}:1:{seat1}"))
    seconds, moves = [0.0, 0.0], [0, 0]
    state = new_deal(seed, dealer)
    while not state.is_over:
        player = state.turn
        start = time.perf_counter()
        action = bots[player].act(observe(state, player), rngs[player])
        seconds[player] += time.perf_counter() - start
        moves[player] += 1
        state = step(state, action)
    outcome = state.outcome
    assert outcome is not None
    return DealResult(
        seed,
        (seat0, seat1),
        outcome.winner,
        outcome.game_points,
        outcome.reason.value,
        (seconds[0], seconds[1]),
        (moves[0], moves[1]),
    )


def _job(args: tuple[str, str, str, int]) -> DealResult:
    """Run one deal; a crash is recorded as a result instead of ending the tournament."""
    try:
        return play_deal(*args)
    except Exception as exc:
        seat0, seat1, seed, _ = args
        return DealResult(seed, (seat0, seat1), None, 0, f"error: {exc!r}", (0.0, 0.0), (0, 0))


def schedule(
    specs: list[str], deals: int, prefix: str = "arena"
) -> list[tuple[str, str, str, int]]:
    """Each pair plays `deals` seeds twice, once from each seat (mirrored)."""
    jobs: list[tuple[str, str, str, int]] = []
    for a, b in itertools.combinations(specs, 2):
        for i in range(deals):
            seed = f"{prefix}:{i}"
            jobs.append((a, b, seed, i % 2))
            jobs.append((b, a, seed, i % 2))
    return jobs


def run(
    specs: list[str],
    deals: int,
    workers: int = 1,
    prefix: str = "arena",
    progress: Callable[[int, int], None] | None = None,
) -> list[DealResult]:
    if len(set(specs)) != len(specs):
        raise ValueError("bot specs must be distinct")
    jobs = schedule(specs, deals, prefix)
    results: list[DealResult] = []
    if workers <= 1:
        stream: Iterable[DealResult] = map(_job, jobs)
        results = _collect(stream, len(jobs), progress)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = _collect(pool.map(_job, jobs, chunksize=4), len(jobs), progress)
    return results


def _collect(
    stream: Iterable[DealResult], total: int, progress: Callable[[int, int], None] | None
) -> list[DealResult]:
    results: list[DealResult] = []
    for result in stream:
        results.append(result)
        if progress is not None:
            progress(len(results), total)
    return results
