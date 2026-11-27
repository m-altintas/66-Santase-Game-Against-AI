"""Summaries of arena results as a dict (for JSON) and a Markdown table."""

from __future__ import annotations

import itertools
from collections.abc import Sequence

from santase.arena.runner import DealResult
from santase.arena.stats import elo, wilson


def summarize(specs: Sequence[str], all_results: Sequence[DealResult]) -> dict[str, object]:
    errors = [r for r in all_results if r.reason.startswith("error")]
    results = [r for r in all_results if not r.reason.startswith("error")]
    pairs: list[dict[str, object]] = []
    games: list[tuple[str, str, float]] = []
    for a, b in itertools.combinations(specs, 2):
        score, points, n = 0.0, 0, 0
        for r in results:
            if set(r.seats) != {a, b}:
                continue
            seat_a = r.seats.index(a)
            n += 1
            if r.winner is None:
                score += 0.5
                games.append((a, b, 0.5))
            elif r.winner == seat_a:
                score += 1
                points += r.game_points
                games.append((a, b, 1.0))
            else:
                points -= r.game_points
                games.append((a, b, 0.0))
        low, high = wilson(score, n)
        pairs.append(
            {
                "a": a,
                "b": b,
                "deals": n,
                "win_rate_a": score / n if n else 0.0,
                "ci95": [low, high],
                "game_points_per_deal_a": points / n if n else 0.0,
            }
        )
    timing: dict[str, float] = {}
    for spec in specs:
        secs = sum(r.seconds[i] for r in results for i in (0, 1) if r.seats[i] == spec)
        moves = sum(r.moves[i] for r in results for i in (0, 1) if r.seats[i] == spec)
        timing[spec] = 1000 * secs / moves if moves else 0.0
    ratings = elo(list(specs), games)
    return {
        "bots": list(specs),
        "elo": ratings,
        "ms_per_move": timing,
        "pairs": pairs,
        "errors": [r.to_dict() for r in errors],
    }


def markdown(summary: dict[str, object]) -> str:
    ratings: dict[str, float] = summary["elo"]  # type: ignore[assignment]
    timing: dict[str, float] = summary["ms_per_move"]  # type: ignore[assignment]
    pairs: list[dict[str, object]] = summary["pairs"]  # type: ignore[assignment]
    lines = ["| Bot | Elo | ms/move |", "|---|---:|---:|"]
    for name in sorted(ratings, key=lambda n: -ratings[n]):
        lines.append(f"| {name} | {ratings[name]:.0f} | {timing[name]:.1f} |")
    lines += [
        "",
        "| A | B | Deals | A win rate | 95% CI | A game points/deal |",
        "|---|---|---:|---:|---|---:|",
    ]
    for p in pairs:
        low, high = p["ci95"]  # type: ignore[misc]
        lines.append(
            f"| {p['a']} | {p['b']} | {p['deals']} | {p['win_rate_a']:.3f} | "
            f"{low:.3f} to {high:.3f} | {p['game_points_per_deal_a']:+.2f} |"
        )
    return "\n".join(lines)
