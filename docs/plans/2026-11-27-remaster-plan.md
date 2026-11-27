# Santase remaster: plan

Date: 2026-11-27 · Status: draft, awaiting approval

## 1. Goal

Rebuild the 2025 university project (a pygame Santase game with four bots) from scratch as a
portfolio-grade repository:

- a rules engine that is correct, typed, tested and replayable;
- bots that play under genuine imperfect information, ranked by a measured tournament;
- a self-play reinforcement-learning agent that improves over published, gated versions;
- a browser demo with no server, later embedded in a personal portfolio site.

The repo is the first of a series of remastered course projects (Wikipedia RAG, Turkish Penal
Code LLM and stock-direction prediction follow). The cost ceiling for the whole series is the
price of one domain, about 10–12 USD per year.

### Non-goals (for this plan)

- The portfolio site itself (a separate repo, phase 5 only links to it).
- Multiplayer between humans, accounts, or chat.
- Keeping any of the legacy code, file layout or libraries.
- Building on a third-party game engine. Every part of the project is written from scratch;
  outside engines are references and test oracles only.

## 2. What the legacy code tells us

Short audit of `main` at `25f8f21` (2,592 lines, pygame):

| Finding | Where | Consequence for the remaster |
|---|---|---|
| Bots receive the human's real hand in `game_state` | `gameplay.py:174` | The engine must hand each player an *observation*, never the full state. |
| The hand sampler treats the remaining deck as known, so "unknown" cards collapse to the human's hand plus past tricks | `ai.py:257` | Determinization must sample from the true information set. |
| A "tie trick" branch exists | `gameplay.py:~737` | A Santase trick always has a winner; trick resolution needs rule tests. |
| The last-trick bonus is awarded when the deck empties | `gameplay.py:797` | Scoring rules are to be specified first, then tested against the spec. |
| Game logic, animation and input handling share one 1,026-line class | `gameplay.py` | The engine, bots and UI become separate layers. |
| No tests, no dependency file, one-line README, card art of unknown origin | repo | Covered by phases 0, 1 and 4. |

The legacy code is preserved under the tag `v0-university` before anything is removed.

## 3. Architecture

```
            ┌──────────────────────────── santase (Python package) ───────────────────────────┐
            │ engine/   rules, immutable State, legal_actions, step, Observation, seeded deal  │
            │ bots/     Random, Greedy, DeterminizedMCTS, ISMCTS, PolicyNet (RL)               │
            │ arena/    headless tournaments, Elo + win rate with confidence intervals         │
            │ rl/       self-play, training, checkpoint league, export of weights              │
            │ replay/   game record format (seed + action list), validator                     │
            └──────────────────────────────────────────────────────────────────────────────────┘
                     │ same wheel                                     │ weights (.npz)
                     ▼                                                ▼
   web/ (TypeScript + Vite)  ── Web Worker runs Pyodide ── engine + bots, NumPy inference
   renders Observation only, sends actions, never holds game logic
                     │ (phase 6) finished game records
                     ▼
   Cloudflare Worker + D1  ── replays each record in the engine, rejects illegal ones
                     │ weekly
                     ▼
   GitHub Actions  ── retrain → arena gate vs current version → publish new weights
```

Design rules:

1. **Information hiding by construction.** `State` is private to the engine. Bots and the UI
   receive only `Observation` (own hand, trump card, visible tricks, announced marriages, scores,
   deck size). An agent that never sees hidden cards cannot cheat.
2. **Pure, immutable core.** `step(state, action) -> state` has no side effects. That gives
   simple tests, cheap tree search, and deterministic replays.
3. **Seeded and replayable.** A game is fully described by `(rules_version, seed, actions)`.
   That format serves as test fixtures, the arena log, RL data and the upload format.
4. **One engine everywhere.** The browser, the arena, training and the server validator import
   the same package, so there is no second implementation that can drift.
5. **Assets are swappable.** The UI draws from SVG files behind a small manifest. The engine
   never refers to art.

## 4. Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.12, `pyproject.toml`, conda env `santase` | one language for engine, bots and RL |
| Quality | ruff (lint + format), pyright strict on `engine/`, pytest, hypothesis | property tests suit rule engines |
| CI | GitHub Actions: lint, types, tests, a short arena smoke run | |
| RL | PyTorch for training only; inference as a small MLP in NumPy | NumPy runs in Pyodide, so the browser needs no ONNX runtime |
| Web | TypeScript, Vite, Pyodide in a Web Worker, SVG cards | static output for GitHub/Cloudflare Pages |
| Data loop | Cloudflare Workers + D1 (free tier) | no server to run or pay for |

## 5. Phases

Each phase ends with a merged PR into `dev`. Each step is written as `step → verify`.

### Phase 0: groundwork

