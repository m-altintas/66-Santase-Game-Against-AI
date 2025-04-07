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

        # Filter valid moves based on allowed suit, if applicable.
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

        index = random.randrange(len(valid_moves))
        chosen_card = valid_moves[index]
        hand.remove(chosen_card)
        logger.info("JustRandom selected card %s", chosen_card)
        return chosen_card

class TrickBasedGreedy:
    """
    An AI strategy that tries to win the trick with maximum point gain.
    It keeps track of cards seen and certain known cards from the opponent's actions.
    """
    def __init__(self):
        self.seen_cards = []           # List of all cards seen in past tricks.
        self.known_player_cards = {}   # Cards known to be in the opponent's hand.
        logger.debug("TrickBasedGreedy AI initialized.")

    def update_memory(self, played_cards):
        """
        Update the memory with cards played in the trick.
        Also automatically remove any known cards if they have been played.
        """
        for card in played_cards:
            if card not in self.seen_cards:
                self.seen_cards.append(card)
            if card in self.known_player_cards:
                del self.known_player_cards[card]

    def note_trump_switch(self, old_trump_card):
        """
        When the opponent performs a trump switch, record that the old trump card is in their hand.
        """
        self.known_player_cards[old_trump_card] = True
        logger.debug("Noted trump switch: %s", old_trump_card)

    def note_marriage(self, card1, card2):
        """
        Record that the two cards used in a marriage are known to be in the opponent's hand.
        """
        self.known_player_cards[card1] = True
        self.known_player_cards[card2] = True
        logger.debug("Noted marriage: %s and %s", card1, card2)

    def play(self, game_state, hand):
        allowed_suit = game_state.get("allowed_suit")
        trump_suit = game_state.get("trump_suit")
        
        # --- Following Mode ---
        if allowed_suit:
            # Determine valid moves: must follow suit if possible; if not, use trump if available.
            if any(card[1] == allowed_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == allowed_suit]
            elif any(card[1] == trump_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == trump_suit]
            else:
                valid_moves = hand.copy()
                
            leader_card = game_state.get("leader_card")
            
            # Partition valid moves into winning and losing moves.
            winning_moves = []
            losing_moves = []
            for card in valid_moves:
                if leader_card and self.card_wins(card, leader_card, trump_suit, allowed_suit):
                    winning_moves.append(card)
                else:
                    losing_moves.append(card)
                    
            if winning_moves:
                # If a winning move exists, choose the one that maximizes trick points.
                # (Since the leader's card value is constant, we choose the highest-value card among winning moves.)
                best_card = max(winning_moves, key=lambda card: CARD_VALUES[card[0]])
                trick_points = CARD_VALUES[best_card[0]] + CARD_VALUES[leader_card[0]]
                logger.info("TrickBasedGreedy (follow): Winning move selected %s with trick points %d", best_card, trick_points)
            else:
                # No winning move—dump the lowest-value card.
                best_card = min(losing_moves, key=lambda card: CARD_VALUES[card[0]])
                logger.info("TrickBasedGreedy (follow): No winning move; dumping lowest card %s", best_card)
                
            hand.remove(best_card)
            return best_card
        
        # --- Leading Mode ---
        else:
            # Instead of always playing the highest card, lead with the median-value card to avoid wasting your best cards.
            sorted_hand = sorted(hand, key=lambda card: CARD_VALUES[card[0]])
            median_index = len(sorted_hand) // 2
            best_card = sorted_hand[median_index]
            hand.remove(best_card)
            logger.info("TrickBasedGreedy (lead): Leading with median card %s", best_card)
            return best_card

    def card_wins(self, card, leader_card, trump_suit, lead_suit):
        """
        Determine whether 'card' beats 'leader_card' under current rules.
        """
        # Trump rule: trump beats non-trump.
        if card[1] == trump_suit and leader_card[1] != trump_suit:
            return True
        if leader_card[1] == trump_suit and card[1] != trump_suit:
            return False
        # If both are of the same suit (whether lead or trump), compare point values.
        if card[1] == leader_card[1]:
            return CARD_VALUES[card[0]] > CARD_VALUES[leader_card[0]]
        # Otherwise, if card is not following the lead, assume it loses.
        return False
    
