from log_config import logger
from ai import JustRandom, TrickBasedGreedy

# ---------------------------
# Player Classes Definitions
# ---------------------------
class Player:
    def __init__(self):
        self.hand = []             # List of cards in hand (tuples, e.g. ("A", "H"))
        self.played_card = None    # The card currently played this trick
        self.won_cards = []        # Cards won over the round
        self.round_points = 0      # Points accumulated in the current round
        self.tricks = 0            # Number of tricks won in the current round
        self.marriages_announced = set()  # Suits for which marriage has been announced
        self.marriage_pending = False     # Flag for pending marriage action

    def play_card(self, game_state):
        """
        This method should be overridden in subclasses.
        For HumanPlayer, it will use a card index from UI input.
        For AIPlayer, it will use an AI strategy.
        """
        raise NotImplementedError("play_card() must be implemented in a subclass.")

    def announce_marriage(self, selected_card, partner_card):
        """
        Process marriage announcement.
        Actual point awarding and further logic will be handled by the game engine.
        """
        raise NotImplementedError("announce_marriage() must be implemented in a subclass.")

    def switch_trump(self, current_trump, trump9):
        """
        Process trump switch.
        """
        raise NotImplementedError("switch_trump() must be implemented in a subclass.")


class HumanPlayer(Player):
    def __init__(self):
        super().__init__()

    def play_card(self, card_index):
        """
        For the human, the UI passes a card index.
        This method removes that card from hand and sets it as the played card.
        """
        try:
            card = self.hand.pop(card_index)
            self.played_card = card
            logger.debug("Human played card: %s. Remaining hand: %s", card, self.hand)
            return card
        except Exception as e:
            logger.error("Error in HumanPlayer.play_card: %s", e)
            return None

    def announce_marriage(self, selected_card, partner_card):
        """
        When the human announces a marriage via UI,
        the game engine will then award points.
        """
        logger.info("Human announces marriage with cards: %s and %s", selected_card, partner_card)
        # Further processing (e.g. points) is handled by the game engine.
        return

    def switch_trump(self, current_trump, trump9):
        """
        Attempt to switch trump.
        If trump9 is in hand, remove it and replace the trump announcement.
        """
        if trump9 in self.hand:
            self.hand.remove(trump9)
            self.hand.append(current_trump)
            logger.info("Human switched trump with trump9.")
            return trump9
        else:
            logger.warning("Human attempted trump switch but does not have trump9.")
            return None


class AIPlayer(Player):
    def __init__(self, strategy="JustRandom"):
        super().__init__()
        self.strategy = strategy
        self.ai_logic = None  # Will be set by the game engine (or via set_strategy_logic)
        if strategy == "JustRandom":
            self.set_strategy_logic(JustRandom())
        elif strategy == "TrickBasedGreedy":
            self.set_strategy_logic(TrickBasedGreedy())

    def set_strategy_logic(self, ai_logic):
        """
        Set the AI strategy instance (from ai.py) that will be used.
        """
        self.ai_logic = ai_logic

    def play_card(self, game_state):
        """
        Uses the assigned AI strategy to pick a card.
        """
        if self.ai_logic is None:
            raise ValueError("AI logic is not set for AIPlayer.")
        card = self.ai_logic.play(game_state, self.hand)
        self.played_card = card
        logger.debug("AI played card: %s. Remaining hand: %s", card, self.hand)
        return card

    def announce_marriage(self, selected_card, partner_card):
        """
        Implement AI marriage strategy if desired.
        For now, just log the action.
        """
        logger.debug("AI announces marriage with cards: %s and %s", selected_card, partner_card)
        return

    def switch_trump(self, current_trump, trump9):
        """
        Implement AI trump switch strategy if desired.
        For now, no switch is performed.
        """
        logger.debug("AI attempts trump switch with trump9: %s", trump9)
        return None
