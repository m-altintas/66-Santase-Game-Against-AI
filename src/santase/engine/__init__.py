"""Rules engine. Implements docs/rules.md; nothing outside this package sees hidden state."""

from santase.engine.actions import Action, Announce, Close, Declare, Exchange, Play, parse_action
from santase.engine.cards import FULL_DECK, Card, Rank, Suit, cards
from santase.engine.deal import deal_from_order, new_deal, shuffled_deck
from santase.engine.match import MatchState, match_step, new_match
from santase.engine.observation import Observation, observe
from santase.engine.rules import IllegalActionError, legal_actions, step
from santase.engine.state import DealOutcome, DealState, EndReason

RULES_VERSION = 1

__all__ = [
    "FULL_DECK",
    "RULES_VERSION",
    "Action",
    "Announce",
    "Card",
    "Close",
    "DealOutcome",
    "DealState",
    "Declare",
    "EndReason",
    "Exchange",
    "IllegalActionError",
    "MatchState",
    "Observation",
    "Play",
    "Rank",
    "Suit",
    "cards",
    "deal_from_order",
    "legal_actions",
    "match_step",
    "new_deal",
    "new_match",
    "observe",
    "parse_action",
    "shuffled_deck",
    "step",
]
