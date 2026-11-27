# Prior art

References read before writing the engine and bots. None of their code is copied, vendored or
imported into `src/`. They serve as design references and, where the licence and rules allow,
as dev-only test oracles.

| Project | Licence | Language | Rules match | Use here |
|---|---|---|---|---|
| [NikolayIT/SantaseGameEngine](https://github.com/NikolayIT/SantaseGameEngine) | MIT | C# (.NET 10) | Bulgarian Santase, but going out is automatic (our R8.1 is declared) | design reference; possible differential oracle for R1 to R7 |
| [intelligent-systems-course/schnapsen](https://github.com/intelligent-systems-course/schnapsen) (VU Amsterdam) | GPL-3.0 | Python | Schnapsen: 20 cards, no 9s, different numbers | bot ideas only |
| [google-deepmind/open_spiel](https://github.com/google-deepmind/open_spiel) | Apache-2.0 | C++/Python | no Santase game | algorithm reference (ISMCTS, CFR, NFSP) |

## What each one taught us

**SantaseGameEngine.** The closest match to our rules, with a 442-test xUnit suite for the
engine. `RULES.md` there is a source for our `docs/rules.md` (NE). Its strongest hand-written
player combines a heuristic for the open-talon phase with an exact alpha-beta search once the
talon is exhausted. At that point every card is known (own hand plus everything played), so the
endgame is a perfect-information game and can be solved exactly. We plan the same split: an
exact endgame solver shared by all search bots. Its neural player (`NEURAL_NETWORK.md`) is a
small from-scratch network trained from self-play and gated by a promotion check against the
previous best, the same shape as our phase 6 loop. Because its 66 is automatic, a differential
test can only compare deals in which no player declares, or must map our declaration onto its
automatic end.

**schnapsen (VU).** A teaching platform for the Austrian relative of Santase. Its bot set (random,
bully, rdeep, minimax, alpha-beta, an ML bot) is a ready-made ladder of baselines; `rdeep`
(random determinizations, then random rollouts) is the simplest search bot worth beating. The
licence is GPL-3.0, so nothing from it enters this MIT repository, and the different deck makes
it unsuitable as an oracle.

**OpenSpiel.** `open_spiel/python/algorithms/ismcts.py` is a clean reference for Information
Set MCTS (Cowling, Powley and Whitehouse, 2011): one tree over information sets, a fresh
determinization each iteration, UCT or PUCT child selection, and a cap on sampled worlds per
node. It also has CFR variants and NFSP, which are our fallback if PPO struggles (plan, risks).
OpenSpiel has no Santase game, so it is not an oracle.

## Consequences for the plan

- Phase 1: an endgame solver (talon exhausted or closed) belongs next to the engine, because
  every search bot needs it.
- Phase 2 baseline ladder: Random, Greedy, Determinized MCTS (rdeep style), ISMCTS.
- Differential testing against SantaseGameEngine is optional and dev-only. It needs the .NET
  SDK, so it stays out of CI unless it proves cheap.
