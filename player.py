from log_config import logger
from ai import JustRandom, TrickBasedGreedy, Expectiminimax

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
        self.known_cards = set()

    def play_card(self, card_index):
        """
        For the human, the UI passes a card index.
        This method removes that card from hand and sets it as the played card.
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
        self.ai_logic = None  # Will be set by the game engine (or via set_strategy_logic)
        if strategy == "JustRandom":
            self.set_strategy_logic(JustRandom())
        elif strategy == "TrickBasedGreedy":
            self.set_strategy_logic(TrickBasedGreedy())
        elif strategy == "Expectiminimax":
            self.set_strategy_logic(Expectiminimax(max_depth=2, n_player_samples=5))

    def set_strategy_logic(self, ai_logic):
        """
        Set the AI strategy instance (from ai.py) that will be used.
        """
        self.ai_logic = ai_logic

    def play_card(self, game_state):
        # --- Check for possible marriage announcement ---
        for suit in ["H", "D", "C", "S"]:
            king = ("K", suit)
            queen = ("Q", suit)
            # If both King and Queen of the same suit are in hand and marriage not yet announced:
            if king in self.hand and queen in self.hand and suit not in self.marriages_announced:
                self.announce_marriage(king, queen)
                # (Optionally, you can decide whether to immediately return
                # or let the AI also select a card to play in this trick.)
                break

        # --- Check for possible trump switch ---
        trump_suit = game_state.get("trump_suit")
        # If AI is leading (i.e. current_leader == "opponent") and holds the trump 9:
        if game_state.get("current_leader") == "opponent":
            trump9 = ("9", trump_suit)
            if trump9 in self.hand:
                self.switch_trump(game_state.get("trump_card"), trump9)

        # --- Proceed with normal move selection ---
        card = self.ai_logic.play(game_state, self.hand)
        self.played_card = card
        return card

    def announce_marriage(self, selected_card, partner_card):
        logger.info("AI announces marriage with cards: %s and %s", selected_card, partner_card)
        # Mark the suit as announced so we don't repeat
        self.marriages_announced.add(selected_card[1])

    def switch_trump(self, current_trump, trump9):
        if trump9 in self.hand:
            self.hand.remove(trump9)
            self.hand.append(current_trump)
            logger.info("AI switches trump: replaced trump card %s with trump9 %s", current_trump, trump9)
            return trump9
        else:
            logger.warning("AI attempted trump switch but does not have trump9.")
            return None
