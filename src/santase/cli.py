"""Play Santase in the terminal against a simple opponent (phase 1 check).

The opponent plays random legal cards and declares "out" when its own count reaches 66.
Scores are never shown during a deal (rules R8.1, R8.1b).
"""

from __future__ import annotations

import argparse
import random

from santase.engine import (
    Action,
    Announce,
    Card,
    Close,
    Declare,
    Exchange,
    MatchState,
    Observation,
    Play,
    match_step,
    new_match,
    observe,
    step,
)
from santase.engine.observation import count_points
from santase.engine.state import (
    CardPlayed,
    Event,
    MarriageAnnounced,
    OutDeclared,
    TalonClosed,
    TrickTaken,
    TrumpCardTaken,
    TrumpExchanged,
)

HUMAN, BOT = 0, 1
SUIT_SYMBOLS = "♣♦♥♠"
NAMES = {HUMAN: "You", BOT: "Bot"}


def show(card: Card) -> str:
    return f"{card.rank.label}{SUIT_SYMBOLS[card.suit]}"


def describe(action: Action) -> str:
    match action:
        case Play(card=card):
            return show(card)
        case Announce(suit=suit):
            return f"announce marriage in {SUIT_SYMBOLS[suit]}"
        case Exchange():
            return "exchange the 9 of trumps"
        case Close():
            return "close the talon"
        case Declare():
            return 'declare "out" (66)'


def narrate(event: Event) -> str | None:
    match event:
        case CardPlayed(player=p, card=card):
            return f"{NAMES[p]} played {show(card)}"
        case TrickTaken(winner=p):
            return f"{NAMES[p]} took the trick"
        case MarriageAnnounced(player=p, suit=suit, points=points):
            return f"{NAMES[p]} announced {points} in {SUIT_SYMBOLS[suit]}"
        case TrumpExchanged(player=p, taken=taken):
            return f"{NAMES[p]} exchanged the 9 for {show(taken)}"
        case TalonClosed(player=p):
            return f"{NAMES[p]} closed the talon"
        case TrumpCardTaken(player=p, card=card):
            return f"{NAMES[p]} took the trump card {show(card)}"
        case OutDeclared(player=p):
            return f'{NAMES[p]} declared "out"'
        case _:
            return None


def bot_action(obs: Observation, rng: random.Random) -> Action:
    if Declare() in obs.legal_actions and count_points(obs.history, obs.player) >= 66:
        return Declare()
    return rng.choice([a for a in obs.legal_actions if a != Declare()])


def ask(obs: Observation) -> Action:
    trump = show(obs.trump_card) if obs.trump_card else f"{SUIT_SYMBOLS[obs.trump_suit]} (closed)"
    print(
        f"\nTrump {trump} | talon {obs.talon_size} | your hand: "
        + " ".join(show(c) for c in obs.hand)
    )
    if obs.trick:
        print(f"On the table: {show(obs.trick[0])}")
    for index, action in enumerate(obs.legal_actions, 1):
        print(f"  {index}. {describe(action)}")
    while True:
        answer = input("> ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(obs.legal_actions):
            return obs.legal_actions[int(answer) - 1]
        print(f"Pick a number from 1 to {len(obs.legal_actions)}.")


def play(seed: int, target: int) -> MatchState:
    rng = random.Random(f"bot:{seed}")
    match = new_match(seed, target)
    seen = 0
    while not match.is_over:
        deal = match.deal
        for event in deal.history[seen:]:
            line = narrate(event)
            if line:
                print(line)
        seen = len(deal.history)
        obs = observe(deal, deal.turn)
        action = ask(obs) if deal.turn == HUMAN else bot_action(obs, rng)
        before = match.deal_index
        finished = step(deal, action)
        match = match_step(match, action)
        if match.deal_index != before or match.is_over:
            for event in finished.history[seen:]:
                line = narrate(event)
                if line:
                    print(line)
            outcome = match.last_outcome
            assert outcome is not None
            who = "Nobody" if outcome.winner is None else NAMES[outcome.winner]
            print(
                f"\n== Deal over: {who} +{outcome.game_points} ({outcome.reason.value}); "
                f"card points you {outcome.card_points[HUMAN]}, bot {outcome.card_points[BOT]}. "
                f"Match {match.scores[HUMAN]}:{match.scores[BOT]} =="
            )
            seen = 0
    print("\nYou won the match!" if match.winner == HUMAN else "\nThe bot won the match.")
    return match


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Santase (66) in the terminal.")
    parser.add_argument("--seed", type=int, default=random.randrange(2**31))
    parser.add_argument("--target", type=int, default=11)
    args = parser.parse_args()
    print(f"Seed {args.seed}. You are player 0.")
    play(args.seed, args.target)


if __name__ == "__main__":
    main()
