import random

from log_config import logger

# ---------------------------
# Opponent Class Definition
# ---------------------------
class JustRandom:
    """
    A simple opponent that now respects follow/trump rules.
    """
    def __init__(self):
        logger.debug("JustRandom AI initialized.")
    
    def play(self, game_state, hand):
        """
        Decide on a card to play using the current game state.
        
        game_state should contain:
          - 'allowed_suit': The suit that was led (if any, e.g. from computer_played).
          - 'trump_suit': The trump suit.
          
        Args:
            game_state (dict): Information about the current state.
            hand (list): List of available cards (each a tuple (rank, suit)).
        
        Returns:
            A card (tuple) chosen from hand, or None if empty.
        """
        
        logger.debug("JustRandom.play() called with game_state: %s", game_state)
        logger.debug("Current hand: %s", hand)
        
        if not hand:
            logger.warning("JustRandom.play() called with an empty hand.")
            return None
        
        allowed_suit = game_state.get("allowed_suit")
        trump_suit = game_state.get("trump_suit")
        valid_moves = []

        if allowed_suit:
            has_follow = any(card[1] == allowed_suit for card in hand)
            has_trump = any(card[1] == trump_suit for card in hand)
            
            if has_follow and has_trump:
                # Valid moves: cards that are either of the led suit or trump.
                valid_moves = [card for card in hand if card[1] == allowed_suit or card[1] == trump_suit]
            elif has_follow:
                valid_moves = [card for card in hand if card[1] == allowed_suit]
            elif has_trump:
                valid_moves = [card for card in hand if card[1] == trump_suit]
            else:
                valid_moves = hand.copy()
        else:
            # If no allowed suit is defined (e.g. the computer is leading), any card is allowed.
            valid_moves = hand.copy()
        
        # Fallback: if valid_moves is empty for some reason, use the full hand.
        if not valid_moves:
            valid_moves = hand.copy()
        
        # Choose a card at random from the valid moves.
        index = random.randrange(len(valid_moves))
        chosen_card = valid_moves[index]
        # Remove the chosen card from the hand.
        hand.remove(chosen_card)
        
        logger.info("JustRandom selected card %s at index %d", chosen_card, index)
        return chosen_card

class TrickBasedGreedy:
    """
    An opponent that keeps track of played cards and uses a simple heuristic to decide moves.
    
    - When following: it considers the leader's card (passed in game_state as "leader_card")
      and selects, among valid moves, the card that maximizes the trick's point gain.
    
    - When leading: it picks the highest value card (based on CARD_VALUES) from its hand.
    
    Memory of past tricks is stored in self.seen_cards.
    """
    def __init__(self):
        self.seen_cards = []  # Cards seen in past tricks
        self.known_player_cards = {}  # Tracks cards known to be in the player's hand

    def update_memory(self, played_cards):
        """
        Update memory with a list of cards from the completed trick.
        Also, automatically remove any known player cards if they have been played.
        """
        for card in played_cards:
            if card not in self.seen_cards:
                self.seen_cards.append(card)
            # If the card is marked as known in the player's hand, remove it.
            if card in self.known_player_cards:
                del self.known_player_cards[card]
                
    def note_trump_switch(self, old_trump_card):
        # When a trump switch happens, record that this card is now in player's hand.
        self.known_player_cards[old_trump_card] = True

    def note_marriage(self, card1, card2):
        # Record both cards from the marriage as known.
        self.known_player_cards[card1] = True
        self.known_player_cards[card2] = True

    def play(self, game_state, hand):
        """
        Decide on a card to play.
        
        Args:
            game_state (dict): Contains keys:
                - "allowed_suit": The suit that must be followed (if any).
                - "trump_suit": The trump suit.
                - "leader_card": (Optional) The card played by the leader.
            hand (list): List of available cards (tuples like ("A", "H")).
        
        Returns:
            A chosen card (tuple) from hand.
        """
        allowed_suit = game_state.get("allowed_suit")
        trump_suit = game_state.get("trump_suit")
        
        # If following (i.e. allowed_suit is defined), try to win the trick.
        if allowed_suit:
            # Determine valid moves (following suit if possible, otherwise trump if possible).
            if any(card[1] == allowed_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == allowed_suit]
            elif any(card[1] == trump_suit for card in hand):
                valid_moves = [card for card in hand if card[1] == trump_suit]
            else:
                valid_moves = hand.copy()
            
            # Use a simple heuristic: if the leader's card is known, choose the valid move
            # that wins the trick and maximizes the combined point value.
            leader_card = game_state.get("leader_card")
            best_score = -1
            best_card = valid_moves[0]
            from constants import CARD_VALUES
            for card in valid_moves:
                score = 0
                if leader_card:
                    if self.card_wins(card, leader_card, trump_suit, allowed_suit):
                        # Score: sum of point values of leader's and candidate card.
                        score = CARD_VALUES[card[0]] + CARD_VALUES[leader_card[0]]
                    else:
                        score = 0
                else:
                    # Fallback: simply use the card's own value.
                    score = CARD_VALUES[card[0]]
                if score > best_score:
                    best_score = score
                    best_card = card
            hand.remove(best_card)
            return best_card
        else:
            # If leading, choose the highest value card from hand.
            from constants import CARD_VALUES
            best_card = max(hand, key=lambda c: CARD_VALUES[c[0]])
            hand.remove(best_card)
            return best_card

    def card_wins(self, card, leader_card, trump_suit, lead_suit):
        """
        Returns True if 'card' beats the leader's card based on:
         - Trump rules: trump beats non-trump.
         - Following suit: if both follow suit, higher CARD_VALUES wins.
         - Otherwise, the card loses.
        """
        from constants import CARD_VALUES
        # If card is trump and leader_card is not trump, card wins.
        if card[1] == trump_suit and leader_card[1] != trump_suit:
            return True
        # If both cards are of the same suit (whether trump or lead), compare point values.
        if card[1] == leader_card[1]:
            return CARD_VALUES[card[0]] > CARD_VALUES[leader_card[0]]
        # If card does not follow suit, it loses.
        return False