class Expectiminimax:
    """
    An Expectiminimax-based AI for Santase that models imperfect information 
    by sampling possible player hands instead of using the known player_hand state.
    """

    def __init__(self, max_depth=40, n_player_samples=100):
        self.max_depth = max_depth
        self.n_player_samples = n_player_samples  # Number of samples for player's unknown hand.
        logger.debug("Expectiminimax AI initialized with depth %d and %d player samples.", 
                     self.max_depth, self.n_player_samples)

    def play(self, game_state, hand):
        """
        Chooses a card to play from the AI's hand.
        """
        valid_moves = self.get_valid_moves(hand, game_state.get("allowed_suit"), game_state["trump_suit"])
        best_move = None
        best_value = float("-inf")
        for move in valid_moves:
            new_state = self.simulate_move(game_state, move, is_ai_turn=True)
            # If the trick is complete, resolve it including chance draws.
            if new_state["player_played"] is not None and new_state["opponent_played"] is not None:
                value = self.resolve_trick_with_chance(new_state, self.max_depth, is_ai_turn=None)
            else:
                # Next turn is assumed to be the player's turn.
                value = self.expectiminimax(new_state, self.max_depth - 1, is_ai_turn=False)
            if value > best_value:
                best_value = value
                best_move = move
        if best_move:
            hand.remove(best_move)
            logger.info("Expectiminimax chose card %s with estimated value %.2f", best_move, best_value)
            return best_move
        else:
            chosen = random.choice(valid_moves)
            hand.remove(chosen)
            logger.info("Expectiminimax fallback move: %s", chosen)
            return chosen

    def expectiminimax(self, state, depth, is_ai_turn):
        """
        Recursively evaluate the state using Expectiminimax.
        When it's the player's turn (minimization branch), we sample possible player hands.
        """
        if depth == 0 or self.is_terminal(state):
            return self.evaluate(state)
        
        # If a trick is complete, resolve it via chance draws.
        if state["player_played"] is not None and state["opponent_played"] is not None:
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
            # For the player's turn, we don't use the actual state["player_hand"].
            # Instead, we sample possible hands from the unknown cards.
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
            worst_value = sum(sample_values) / len(sample_values) if sample_values else self.evaluate(state)
            return worst_value

    def get_valid_moves(self, hand, allowed_suit, trump_suit):
        """
        Return valid moves for the given hand according to Santase rules.
        """
        if allowed_suit:
            moves = [card for card in hand if card[1] == allowed_suit]
            if moves:
                return moves
            moves = [card for card in hand if card[1] == trump_suit]
            if moves:
                return moves
        return hand.copy()

    def simulate_move(self, state, card, is_ai_turn):
        """
        Simulate playing a card by the AI.
        Returns a deep copy of the state updated with the played card.
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
            # NEW: Remove the played card from the known set.
            if "player_known_cards" in new_state and card in new_state["player_known_cards"]:
                new_state["player_known_cards"].remove(card)
            if new_state["opponent_played"] is None:
                new_state["allowed_suit"] = card[1]
                new_state["leader_card"] = card
                new_state["current_leader"] = "player"
        return new_state

    def simulate_player_move(self, state, card, sampled_hand):
        """
        Simulate a player's move using a sampled hand.
        Returns a deep copy of the state where state["player_hand"] is replaced by the sampled hand.
        """
        new_state = copy.deepcopy(state)
        new_state["player_hand"] = sampled_hand.copy()
        if card in new_state["player_hand"]:
            new_state["player_hand"].remove(card)
        # NEW: Remove the played card from the known cards, if present.
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
        Sample a plausible player hand of size hand_size from the unknown cards.
        The unknown cards are those not visible in the opponent's hand, the trump,
        played cards, the remaining deck, and not already known to be in the player's hand.
        The sampled hand always includes the known cards.
        """
        full_deck = [(rank, suit) for suit in ["H", "D", "C", "S"] for rank in ["9", "J", "Q", "K", "10", "A"]]
        
        # Build the set of known cards.
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
        
        # Also include cards that our memory says the player definitely has.
        player_known = set(state.get("player_known_cards", []))
        known.update(player_known)

        # Unknown pool: cards not seen anywhere.
        unknown = [card for card in full_deck if card not in known]

        # Start the sampled hand with the known cards.
        sampled = list(player_known)
        remaining_needed = hand_size - len(sampled)
        if remaining_needed > 0 and len(unknown) >= remaining_needed:
            sampled += random.sample(unknown, remaining_needed)
        elif remaining_needed > 0:
            # Fallback in case there aren't enough unknown cards.
            sampled += unknown

        return sampled

    def resolve_trick_with_chance(self, state, depth, is_ai_turn):
        """
        Resolve a completed trick (both players have played a card) and then handle the chance
        event for drawing cards from the deck by enumerating all possible draw outcomes.
        Returns the expected value over these outcomes.
        """
        pcard = state["player_played"]
        ocard = state["opponent_played"]
        trump = state["trump_suit"]
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
            winner = "player"
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
        outcomes = []
        if deck:
            n = len(deck)
            if n >= 2:
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
                        next_is_ai_turn = (outcome_state["current_leader"] == "opponent")
                        outcome_value = self.expectiminimax(outcome_state, depth - 1, is_ai_turn=next_is_ai_turn)
                        outcomes.append(outcome_value)
                total_outcomes = len(outcomes)
                expected_value = sum(outcomes) / total_outcomes if total_outcomes > 0 else self.evaluate(new_state)
                return expected_value
            else:
                outcome_state = copy.deepcopy(new_state)
                card = deck[0]
                outcome_state["remaining_deck"].remove(card)
                if winner == "player":
                    outcome_state["player_hand"].append(card)
                else:
                    outcome_state["opponent_hand"].append(card)
                next_is_ai_turn = (outcome_state["current_leader"] == "opponent")
                return self.expectiminimax(outcome_state, depth - 1, is_ai_turn=next_is_ai_turn)
        else:
            next_is_ai_turn = (new_state["current_leader"] == "opponent")
            return self.expectiminimax(new_state, depth - 1, is_ai_turn=next_is_ai_turn)

    def is_terminal(self, state):
        """
        Determine whether the round is over.
        For this implementation, we consider the round over when both hands are empty.
        """
        return (len(state["player_hand"]) == 0 and len(state["opponent_hand"]) == 0)

    def evaluate(self, state):
        """
        A simple heuristic evaluation function.
        Returns the difference between the opponent's and player's round points.
        """
        return state["opponent_round_points"] - state["player_round_points"]