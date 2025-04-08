import copy
import math
import random

from constants import CARD_VALUES
from log_config import logger

class JustRandom:
    """
    A simple AI strategy that selects a random valid move.
    """
    def __init__(self):
        logger.debug("JustRandom AI initialized.")

    def play(self, game_state, hand):
        if not hand:
            logger.warning("JustRandom.play() called with an empty hand.")
            return None

        allowed_suit = game_state.get("allowed_suit")
        trump_suit = game_state.get("trump_suit")

        # Filter valid moves based on allowed suit, if applicable
        if allowed_suit:
            if any(card[1] == allowed_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == allowed_suit]
            elif any(card[1] == trump_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == trump_suit]
            else:
                valid_moves = hand.copy()
        else:
            valid_moves = hand.copy()

        if not valid_moves:
            valid_moves = hand.copy()

        chosen_card = random.choice(valid_moves)
        logger.info("JustRandom selected card %s", chosen_card)
        return chosen_card


class TrickBasedGreedy:
    """
    An AI strategy that tries to win the trick with a high-value approach:
    - If following suit, try to beat the leader’s card if possible.
    - If leading, pick a median-value card to avoid wasting highest cards too early.
    """
    def __init__(self):
        logger.debug("TrickBasedGreedy AI initialized.")

    def play(self, game_state, hand):
        allowed_suit = game_state.get("allowed_suit")
        trump_suit = game_state.get("trump_suit")

        # ----------------
        # Following Mode
        # ----------------
        if allowed_suit:
            if any(card[1] == allowed_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == allowed_suit]
            elif any(card[1] == trump_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == trump_suit]
            else:
                valid_moves = hand.copy()

            leader_card = game_state.get("leader_card")
            winning_moves = []
            losing_moves = []

            for card in valid_moves:
                if leader_card and self.card_wins(card, leader_card, trump_suit, allowed_suit):
                    winning_moves.append(card)
                else:
                    losing_moves.append(card)

            if winning_moves:
                # Pick the highest-value winning card
                best_card = max(winning_moves, key=lambda c: CARD_VALUES[c[0]])
                trick_points = CARD_VALUES[best_card[0]] + CARD_VALUES[leader_card[0]]
                logger.info("TrickBasedGreedy (follow): Winning move %s, trick pts %d", best_card, trick_points)
            else:
                # Dump the lowest-value card
                best_card = min(losing_moves, key=lambda c: CARD_VALUES[c[0]])
                logger.info("TrickBasedGreedy (follow): No winning move; dumping %s", best_card)

            return best_card

        # ----------------
        # Leading Mode
        # ----------------
        else:
            sorted_hand = sorted(hand, key=lambda c: CARD_VALUES[c[0]])
            median_index = len(sorted_hand) // 2
            best_card = sorted_hand[median_index]
            hand.remove(best_card)
            logger.info("TrickBasedGreedy (lead): Leading with median card %s", best_card)
            return best_card

    def card_wins(self, card, leader_card, trump_suit, lead_suit):
        """
        Determine whether 'card' beats 'leader_card'.
        """
        # Trump overrides non-trump
        if card[1] == trump_suit and leader_card[1] != trump_suit:
            return True
        if leader_card[1] == trump_suit and card[1] != trump_suit:
            return False

        # Must follow suit to have a chance
        if card[1] != lead_suit:
            return False

        # Compare values if same suit
        return CARD_VALUES[card[0]] > CARD_VALUES[leader_card[0]]


