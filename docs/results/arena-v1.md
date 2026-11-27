# Arena v1: classical bots

Run on 2026-11-27 with rules version 1. Command:

```
python -m santase.arena random greedy pimc ismcts --deals 200 --workers 10
```

Each pair played 200 seeded deals twice, once from each seat, so deal luck cancels out
(400 deals per pair). A deal win counts 1 and a draw counts 0.5. Elo is a Bradley-Terry fit
with one virtual draw per pair as a prior. The ms/move figures were measured with 10 deals
running in parallel on a 12-thread x86_64 desktop; a single game runs about twice as fast.

| Bot | What it is |
|---|---|
| random | random legal moves; declares "out" only with 66 |
| greedy | the university bot's idea: win the current trick if possible |
| pimc | 20 sampled worlds, UCT with 30 iterations each, worlds vote; exact solver in strict play |
| ismcts | single-observer information set MCTS, 1000 iterations |

All bots act from the observation only, and both search bots switch to the exact endgame
solver once the talon is exhausted.

| Bot | Elo | ms/move |
|---|---:|---:|
| ismcts | 1678 | 684.5 |
| pimc | 1590 | 322.5 |
| greedy | 1498 | 0.1 |
| random | 1234 | 0.1 |

| A | B | Deals | A win rate | 95% CI | A game points/deal |
|---|---|---:|---:|---|---:|
| random | greedy | 400 | 0.190 | 0.155 to 0.231 | -1.47 |
| random | pimc | 400 | 0.110 | 0.083 to 0.144 | -1.61 |
| random | ismcts | 400 | 0.062 | 0.043 to 0.091 | -1.88 |
| greedy | pimc | 400 | 0.380 | 0.334 to 0.428 | -0.13 |
| greedy | ismcts | 400 | 0.264 | 0.223 to 0.309 | -0.62 |
| pimc | ismcts | 400 | 0.384 | 0.337 to 0.432 | -0.59 |

## Reading

- The ordering random < greedy < pimc < ismcts holds, and every pairwise 95% interval
  excludes 50%. This is the phase 2 check from the plan.
- PIMC beats greedy on deals (62%) but barely on game points (+0.13 per deal): it wins small
  (1.15 points on average) and loses big (1.52). Searching worlds where it sees the talon
  makes it too confident, the known weakness of determinized search (strategy fusion).
  ISMCTS does not have this problem as strongly and wins both ways.
- A first run had PIMC making 23 wrong "out" declarations: the solver treated a wrong "out"
  as equal to playing on and tried it first. Fixed before this run; there are none now.
