import random

# ---------------------------
# Opponent Class Definition
# ---------------------------
class JustRandom:
    """
    A simple opponent that now respects follow/trump rules.
    """
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
        return chosen_card