- Tag legacy `main` as `v0-university`; start the rewrite on `feat/engine` → verify: tag pushed.
- Prior-art study: read existing Santase/Schnapsen engines and bots (for example the VU
  Amsterdam Schnapsen platform, OpenSpiel's imperfect-information games) as references only.
  All engine, bot and training code in this repo is written here; no third-party engine is
  vendored or imported. External engines may serve as test oracles (differential tests on
  shared rules), kept as dev-only dependencies → verify: short note in `docs/research.md`
  listing what each reference taught us and its licence.
- Write `docs/rules.md`: the exact Santase variant (24 cards, 6-card hands, trump exchange with
  the 9, marriages 20/40, closing, 66 to win a deal, last-trick 10, 1/2/3 game points, 11 game
  points for a match), with sources and any house-rule choices marked → verify: Mehmet approves
  the variant.
- Repo skeleton: `pyproject`, env, ruff, pyright, pytest, CI → verify: CI green on an empty test.

### Phase 1: engine

- `Card`, `Deck`, seeded deal, `State`, `Observation`, `Action` → verify: unit tests.
- `legal_actions` and `step` for both phases (open deck and closed deck/talon exhausted), the
  trump exchange, marriages, closing, scoring and deal/match end → verify: one test per rule
  in `docs/rules.md`, plus hand-written replay fixtures of full deals.
- Property tests: points are conserved (always 120 card points plus bonuses), every trick has
  a winner, a random legal play always terminates, an observation never contains an opponent's
  hidden card → verify: hypothesis runs of 10k+ games pass.
- Replay format and validator → verify: replaying a record reproduces the final state exactly.
- CLI to play in the terminal → verify: a manual game to the end.

### Phase 2: classical bots and the arena

- `Random`, `Greedy` (ported in spirit), `DeterminizedMCTS`, `ISMCTS` (single-observer), each
  acting from an `Observation` only → verify: bots pass a "no hidden information" test that
  feeds two states identical in observation and checks that the decisions match.
- Arena: round-robin over N seeded deals with mirrored seats (each deal played twice with
  hands swapped, to cancel deal luck), Elo plus Wilson intervals on win rate, results as
  JSON and a Markdown table → verify: the ordering Random < Greedy < MCTS holds with
  non-overlapping intervals; MCTS speed reported per move.

### Phase 3: RL agent

- Observation encoder (fixed-size vector) and action mask → verify: round-trip tests.
- Self-play training against a league of past checkpoints and the ISMCTS bot (PPO with action
  masking as the first candidate; Deep CFR / NFSP as alternatives if PPO plateaus) → verify:
  learning curves logged; the agent beats ISMCTS in the arena with a non-overlapping interval,
  or the plan is revisited.
- Versioning: each published model has a version, training summary and arena result vs the
  previous version → verify: `models/registry.json` and a gate script that refuses a model
  that does not beat the incumbent.
- Export to `.npz` and a NumPy forward pass matching PyTorch to 1e-5 → verify: parity test.

Training runs on CPU locally first; RunPod only if CPU proves too slow (price quoted first).

### Phase 4: browser demo

- Visual constraints, decided now and designed later together with the portfolio site:
  - cards are SVG, open licence (CC0/public domain preferred; candidates: Byron Knoll's
    "Vector Playing Cards", David Bellot's SVG-cards, or a custom 24-card deck), licence
    recorded in `web/assets/LICENSES.md`;
  - the UI renders `Observation` and sends `Action`, with no rules in TypeScript;
  - table, palette and motion follow the portfolio's design language.
- Pyodide worker loading the `santase` wheel and the weights → verify: a full game in the
  browser, first-load time measured.
- Opponent picker (all bots and the latest RL version), a developer view that reveals hands
  only after a deal ends, rules screen → verify: Playwright E2E for one full deal.
- Deploy to GitHub Pages from CI → verify: public link works on desktop and mobile.

### Phase 5: repository polish

- README: GIF, live link, architecture diagram, arena table, RL story with versions, how to
  run, the legacy-to-remaster story → verify: Mehmet's review.
- `docs/`: rules, design notes, bot write-ups, results.

### Phase 6: learning loop (after the portfolio site exists)

- The browser posts finished game records to a Cloudflare Worker; the Worker replays each one in
  the engine (Pyodide or a Python Worker) and stores valid ones in D1 → verify: forged or
  illegal records are rejected in tests.
- Weekly Action: pull records, add them to the self-play data, retrain, gate against the
  incumbent, publish if better → verify: one full cycle end to end.
- Public stats: human vs bot win rates, leaderboard, model history.

Expectation set in advance: human games mainly measure the agent and feed the stats page;
the strength itself comes from self-play. The site will say so.

## 6. Risks

| Risk | Mitigation |
|---|---|
| Rule ambiguity across Santase variants | `docs/rules.md` approved before engine work; variant flags only if needed |
| ISMCTS too slow inside Pyodide | time-budgeted search, fewer iterations in the browser, measured in phase 4 |
| PPO struggles in an imperfect-information game | league training, ISMCTS as an anchor opponent, Deep CFR/NFSP fallback |
| Pyodide first load (~10 MB) | load in the background behind the menu; cache with a service worker |
| Abuse of the upload endpoint | replay validation, rate limits, gating means bad data cannot ship a worse model |
| Asset licence | only assets with a recorded open licence enter the repo |

## 7. Open decisions

1. Santase variant details (phase 0, from `docs/rules.md`).
2. Repo name: keep `66-Santase-Game-Against-AI` or rename (for example `santase`); GitHub
   redirects old links after a rename.
3. Card art: existing open deck or a custom one (phase 4).
4. Domain name for the portfolio (before phase 6).
