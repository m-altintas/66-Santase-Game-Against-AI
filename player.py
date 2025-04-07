from log_config import logger
from ai import JustRandom, TrickBasedGreedy, Expectiminimax

# ---------------------------
# Player Classes Definitions
# ---------------------------
class Player:
    """
    Abstract base class for Player-like objects (Human or AI).
    """
    def __init__(self):
        self.hand = []               # List of cards in hand (tuples, e.g. ("A", "H"))
        self.played_card = None      # Card currently played this trick
        self.won_cards = []          # Cards won over the round
        self.round_points = 0        # Points accumulated in the current round
        self.tricks = 0              # Number of tricks won in the current round
        self.marriages_announced = set()  # Suits for which marriage has been announced
        self.marriage_pending = False     # Flag for a pending marriage action

    def play_card(self, game_state):
        """
        Override in subclasses to define how a card is chosen to play.
        """
        raise NotImplementedError("play_card() must be implemented in a subclass.")

    def announce_marriage(self, selected_card, partner_card):
        """
        Override in subclasses to define how a marriage is announced.
        """
        raise NotImplementedError("announce_marriage() must be implemented in a subclass.")

    def switch_trump(self, current_trump, trump9):
        """
        Override in subclasses to define how the trump switch is handled.
        """
        raise NotImplementedError("switch_trump() must be implemented in a subclass.")


class HumanPlayer(Player):
    def __init__(self):
        super().__init__()
        self.known_cards = set()

    def play_card(self, card_index):
        """
        Removes the card at 'card_index' from the player's hand
        and sets it as 'played_card'.
        """
        try:
            card = self.hand.pop(card_index)
            self.played_card = card
            if card in self.known_cards:
                self.known_cards.remove(card)
            logger.debug("Human played card: %s. Remaining hand: %s", card, self.hand)
            return card
        except Exception as e:
            logger.error("Error in HumanPlayer.play_card: %s", e)
            return None

    def announce_marriage(self, selected_card, partner_card):
        logger.info("Human announces marriage with cards: %s and %s", selected_card, partner_card)

    def switch_trump(self, current_trump, trump9):
        if trump9 in self.hand:
            self.hand.remove(trump9)
            self.hand.append(current_trump)
            self.known_cards.add(current_trump)
            logger.info("Human switched trump with trump9.")
            return trump9
        else:
            logger.warning("Human attempted trump switch but does not have trump9.")
            return None


class AIPlayer(Player):
    def __init__(self, strategy="JustRandom"):
        super().__init__()
        self.strategy = strategy
        logger.info("Initializing AI opponent with strategy: %s", strategy)
        self.ai_logic = None
        self.set_strategy_logic_by_name(strategy)

    def set_strategy_logic_by_name(self, strategy_name):
        """
        Assign an AI logic instance based on the provided strategy name.
        """
        if strategy_name == "JustRandom":
            self.ai_logic = JustRandom()
        elif strategy_name == "TrickBasedGreedy":
            self.ai_logic = TrickBasedGreedy()
        elif strategy_name == "Expectiminimax":
            self.ai_logic = Expectiminimax(max_depth=2, n_player_samples=5)
        else:
            # If an unknown strategy is passed, default to JustRandom
            logger.warning("Unknown AI strategy '%s'. Defaulting to JustRandom.", strategy_name)
            self.ai_logic = JustRandom()

    def set_strategy_logic(self, ai_logic):
        """
        Manually set the AI strategy instance (from ai.py) to use.
        """
        self.ai_logic = ai_logic

    def play_card(self, game_state):
        """
        The AI uses its defined logic to pick a card from its hand.
        """
        # Optional: Could insert additional marriage or trump-switch checks here,
        # but they’re primarily handled in gameplay.py’s AI flow.
        if not self.ai_logic:
            logger.warning("No AI logic set. Defaulting to JustRandom.")
            self.ai_logic = JustRandom()

        card = self.ai_logic.play(game_state, self.hand)
        self.played_card = card
        return card

    def announce_marriage(self, selected_card, partner_card):
        logger.info("AI announces marriage with cards: %s and %s", selected_card, partner_card)
        self.marriages_announced.add(selected_card[1])

    def switch_trump(self, current_trump, trump9):
        if current_trump and trump9 in self.hand:
            self.hand.remove(trump9)
            self.hand.append(current_trump)
            logger.info("AI switches trump: replaced %s with %s", current_trump, trump9)
            return trump9
        logger.warning("AI attempted trump switch but doesn't have trump9 or no trump card is available.")
        return None
