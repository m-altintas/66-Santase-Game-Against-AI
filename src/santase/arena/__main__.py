"""Run a tournament: python -m santase.arena random greedy pimc ismcts --deals 200."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from santase.arena.report import markdown, summarize
from santase.arena.runner import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Santase bot arena")
    parser.add_argument("bots", nargs="+", help='bot specs, e.g. random greedy "ismcts:1000"')
    parser.add_argument("--deals", type=int, default=100, help="seeds per pair (each played twice)")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument("--out", type=Path, default=Path("results/arena"))
    args = parser.parse_args()

    start = time.perf_counter()
    results = run(args.bots, args.deals, args.workers)
    summary = summarize(args.bots, results)
    summary["seconds"] = time.perf_counter() - start
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2))
    (args.out / "deals.json").write_text(json.dumps([r.to_dict() for r in results]))
    table = markdown(summary)
    (args.out / "summary.md").write_text(table + "\n")
    print(table)


if __name__ == "__main__":
    main()
