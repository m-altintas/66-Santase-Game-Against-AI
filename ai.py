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