class Expectiminimax:
    """
    An Expectiminimax-based AI for Santase that models imperfect information
    by sampling possible player hands. It evaluates states by recursively
    exploring the game tree, factoring in chance events when drawing cards.
    """
    def __init__(self, max_depth=40, n_player_samples=100):
        self.max_depth = max_depth
        self.n_player_samples = n_player_samples
        logger.debug("Expectiminimax AI initialized (depth=%d, samples=%d)",
                     max_depth, n_player_samples)

    def play(self, game_state, hand):
        valid_moves = self.get_valid_moves(hand, game_state.get("allowed_suit"), game_state["trump_suit"])
        best_move = None
        best_value = float("-inf")

        for move in valid_moves:
            new_state = self.simulate_move(game_state, move, is_ai_turn=True)
            # If the trick is complete (both cards played), resolve it with chance-based draws
            if new_state["player_played"] and new_state["opponent_played"]:
                value = self.resolve_trick_with_chance(new_state, self.max_depth, is_ai_turn=None)
            else:
                value = self.expectiminimax(new_state, self.max_depth - 1, is_ai_turn=False)

            if value > best_value:
                best_value = value
                best_move = move

        if best_move:
            logger.info("Expectiminimax chose card %s with estimated value %.2f", best_move, best_value)
            return best_move
        else:
            fallback = random.choice(valid_moves)
            logger.info("Expectiminimax fallback move: %s", fallback)
            return fallback

    def expectiminimax(self, state, depth, is_ai_turn):
        if depth == 0 or self.is_terminal(state):
            return self.evaluate(state)

        # If a trick is complete, resolve it before continuing
        if state["player_played"] and state["opponent_played"]:
            return self.resolve_trick_with_chance(state, depth, is_ai_turn)

        if is_ai_turn:
            best_value = float("-inf")
            valid_moves = self.get_valid_moves(state["opponent_hand"], state.get("allowed_suit"), state["trump_suit"])
            if not valid_moves:
                return self.evaluate(state)

            for move in valid_moves:
                new_state = self.simulate_move(state, move, is_ai_turn=True)
                value = self.expectiminimax(new_state, depth - 1, is_ai_turn=False)
                best_value = max(best_value, value)
            return best_value
        else:
            # Player turn: we sample from unknown cards in the deck
            sample_values = []
            for _ in range(self.n_player_samples):
                sampled_hand = self.sample_possible_player_hand(state, len(state["player_hand"]))
                valid_moves = self.get_valid_moves(sampled_hand, state.get("allowed_suit"), state["trump_suit"])
                if not valid_moves:
                    sample_value = self.evaluate(state)
                else:
                    sample_worst = float("inf")
                    for move in valid_moves:
                        new_state = self.simulate_player_move(state, move, sampled_hand)
                        value = self.expectiminimax(new_state, depth - 1, is_ai_turn=True)
                        sample_worst = min(sample_worst, value)
                    sample_value = sample_worst
                sample_values.append(sample_value)

            if sample_values:
                return sum(sample_values) / len(sample_values)
            else:
                return self.evaluate(state)

    def get_valid_moves(self, hand, allowed_suit, trump_suit):
        """
        Return valid moves according to Santase rules for following suit or trumping.
        """
        if allowed_suit:
            moves = [c for c in hand if c[1] == allowed_suit]
            if moves:
                return moves
            moves = [c for c in hand if c[1] == trump_suit]
            if moves:
                return moves
        return hand.copy()

    def simulate_move(self, state, card, is_ai_turn):
        """
        Returns a copy of the state updated with the chosen card (AI or player).
        """
        new_state = copy.deepcopy(state)
        if is_ai_turn:
            if card in new_state["opponent_hand"]:
                new_state["opponent_hand"].remove(card)
            new_state["opponent_played"] = card
            if new_state["player_played"] is None:
                new_state["allowed_suit"] = card[1]
                new_state["leader_card"] = card
                new_state["current_leader"] = "opponent"
        else:
            if card in new_state["player_hand"]:
                new_state["player_hand"].remove(card)
            new_state["player_played"] = card
            if "player_known_cards" in new_state and card in new_state["player_known_cards"]:
                new_state["player_known_cards"].remove(card)
            if new_state["opponent_played"] is None:
                new_state["allowed_suit"] = card[1]
                new_state["leader_card"] = card
                new_state["current_leader"] = "player"
        return new_state

    def simulate_player_move(self, state, card, sampled_hand):
        """
        Similar to simulate_move, but uses a sampled 'player_hand' (for imperfect info).
        """
        new_state = copy.deepcopy(state)
        new_state["player_hand"] = sampled_hand.copy()
        if card in new_state["player_hand"]:
            new_state["player_hand"].remove(card)
        if "player_known_cards" in new_state and card in new_state["player_known_cards"]:
            new_state["player_known_cards"].remove(card)
        new_state["player_played"] = card
        if new_state["opponent_played"] is None:
            new_state["allowed_suit"] = card[1]
            new_state["leader_card"] = card
            new_state["current_leader"] = "player"
        return new_state

    def sample_possible_player_hand(self, state, hand_size):
        """
        Build a plausible player hand from the unknown cards in the deck.
        """
        full_deck = [
            (rank, suit)
            for suit in ["H", "D", "C", "S"]
            for rank in ["9", "J", "Q", "K", "10", "A"]
        ]
        known = set()

        for card in state["opponent_hand"]:
            known.add(card)
        if state.get("trump_card"):
            known.add(state["trump_card"])
        if state.get("player_played"):
            known.add(state["player_played"])
        if state.get("opponent_played"):
            known.add(state["opponent_played"])
        for card in state["remaining_deck"]:
            known.add(card)
        if "player_known_cards" in state:
            known.update(state["player_known_cards"])

        unknown = [card for card in full_deck if card not in known]

        sampled = list(state.get("player_known_cards", []))
        needed = hand_size - len(sampled)
        if needed > 0 and len(unknown) >= needed:
            sampled += random.sample(unknown, needed)
        else:
            sampled += unknown

        return sampled

    def resolve_trick_with_chance(self, state, depth, is_ai_turn):
        """
        Resolve a completed trick by determining a winner, awarding points, and then
        enumerating possible draw outcomes from the deck.
        """
        pcard = state["player_played"]
        ocard = state["opponent_played"]
        trump = state["trump_suit"]

        # Determine trick winner
        if pcard[1] == trump and ocard[1] != trump:
            winner = "player"
        elif ocard[1] == trump and pcard[1] != trump:
            winner = "opponent"
        elif pcard[1] == ocard[1]:
            if CARD_VALUES[pcard[0]] >= CARD_VALUES[ocard[0]]:
                winner = "player"
            else:
                winner = "opponent"
        else:
            # If suits differ and neither is trump, assume leader wins.
            winner = "player"  if state["current_leader"] == "player" else "opponent"

        trick_points = CARD_VALUES[pcard[0]] + CARD_VALUES[ocard[0]]
        new_state = copy.deepcopy(state)
        if winner == "player":
            new_state["player_round_points"] += trick_points
            new_state["current_leader"] = "player"
        else:
            new_state["opponent_round_points"] += trick_points
            new_state["current_leader"] = "opponent"

        new_state["player_played"] = None
        new_state["opponent_played"] = None
        new_state["allowed_suit"] = None
        new_state["leader_card"] = None

        deck = new_state["remaining_deck"]
        if deck:
            n = len(deck)
            if n >= 2:
                outcomes = []
                for i in range(n):
                    for j in range(n):
                        if i == j:
                            continue
                        outcome_state = copy.deepcopy(new_state)
                        card_for_winner = deck[i]
                        card_for_loser = deck[j]
                        outcome_state["remaining_deck"].remove(card_for_winner)
                        outcome_state["remaining_deck"].remove(card_for_loser)

                        if winner == "player":
                            outcome_state["player_hand"].append(card_for_winner)
                            outcome_state["opponent_hand"].append(card_for_loser)
                        else:
                            outcome_state["opponent_hand"].append(card_for_winner)
                            outcome_state["player_hand"].append(card_for_loser)

                        next_is_ai = (outcome_state["current_leader"] == "opponent")
                        outcome_value = self.expectiminimax(outcome_state, depth - 1, is_ai_turn=next_is_ai)
                        outcomes.append(outcome_value)

                return sum(outcomes) / len(outcomes) if outcomes else self.evaluate(new_state)
            else:
                # Only one card left
                outcome_state = copy.deepcopy(new_state)
                card = deck[0]
                outcome_state["remaining_deck"].remove(card)
                if winner == "player":
                    outcome_state["player_hand"].append(card)
                else:
                    outcome_state["opponent_hand"].append(card)
                next_is_ai = (outcome_state["current_leader"] == "opponent")
                return self.expectiminimax(outcome_state, depth - 1, is_ai_turn=next_is_ai)
        else:
            # No cards left to draw
            next_is_ai = (new_state["current_leader"] == "opponent")
            return self.expectiminimax(new_state, depth - 1, is_ai_turn=next_is_ai)

    def is_terminal(self, state):
        """
        Consider the round terminal if both hands are empty.
        """
        return (len(state["player_hand"]) == 0 and len(state["opponent_hand"]) == 0)

    def evaluate(self, state):
        """
        A simple evaluation heuristic: difference in round points
        (AI points - player points).
        """
        return state["opponent_round_points"] - state["player_round_points"]
