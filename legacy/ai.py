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

    def should_close_game(self, game_state, hand):
        # For now, always return False (placeholder)
        return False

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

    def should_close_game(self, game_state, hand):
        # For now, always return False (placeholder)
        return False


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

    def should_close_game(self, game_state, hand):  
        # For now, always return False (placeholder)
        return False
    
class MCTS:
    """
    A full Monte Carlo Tree Search (MCTS) AI implementation for Santase.
    It builds a search tree using random playouts to statistically evaluate moves.
    """
    def __init__(self, num_simulations=100, rollout_depth=10):
        self.num_simulations = num_simulations
        self.rollout_depth = rollout_depth
        self.exploration_constant = math.sqrt(2)
        logger.debug("MCTS AI initialized with %d simulations and rollout depth %d", num_simulations, rollout_depth)

    class Node:
        def __init__(self, state, move=None, parent=None):
            self.state = state             # a deep copy of the game state (dictionary)
            self.move = move               # the move (card) that led to this state
            self.parent = parent
            self.children = []
            self.wins = 0.0
            self.visits = 0.0
            self.untried_moves = []        # moves available from this state

        def uct_value(self, exploration_constant):
            if self.visits == 0:
                return float('inf')
            return (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

        def is_fully_expanded(self):
            return len(self.untried_moves) == 0

        def best_child(self, exploration_constant):
            return max(self.children, key=lambda child: child.uct_value(exploration_constant))

    def play(self, game_state, hand):
        """
        Given the current game state and opponent's hand,
        run MCTS simulations and return the chosen card to play.
        """
        # Create the root node; assume game_state reflects the current state.
        root = self.Node(copy.deepcopy(game_state))
        root.untried_moves = self._get_valid_moves(root.state)

        # Run simulations.
        for _ in range(self.num_simulations):
            node = root
            state = copy.deepcopy(game_state)

            # Selection.
            while not self._is_terminal(state) and node.is_fully_expanded() and node.children:
                node = node.best_child(self.exploration_constant)
                state = self._simulate_move(state, node.move, current_turn=True)
            
            # Expansion.
            if not self._is_terminal(state) and node.untried_moves:
                move = random.choice(node.untried_moves)
                state = self._simulate_move(state, move, current_turn=True)
                child_node = self.Node(copy.deepcopy(state), move=move, parent=node)
                child_node.untried_moves = self._get_valid_moves(state)
                node.children.append(child_node)
                node.untried_moves.remove(move)
                node = child_node

            # Rollout.
            reward = self._rollout(state)
            
            # Backpropagation.
            while node is not None:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # Choose the move with the highest visit count.
        if root.children:
            best = max(root.children, key=lambda child: child.visits)
            logger.info("MCTS selected move: %s with %d visits and average reward %.2f", best.move, best.visits, best.wins/best.visits)
            return best.move
        else:
            moves = self._get_valid_moves(game_state)
            chosen = random.choice(moves) if moves else None
            logger.info("MCTS fallback selected move: %s", chosen)
            return chosen

    def should_close_game(self, game_state, hand):
        """
        Decide whether to close the game.
        (A fully developed version might simulate future outcomes.
         For now, we simply return False.)
        """
        return False

    # ------------------- Helper Functions -------------------

    def _sample_possible_player_hand(self, state):
        """
        Constructs a plausible sample for the player's hand using imperfect information.
        It removes known cards from the full deck and then randomly selects a hand.
        """
        full_deck = [(rank, suit) for suit in ["H", "D", "C", "S"] 
                                for rank in ["9", "J", "Q", "K", "10", "A"]]
        known = set()
        # Known cards: opponent's hand, trump card, played cards, and remaining deck.
        for card in state.get("opponent_hand", []):
            known.add(card)
        if state.get("trump_card"):
            known.add(state["trump_card"])
        if state.get("player_played"):
            known.add(state["player_played"])
        if state.get("opponent_played"):
            known.add(state["opponent_played"])
        for card in state.get("remaining_deck", []):
            known.add(card)
        if "player_known_cards" in state:
            known.update(state["player_known_cards"])
        
        unknown = [card for card in full_deck if card not in known]
        
        # Assume the original player's hand size is the length stored in state.
        hand_size = len(state.get("player_hand", []))
        if len(unknown) >= hand_size:
            sampled_hand = random.sample(unknown, hand_size)
        else:
            sampled_hand = unknown  # In extreme cases, if unknown is too short.
        return sampled_hand

    def _get_valid_moves(self, state):
        """Return the valid moves from the opponent's hand based on allowed and trump suit."""
        allowed_suit = state.get("allowed_suit")
        trump_suit = state.get("trump_suit")
        hand = state.get("opponent_hand", [])
        if allowed_suit:
            moves = [card for card in hand if card[1] == allowed_suit]
            if moves:
                return moves
            moves = [card for card in hand if card[1] == trump_suit]
            if moves:
                return moves
        return hand.copy()

    def _get_valid_moves_for_player(self, state):
        """
        Returns valid moves for the player's turn using a sample of unknown cards,
        to simulate imperfect information.
        """
        allowed_suit = state.get("allowed_suit")
        trump_suit = state.get("trump_suit")
        sampled_hand = self._sample_possible_player_hand(state)
        
        if allowed_suit:
            moves = [card for card in sampled_hand if card[1] == allowed_suit]
            if moves:
                return moves
            moves = [card for card in sampled_hand if card[1] == trump_suit]
            if moves:
                return moves
        return sampled_hand.copy()

    def _is_terminal(self, state):
        """A terminal state: when both player and opponent hands are empty."""
        return (len(state.get("player_hand", [])) == 0 and len(state.get("opponent_hand", [])) == 0)

    def _evaluate(self, state):
        """Simple evaluation heuristic: difference in round points (AI - player)."""
        return state.get("opponent_round_points", 0) - state.get("player_round_points", 0)

    def _simulate_move(self, state, move, current_turn=True):
        """
        Simulate applying a move to the current state.
        If current_turn is True, it's the AI's (opponent's) turn;
        otherwise, simulate a player's move.
        This implementation only simulates the move (and updates allowed_suit and leader_card)
        without handling drawing cards or special moves.
        """
        new_state = copy.deepcopy(state)
        if current_turn:
            if move in new_state.get("opponent_hand", []):
                new_state["opponent_hand"].remove(move)
            new_state["opponent_played"] = move
            if new_state.get("player_played") is None:
                new_state["allowed_suit"] = move[1]
                new_state["leader_card"] = move
                new_state["current_leader"] = "opponent"
        else:
            if move in new_state.get("player_hand", []):
                new_state["player_hand"].remove(move)
            new_state["player_played"] = move
            if new_state.get("opponent_played") is None:
                new_state["allowed_suit"] = move[1]
                new_state["leader_card"] = move
                new_state["current_leader"] = "player"
        return new_state

    def _rollout(self, state):
        """
        Perform a random playout (rollout) starting from the given state until a terminal state
        or until a fixed rollout depth is reached.
        Alternates turns between AI and player using random moves.
        For the player's turn, use a sampled hand to avoid perfect information.
        """
        # Determine whose turn it is based on the current leader.
        current_turn = (state.get("current_leader") == "opponent")
        for _ in range(self.rollout_depth):
            if self._is_terminal(state):
                break
            if current_turn:
                valid_moves = self._get_valid_moves(state)
            else:
                valid_moves = self._get_valid_moves_for_player(state)
            if not valid_moves:
                break
            move = random.choice(valid_moves)
            state = self._simulate_move(state, move, current_turn=current_turn)
            current_turn = not current_turn
        return self._evaluate(state)