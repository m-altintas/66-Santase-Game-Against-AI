"""Win-rate intervals and Elo ratings."""

from __future__ import annotations

import math
from collections.abc import Sequence

Z95 = 1.959964


def wilson(successes: float, trials: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval for a proportion (draws may count as half a success)."""
    if trials == 0:
        return (0.0, 1.0)
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def elo(
    names: Sequence[str], games: Sequence[tuple[str, str, float]], steps: int = 2000
) -> dict[str, float]:
    """Bradley-Terry Elo from (a, b, score of a) results, mean 1500.

    One virtual draw per pair acts as a weak prior, so a 100% pairing gives a large but finite
    gap instead of one that grows with the number of fitting steps.
    """
    games = [*games, *((a, b, 0.5) for i, a in enumerate(names) for b in names[i + 1 :])]
    rating = dict.fromkeys(names, 0.0)
    scale = math.log(10) / 400
    for _ in range(steps):
        grad = dict.fromkeys(names, 0.0)
        for a, b, score in games:
            expected = 1 / (1 + math.exp(-scale * (rating[a] - rating[b])))
            grad[a] += score - expected
            grad[b] -= score - expected
        for name in names:
            rating[name] += 8 * grad[name] / max(1, len(games)) * len(names)
        mean = sum(rating.values()) / len(names)
        rating = {n: r - mean for n, r in rating.items()}
    return {n: 1500 + r for n, r in rating.items()}
