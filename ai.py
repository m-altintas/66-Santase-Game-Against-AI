import random

# ---------------------------
# Opponent Class Definition
# ---------------------------
class JustRandom:
    """
    A simple opponent that chooses a card at random.
    Later you can replace this with a more advanced AI.
    """
    def __init__(self):
        pass

    def play(self, game_state, hand):
        """
        Decide on a card to play.
        
        Args:
            game_state (dict): Information about the current state.
            hand (list): List of available cards (each a tuple (rank, suit)).
        
        Returns:
            A card (tuple) chosen from hand, or None if empty.
        """
        if hand:
            index = random.randrange(len(hand))
            return hand.pop(index)
        return None
