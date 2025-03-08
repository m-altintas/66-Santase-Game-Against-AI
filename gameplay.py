import pygame
import random
import math

from constants import CARD_HEIGHT, CARD_WIDTH, CARD_SPACING, MARGIN, CARD_VALUES, MARRIAGE_DONE_EVENT
from ui import Button
from ai import JustRandom
from log_config import logger
from utils import resource_path

# ---------------------------
# GamePlay Class Definition (Revised Rules & Draw Modification)
# ---------------------------
class GamePlay:
    def __init__(self, screen, end_game_callback):
        logger.info("Initializing GamePlay.")
        self.end_game_callback = end_game_callback
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        logger.debug("Screen dimensions: %d x %d", self.screen_width, self.screen_height)

        # Load background image (or fallback)
        try:
            self.background = pygame.image.load(resource_path("assets/backgrounds/game_background.jpg"))
            self.background = pygame.transform.scale(self.background, (self.screen_width, self.screen_height))
            logger.info("Background image loaded and scaled.")
        except Exception as e:
            logger.error("Error loading background image: %s", e)
            self.background = pygame.Surface((self.screen_width, self.screen_height))
            self.background.fill((0, 128, 0))

        # Load card back image.
        try:
            self.card_back = pygame.image.load(resource_path("assets/cards/back.png"))
            self.card_back = pygame.transform.scale(self.card_back, (CARD_WIDTH, CARD_HEIGHT))
            logger.info("Card back image loaded.")
        except Exception as e:
            logger.error("Error loading card back: %s", e)
            self.card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.card_back.fill((0, 0, 128))

        # Load card images.
        self.card_images = {}
        self.ranks = ["9", "J", "Q", "K", "10", "A"]
        self.suits = ["H", "D", "C", "S"]
        for suit in self.suits:
            for rank in self.ranks:
                filename = f"assets/cards/{rank}{suit}.png"
                try:
                    img = pygame.image.load(resource_path(filename))
                    img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                    self.card_images[(rank, suit)] = img
                except Exception as e:
                    logger.error("Error loading %s: %s", filename, e)
                    placeholder = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                    placeholder.fill((200, 200, 200))
                    self.card_images[(rank, suit)] = placeholder
        logger.info("Card images loaded.")

        # Build a 24-card deck.
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        logger.debug("Deck built and shuffled with %d cards.", len(self.deck))

        # Deal cards in two rounds of 3 cards each.
        self.player_hand = [self.deck.pop() for _ in range(3)]
        self.computer_hand = [self.deck.pop() for _ in range(3)]
        self.player_hand += [self.deck.pop() for _ in range(3)]
        self.computer_hand += [self.deck.pop() for _ in range(3)]
        logger.debug("Player hand: %s", self.player_hand)
        logger.debug("Computer hand: %s", self.computer_hand)

        # Reveal trump card.
        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None
        logger.info("Trump card revealed: %s", self.trump_card)

        # Played cards for the current trick.
        self.player_played = None
        self.computer_played = None

        # Phase and trick state.
        self.trick_ready = False
        self.first_phase = True  # True when drawing from deck is active.
        # Who leads the trick: "player" or "computer".
        self.current_leader = "player"  # Initially, player leads.

        # Round (trick) points and counts.
        self.player_round_points = 0
        self.computer_round_points = 0
        self.player_tricks = 0
        self.computer_tricks = 0

        # Overall game points.
        self.player_game_points = 0
        self.computer_game_points = 0
        
        # Add a flag to indicate that an animation is ongoing.
        self.ongoing_animation = False
        
        self.marriage_pending = False       # Waiting for human to select a card for marriage
        self.marriage_announcement = None     # Will hold a tuple of the two cards forming the marriage
        self.marriage_time = None             # Timestamp when marriage was announced
        self.player_marriages_announced = set()      # A set of suits already announced by the human.
        self.computer_marriages_announced = set()    # A set of suits already announced by the computer.
        self.computer_marriage_processed = False  # Temporary flag for the current trick
        
        self.player_won_cards = []
        self.computer_won_cards = []
        
        self.game_closed = False

        # Feedback message.
        self.message = "Your turn to lead."

        # Create the opponent instance.
        self.opponent = JustRandom()

        self.zones = self.init_zones()

        # Close button for Zone K.
        self.close_button = Button(self.zones['K'], "Close", self.close_game, pygame.font.SysFont('Arial', 20))
        self.switch_button = Button(self.zones['L'], "Switch", self.switch_trump, pygame.font.SysFont('Arial', 20))
        self.marriage_button = Button(self.zones['M'], "Marriage", self.announce_marriage, pygame.font.SysFont('Arial', 20))
        
        # Variables for shake animation
        self.shake_card_index = None   # The index of the card to shake (if any)
        self.shake_start_time = 0        # When the shake started (in milliseconds)
        self.shake_duration = 500        # Duration of the shake animation in milliseconds
        
        pause_button_rect = pygame.Rect(self.screen_width - MARGIN - 100, MARGIN, 100, 40)
        self.pause_button = Button(pause_button_rect, "Pause", self.pause_game, pygame.font.SysFont('Arial', 20))
        
        logger.info("GamePlay initialized successfully.")

    def init_zones(self):
        zones = {}
        zones['A'] = pygame.Rect(MARGIN, MARGIN, self.screen_width - 2 * MARGIN, 150)
        zones['B'] = pygame.Rect(MARGIN, self.screen_height - MARGIN - 150, self.screen_width - 2 * MARGIN, 150)
        zones['C'] = pygame.Rect(390, 260, 500, 200)
        zones['D'] = pygame.Rect(zones['C'].x, zones['C'].y, zones['C'].width // 2, zones['C'].height)
        zones['E'] = pygame.Rect(zones['C'].x + zones['C'].width // 2, zones['C'].y, zones['C'].width // 2, zones['C'].height)
        zones['F'] = pygame.Rect(zones['C'].right + 10, zones['C'].y + (zones['C'].height - 50) // 2, 100, 50)
        group_height = 150
        group_y = (self.screen_height - group_height) // 2
        zones['I'] = pygame.Rect(MARGIN, group_y, 100, 150)
        zones['H'] = pygame.Rect(MARGIN + 100 + 10, group_y, 100, 150)
        zones['T'] = pygame.Rect(zones['H'].right + 10, zones['H'].y + (zones['H'].height // 2) - 20, 150, 40)
        zones['J'] = pygame.Rect(MARGIN, zones['B'].y - 70, 80, 40)
        zones['K'] = pygame.Rect(MARGIN, zones['J'].bottom + 10, 80, 40)
        zones['L'] = pygame.Rect(zones['J'].right + 10, zones['J'].y, 80, 40)
        zones['M'] = pygame.Rect(zones['L'].x, zones['L'].bottom + 10, 80, 40)
        zones['G'] = pygame.Rect(self.screen_width - MARGIN - 100, zones['B'].y - 70, 100, 40)
        zones['OG'] = pygame.Rect(self.screen_width - MARGIN - 100, zones['G'].y - 50, 100, 40)
        zones['W'] = pygame.Rect(self.screen_width - MARGIN - 200, zones['B'].y, 180, 150)
        return zones

    def get_game_state(self):
        """
        Return a dictionary with current game state details.
        """
        state = {
            "player_played": self.player_played,
            "player_round_points": self.player_round_points,
            "computer_round_points": self.computer_round_points,
            "remaining_deck": self.deck.copy(),
            "trump_card": self.trump_card,
            "trump_suit": self.trump_suit,
            "computer_hand": self.computer_hand.copy(),
            "player_hand": self.player_hand.copy(),
            "first_phase": self.first_phase,
            "current_leader": self.current_leader,
            "allowed_suit": self.player_played[1] if self.current_leader == "player" else None
        }
        logger.debug("Game state: %s", state)
        return state

    def draw(self):
        # Draw the background.
        self.screen.blit(self.background, (0, 0))
        font_small = pygame.font.SysFont('Arial', 20)

        # --- Draw Opponent’s Hand (Zone A) as Card Backs ---
        if self.computer_hand:
            num_cards = len(self.computer_hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.zones['A'].x + (self.zones['A'].width - total_width) // 2
            y = self.zones['A'].y + (self.zones['A'].height - CARD_HEIGHT) // 2
            for i in range(num_cards):
                pos = (start_x + i * (CARD_WIDTH + CARD_SPACING), y)
                self.screen.blit(self.card_back, pos)

        # --- Draw Player’s Hand (Zone B) with Grey-out & Shake Effects ---
        if self.player_hand:
            num_cards = len(self.player_hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
            y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2

            # Determine the allowed suit when in second phase.
            # (Assume that when the computer is leading, its played card defines the led suit.)
            allowed_suit = None
            if not self.first_phase and self.current_leader == "computer" and self.computer_played:
                allowed_suit = self.computer_played[1]

            # Determine what valid moves are.
            # (player_has_follow: does the player hold a card of the led suit?
            #  player_has_trump: does the player hold any trump cards?)
            if allowed_suit:
                player_has_follow = any(card[1] == allowed_suit for card in self.player_hand)
                player_has_trump = any(card[1] == self.trump_suit for card in self.player_hand)
            else:
                player_has_follow = False
                player_has_trump = False

            for i, card in enumerate(self.player_hand):
                pos_x = start_x + i * (CARD_WIDTH + CARD_SPACING)

                # --- Apply Shake Animation if this card was clicked invalidly ---
                if self.shake_card_index is not None and i == self.shake_card_index:
                    elapsed = pygame.time.get_ticks() - self.shake_start_time
                    if elapsed < self.shake_duration:
                        # Oscillate using a sine function (adjust magnitude as needed).
                        offset = int(10 * math.sin((elapsed / 50.0) * math.pi))
                        pos_x += offset
                    else:
                        self.shake_card_index = None

                pos = (pos_x, y)
                card_img = self.card_images.get(card)

                # --- Determine whether this card is a valid move ---
                valid_move = True
                if not self.first_phase and allowed_suit:
                    # If the player has both cards in the led suit and trump cards, allow either.
                    if player_has_follow and player_has_trump:
                        valid_move = (card[1] == allowed_suit or card[1] == self.trump_suit)
                    elif player_has_follow:
                        valid_move = (card[1] == allowed_suit)
                    elif player_has_trump:
                        valid_move = (card[1] == self.trump_suit)
                    else:
                        valid_move = True  # Should not occur—if allowed_suit is defined, one of these should be true.
                
                # Grey out invalid cards.
                if not valid_move:
                    card_img = card_img.copy()
                    card_img.set_alpha(100)

                self.screen.blit(card_img, pos)

        # --- Draw Marriage Announcement, Played Cards, Deck, Buttons, etc. ---
        # Draw marriage announcement if active.
        if self.marriage_announcement is not None:
            current_time = pygame.time.get_ticks()
            if current_time - self.marriage_time < 3000:
                # During the 3-second animation, draw the marriage announcement.
                card1, card2 = self.marriage_announcement
                img1 = self.card_images.get(card1)
                img2 = self.card_images.get(card2)
                if img1 and img2:
                    total_width = CARD_WIDTH * 2 + 10
                    x = self.zones['C'].centerx - total_width // 2
                    y = self.zones['C'].centery - CARD_HEIGHT // 2
                    self.screen.blit(img1, (x, y))
                    self.screen.blit(img2, (x + CARD_WIDTH + 10, y))
                # Ensure input remains blocked.
                self.ongoing_animation = True
            else:
                # After 3 seconds, clear the marriage announcement and allow input.
                self.marriage_announcement = None
                self.ongoing_animation = False

        # Draw played cards (Zone C).
        if self.computer_played:
            img = self.card_images.get(self.computer_played)
            if img:
                rect = img.get_rect(center=self.zones['D'].center)
                self.screen.blit(img, rect)
        if self.player_played:
            img = self.card_images.get(self.player_played)
            if img:
                rect = img.get_rect(center=self.zones['E'].center)
                self.screen.blit(img, rect)

        # Draw the "End Trick" button (Zone F).
        pygame.draw.rect(self.screen, (180, 180, 250), self.zones['F'])
        et_text = font_small.render("End Trick", True, (0, 0, 0))
        et_rect = et_text.get_rect(center=self.zones['F'].center)
        self.screen.blit(et_text, et_rect)

        # Draw deck (Zone I), trump card (Zone H), remaining deck count (Zone J), and other UI elements.
        if self.deck:
            deck_img = pygame.transform.scale(self.card_back, (self.zones['I'].width, self.zones['I'].height))
            self.screen.blit(deck_img, (self.zones['I'].x, self.zones['I'].y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.zones['I'])
        if self.trump_card:
            trump_img = pygame.transform.scale(self.card_images.get(self.trump_card), (self.zones['H'].width, self.zones['H'].height))
            self.screen.blit(trump_img, (self.zones['H'].x, self.zones['H'].y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.zones['H'])
        pygame.draw.rect(self.screen, (250, 250, 200), self.zones['J'])
        count_text = font_small.render(str(len(self.deck)), True, (0, 0, 0))
        count_rect = count_text.get_rect(center=self.zones['J'].center)
        self.screen.blit(count_text, count_rect)

        # Draw additional buttons.
        if self.first_phase:
            self.close_button.draw(self.screen)
        else:
            sp_text = font_small.render("2nd Phase", True, (0, 0, 0))
            sp_rect = sp_text.get_rect(center=self.zones['K'].center)
            pygame.draw.rect(self.screen, (200, 250, 200), self.zones['K'])
            self.screen.blit(sp_text, sp_rect)
        self.switch_button.draw(self.screen)
        self.marriage_button.draw(self.screen)

        # Draw trump suit text (Zone T).
        trump_text = f"Trump Suit: ({self.trump_suit})" if self.trump_suit else "No Trump"
        trump_surface = font_small.render(trump_text, True, (0, 0, 0))
        trump_rect = trump_surface.get_rect(center=self.zones['T'].center)
        pygame.draw.rect(self.screen, (250, 250, 250), self.zones['T'])
        self.screen.blit(trump_surface, trump_rect)

        # Draw overall game points (Zone OG).
        game_points_text = f"Game: {self.player_game_points} - {self.computer_game_points}"
        game_points_surface = font_small.render(game_points_text, True, (0, 0, 0))
        game_points_rect = game_points_surface.get_rect(center=self.zones['OG'].center)
        pygame.draw.rect(self.screen, (250, 250, 200), self.zones['OG'])
        self.screen.blit(game_points_surface, game_points_rect)

        # Draw round points (Zone G).
        pygame.draw.rect(self.screen, (250, 200, 200), self.zones['G'])
        points_text = font_small.render(f"Pts: {self.player_round_points}-{self.computer_round_points}", True, (0, 0, 0))
        points_rect = points_text.get_rect(center=self.zones['G'].center)
        self.screen.blit(points_text, points_rect)

        # Draw the player's won cards (Zone W).
        if self.player_won_cards:
            offset = 20  # Overlap offset.
            x = self.zones['W'].x
            y = self.zones['W'].y
            scale_factor = 0.5
            thumb_width = int(CARD_WIDTH * scale_factor)
            thumb_height = int(CARD_HEIGHT * scale_factor)
            for card in self.player_won_cards:
                img = self.card_images.get(card)
                if img:
                    thumb = pygame.transform.scale(img, (thumb_width, thumb_height))
                    self.screen.blit(thumb, (x, y))
                else:
                    card_text = f"{card[0]}{card[1]}"
                    text_surface = pygame.font.SysFont('Arial', 16).render(card_text, True, (0, 0, 0))
                    self.screen.blit(text_surface, (x, y))
                x += offset
                
        # Draw the pause button (for example, at the top right)
        self.pause_button.draw(self.screen)

        # Draw feedback message.
        msg_text = font_small.render(self.message, True, (255, 255, 255))
        msg_rect = msg_text.get_rect(center=(self.screen_width // 2, self.zones['B'].y - 30))
        self.screen.blit(msg_text, msg_rect)

    def handle_event(self, event):
        #logger.debug("GamePlay.handle_event received event: %s", event)
        # If an animation (such as a marriage announcement) is ongoing, ignore move events.
        # (You might want to let non–move events pass through; adjust as needed.)
        if self.ongoing_animation:
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        # Let the buttons process the event first.
        self.pause_button.handle_event(event)
        self.close_button.handle_event(event)
        self.switch_button.handle_event(event)
        self.marriage_button.handle_event(event)

        pos = event.pos
        logger.debug("Mouse click at position: %s", pos)

        # If the "End Trick" button is clicked, process it immediately.
        if self.zones['F'].collidepoint(pos):
            if self.trick_ready:
                logger.info("End Trick button clicked.")
                self.resolve_trick()
            return

        # If a trick is in progress, ignore further clicks.
        if self.trick_ready:
            logger.debug("Trick already ready; ignoring additional clicks.")
            return

        # Determine the allowed suit when in second phase.
        allowed_suit = None
        if not self.first_phase and self.current_leader == "computer" and self.computer_played:
            allowed_suit = self.computer_played[1]
            logger.debug("Allowed suit for following: %s", allowed_suit)

        if allowed_suit:
            player_has_follow = any(card[1] == allowed_suit for card in self.player_hand)
            player_has_trump = any(card[1] == self.trump_suit for card in self.player_hand)
        else:
            player_has_follow = False
            player_has_trump = False

        num_cards = len(self.player_hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
        y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2

        # Loop over each card in the player's hand to see if it was clicked.
        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i * (CARD_WIDTH + CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                logger.info("Player clicked on card at index %d.", i)
                # If a marriage announcement is pending for the player, handle that first.
                if self.marriage_pending:
                    selected_card = self.player_hand[i]
                    # If the card is not eligible (not "K" or "Q"), cancel the marriage.
                    if selected_card[0] not in ("K", "Q"):
                        self.marriage_pending = False
                        self.message = "Marriage cancelled."
                        return  # Cancel the pending marriage.
                    suit = selected_card[1]
                    if suit in self.player_marriages_announced:
                        self.marriage_pending = False
                        self.message = f"Marriage for {suit} has already been announced. Marriage cancelled."
                        return
                    if selected_card[0] == "K":
                        partner = ("Q", suit)
                    else:
                        partner = ("K", suit)
                    if partner not in self.player_hand:
                        self.marriage_pending = False
                        self.message = "Matching card for marriage not found. Marriage cancelled."
                        return
                    # Valid marriage: record the announcement and start the animation.
                    self.marriage_announcement = (selected_card, partner)
                    self.marriage_time = pygame.time.get_ticks()
                    self.marriage_pending = False
                    self.ongoing_animation = True  # Block further input until animation ends.
                    self.player_marriages_announced.add(suit)
                    points = 40 if suit == self.trump_suit else 20
                    self.player_round_points += points
                    self.message = f"Marriage announced in {suit}! +{points} points."
                    return

                # Otherwise, process the card as a normal move.
                valid_move = True
                if not self.first_phase and allowed_suit:
                    if player_has_follow and player_has_trump:
                        valid_move = (self.player_hand[i][1] == allowed_suit or self.player_hand[i][1] == self.trump_suit)
                    elif player_has_follow:
                        valid_move = (self.player_hand[i][1] == allowed_suit)
                    elif player_has_trump:
                        valid_move = (self.player_hand[i][1] == self.trump_suit)
                    else:
                        valid_move = True

                if not valid_move:
                    msg = f"You must play a {allowed_suit} card"
                    if player_has_trump:
                        msg += " or a trump card"
                    self.message = msg + "."
                    self.shake_card_index = i
                    self.shake_start_time = pygame.time.get_ticks()
                    return

                # Process the card normally based on whose turn it is.
                if self.current_leader == "player":
                    self.player_lead(i)
                else:
                    self.player_follow(i)
                break

    def _player_play_card(self, card_index, move_type="move"):
        try:
            card = self.player_hand.pop(card_index)
            self.player_played = card
            logger.debug("Player %s card: %s. Updated hand: %s", move_type, card, self.player_hand)
            return card
        except Exception as e:
            logger.error("Error in player %s: %s", move_type, e)
            return None

    def player_lead(self, card_index):
        logger.info("Player is leading with card at index %d.", card_index)
        card = self._player_play_card(card_index, "lead")
        if card is None:
            return
        state = self.get_game_state()
        self.computer_played = self.opponent.play(state, self.computer_hand)
        logger.info("Computer responded with: %s", self.computer_played)
        self.trick_ready = True
        self.message = "Trick ready. Click 'End Trick' to resolve."
        self.current_leader = "player"

    def player_follow(self, card_index):
        logger.info("Player is following with card at index %d.", card_index)
        card = self._player_play_card(card_index, "follow")
        if card is None:
            return
        logger.debug("Player followed with card: %s. Updated hand: %s", card, self.player_hand)
        self.trick_ready = True
        self.message = "Trick ready. Click 'End Trick' to resolve."

    def player_follow_by_click(self, pos):
        """
        Helper to select the card the player clicked when following.
        """
        logger.info("Processing player follow by click at position: %s", pos)
        num_cards = len(self.player_hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
        y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2
        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i*(CARD_WIDTH+CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                self.player_follow(i)
                break

    def computer_lead(self):
        logger.info("Computer's turn to lead started.")
        current_time = pygame.time.get_ticks()
        
        # If a marriage announcement is active, wait until the 3-second period is over.
        if self.marriage_announcement is not None:
            delta = current_time - self.marriage_time
            if delta < 3000:
                logger.info("Marriage announcement active (delta: %d ms). Waiting to lead...", delta)
                self.message = "Computer announced marriage. Waiting to lead..."
                return  # Do not lead until the announcement is cleared.
            else:
                logger.debug("Marriage announcement period elapsed; clearing announcement.")
                # (The timer event should normally clear the announcement, but as a fallback:)
                self.marriage_announcement = None

        # Only check for a new marriage if one has not already been processed for this trick.
        if not self.computer_marriage_processed:
            marriage_found = None
            for suit in self.suits:
                if suit in self.computer_marriages_announced:
                    continue  # Skip suits already announced.
                if (("K", suit) in self.computer_hand) and (("Q", suit) in self.computer_hand):
                    marriage_found = (("K", suit), ("Q", suit))
                    break
            if marriage_found:
                self.marriage_announcement = marriage_found
                self.marriage_time = current_time
                points = 40 if marriage_found[0][1] == self.trump_suit else 20
                self.computer_round_points += points
                self.message = f"Computer announces marriage in {marriage_found[0][1]}! +{points} points."
                logger.info("Computer announces marriage: %s, awarding %d points.", marriage_found, points)
                # Schedule a timer event to clear the announcement after 3000ms.
                pygame.time.set_timer(MARRIAGE_DONE_EVENT, 3000)
                return  # Do not lead a card until the timer clears the announcement.

        # If no marriage is announced (or it has already been processed), lead normally.
        state = self.get_game_state()
        self.computer_played = self.opponent.play(state, self.computer_hand)
        logger.info("Computer leads with card: %s.", self.computer_played)
        self.current_leader = "computer"
        self.message = "Computer leads. Your turn to follow."
        self.trick_ready = False

    def resolve_trick(self):
        """
        Determine the trick winner, add points, and update the leader.
        Then call draw_cards (which now also handles the last-trick bonus).
        If the computer wins the trick, automatically have it lead.
        """
        logger.info("Resolving trick. Player card: %s, Computer card: %s.", self.player_played, self.computer_played)
        winner = self.determine_trick_winner(self.player_played, self.computer_played)
        trick_points = CARD_VALUES[self.player_played[0]] + CARD_VALUES[self.computer_played[0]]
        logger.info("Trick points calculated: %d.", trick_points)
        # (The extra 10 points for the last trick will be handled in draw_cards.)
        if winner == "player":
            self.player_round_points += trick_points
            self.player_tricks += 1
            self.message = f"You win the trick and earn {trick_points} points!"
            self.current_leader = "player"
            # Record the won cards for display.
            self.player_won_cards.extend([self.player_played, self.computer_played])
            logger.info("Player wins the trick. New player round points: %d.", self.player_round_points)
        elif winner == "computer":
            self.computer_round_points += trick_points
            self.computer_tricks += 1
            self.message = f"Computer wins the trick and earns {trick_points} points!"
            self.current_leader = "computer"
            self.computer_won_cards.extend([self.player_played, self.computer_played])
            logger.info("Computer wins the trick. New computer round points: %d.", self.computer_round_points)
        else:
            self.message = "Tie trick! No points awarded."
            logger.info("Trick ended in a tie.")

        self.player_played = None
        self.computer_played = None
        self.trick_ready = False

        if self.first_phase:
            self.draw_cards(winner)
        self.check_round_end()
        # If computer is now leader, have it lead automatically (even in second phase).
        if self.current_leader == "computer":
            logger.info("After trick resolution, computer is leading. Initiating computer lead.")
            self.computer_lead()

    def determine_trick_winner(self, player_card, computer_card):
        """
        Determine the trick winner based solely on the CARD_VALUES.
        
        Rules:
        - The leader is the first card played (its suit defines the lead suit).
        - A trump card (i.e. one whose suit equals self.trump_suit) beats any non-trump.
        - If both cards are trump or both are non-trump:
            - If the follower's card does not follow the lead suit, the leader wins.
            - Otherwise, the card with the higher point value (from CARD_VALUES) wins.
            - In case of equal values, the leader wins by default.
        
        Returns:
            "player" or "computer" indicating the winner of the trick.
        """
        logger.debug("Determining trick winner. Player card: %s, Computer card: %s", player_card, computer_card)
        trump = self.trump_suit

        # Identify leader and follower based on who started the trick.
        if self.current_leader == "player":
            leader_card = player_card
            follower_card = computer_card
            leader = "player"
            follower = "computer"
        else:
            leader_card = computer_card
            follower_card = player_card
            leader = "computer"
            follower = "player"

        # The lead suit is defined by the leader's card.
        lead_suit = leader_card[1]

        # Rule 1: If one card is trump and the other is not, trump wins.
        if leader_card[1] == trump and follower_card[1] != trump:
            logger.debug("Player card is trump; player wins.")
            return leader
        if follower_card[1] == trump and leader_card[1] != trump:
            logger.debug("Computer card is trump; computer wins.")
            return follower

        # Rule 2(a): If neither card is trump (or both are trump) and the follower did not follow suit,
        # then the leader wins.
        if follower_card[1] != lead_suit:
            logger.debug("Cards are of different suits; leader wins by default.")
            return leader

        # Rule 2(b): Both cards are of the lead suit (or both are trump), so compare point values.
        logger.debug("Comparing point values: Leader %d vs. Follower %d", CARD_VALUES[leader_card[0]], CARD_VALUES[follower_card[0]])
        if CARD_VALUES[leader_card[0]] >= CARD_VALUES[follower_card[0]]:
            logger.debug("Leader wins based on point value.")
            return leader
        else:
            logger.debug("Follower wins based on point value.")
            return follower

    def draw_cards(self, trick_winner):
        """
        In first phase, after a trick the winner draws first and the loser draws second.
        If, after the winner’s draw the deck becomes empty, then the loser draws the trump-announcement card
        (which counts as the last card) and the winner is awarded an extra 10 points.
        Then, the game switches to second phase.
        """
        logger.info("Drawing cards after trick. Trick winner: %s.", trick_winner)
        if self.deck:
            if trick_winner == "player":
                card = self.deck.pop()
                self.player_hand.append(card)
                logger.debug("Player draws card: %s", card)
                if not self.deck and self.trump_card is not None:
                    # Last card: loser draws the trump card.
                    self.computer_hand.append(self.trump_card)
                    logger.debug("Deck empty after player draw; computer draws trump card: %s", self.trump_card)
                    self.trump_card = None
                    self.player_round_points += 10  # extra 10 points bonus
                    logger.info("Extra 10 points awarded to player for last trick bonus.")
                elif self.deck:
                    card = self.deck.pop()
                    self.computer_hand.append(card)
                    logger.debug("Computer draws card: %s", card)
            elif trick_winner == "computer":
                card = self.deck.pop()
                self.computer_hand.append(card)
                logger.debug("Computer draws card: %s", card)
                if not self.deck and self.trump_card is not None:
                    self.player_hand.append(self.trump_card)
                    logger.debug("Deck empty after computer draw; player draws trump card: %s", self.trump_card)
                    self.trump_card = None
                    self.computer_round_points += 10  # extra 10 points bonus
                    logger.info("Extra 10 points awarded to computer for last trick bonus.")
                elif self.deck:
                    card = self.deck.pop()
                    self.player_hand.append(card)
                    logger.debug("Player draws card: %s", card)
            if not self.deck:
                self.first_phase = False
                logger.info("Deck exhausted. Switching to second phase.")
        else:
            self.first_phase = False
            logger.info("No deck remaining. Switching to second phase.")

    def check_round_end(self):
        """
        Revised round–end check.
        The round now ends only when both players' hands are empty.
        Game points are awarded as follows:
        - If either player has 66 or more points:
            • If the losing side has less than 33 points → winner gets 2 game points.
            • If the losing side has won 0 tricks → winner gets 3 game points.
            • Otherwise → winner gets 1 game point.
        - If neither player reaches 66, the player with the highest points gets 1 game point.
        - If the player closed the game but did not reach 66, the opponent gets 1 game point as a penalty.
        """
        logger.info("Checking if round has ended.")
        # Only check for round end when both hands are empty.
        if len(self.player_hand) > 0 or len(self.computer_hand) > 0:
            logger.debug("Round not ended; player_hand has %d cards, computer_hand has %d cards.", 
                     len(self.player_hand), len(self.computer_hand))
            return  # Round is not over yet.

        # --- Round has ended because both hands are empty. ---
        logger.info("Both hands empty; round has ended.")

        # First, handle the case where the game was closed.
        if self.game_closed:
            logger.info("Game was closed by the player.")
            # Assume only the human can close the game.
            if self.player_round_points < 66:
                logger.info("Player closed the game but did not reach 66 (player points: %d). Awarding 1 game point to computer.", 
                        self.player_round_points)
                # The human closed but did not reach 66; award 1 game point to the computer.
                self.computer_game_points += 1
                self.message = "You closed the game but didn't reach 66. Computer gets 1 game point as penalty."
                # Reset the flag for the next round.
                self.game_closed = False
                # End the round.
                if self.player_game_points >= 11 or self.computer_game_points >= 11:
                    self.message += " Game Over."
                    logger.info("Overall game over. Final scores - Player: %d, Computer: %d", 
                            self.player_game_points, self.computer_game_points)
                    self.end_game_callback()
                else:
                    logger.info("Resetting round after penalty.")
                    self.reset_round()
                return
            else:
                # If closed and the human did reach 66, then clear the flag and continue with normal scoring.
                logger.info("Game was closed but player reached 66. Clearing game_closed flag.")
                self.game_closed = False

        # Now, determine scoring based on round points.
        if self.player_round_points >= 66 or self.computer_round_points >= 66:
            logger.info("At least one player reached 66 points (Player: %d, Computer: %d).", 
                    self.player_round_points, self.computer_round_points)
            # At least one player reached 66.
            if self.player_round_points > self.computer_round_points:
                winner = "player"
                loser_points = self.computer_round_points
                loser_tricks = self.computer_tricks
            else:
                winner = "computer"
                loser_points = self.player_round_points
                loser_tricks = self.player_tricks

            # Apply the game point rules.
            if loser_tricks == 0:
                game_points = 3
                logger.info("Opponent won 0 tricks. Awarding 3 game points to %s.", winner)
            elif loser_points < 33:
                game_points = 2
                logger.info("Opponent has less than 33 points. Awarding 2 game points to %s.", winner)
            else:
                game_points = 1
                logger.info("Awarding 1 game point to %s.", winner)
        else:
            logger.info("Neither player reached 66 points (Player: %d, Computer: %d).", 
                    self.player_round_points, self.computer_round_points)
            # Neither player reached 66.
            if self.player_round_points > self.computer_round_points:
                winner = "player"
            elif self.computer_round_points > self.player_round_points:
                winner = "computer"
            else:
                winner = None  # A tie.
            game_points = 1

        # Award game points.
        if winner:
            if winner == "player":
                self.player_game_points += game_points
                self.message = f"You win the round! (+{game_points} game point)"
            else:
                self.computer_game_points += game_points
                self.message = f"Computer wins the round! (+{game_points} game point)"
            logger.info("Round winner: %s. Awarded %d game point(s). Current overall scores - Player: %d, Computer: %d",
                winner, game_points, self.player_game_points, self.computer_game_points)
        else:
            self.message = "Round ended in a tie. No game points awarded."
            logger.info("Round ended in a tie. No game points awarded.")

        # Check for overall game end.
        if self.player_game_points >= 11 or self.computer_game_points >= 11:
            self.message += " Game Over."
            logger.info("Overall game over. Final scores - Player: %d, Computer: %d", 
                self.player_game_points, self.computer_game_points)
            self.end_game_callback()
        else:
            logger.info("Resetting round for next play. Current overall scores - Player: %d, Computer: %d", 
                self.player_game_points, self.computer_game_points)
            self.reset_round()

    def reset_round(self):
        """
        Reset for a new round: rebuild the deck, re-deal cards, and reset round points and trick counts.
        """
        logger.info("Resetting round.")
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        logger.debug("Deck rebuilt and shuffled. Total cards: %d", len(self.deck))
        self.player_hand = [self.deck.pop() for _ in range(3)]
        self.computer_hand = [self.deck.pop() for _ in range(3)]
        self.player_hand += [self.deck.pop() for _ in range(3)]
        self.computer_hand += [self.deck.pop() for _ in range(3)]
        logger.debug("Dealt new hands. Player hand: %s, Computer hand: %s", self.player_hand, self.computer_hand)
        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None
        logger.info("New trump card: %s", self.trump_card)
        self.player_round_points = 0
        self.computer_round_points = 0
        self.player_tricks = 0
        self.computer_tricks = 0
        logger.debug("Round points and trick counts reset.")
        self.first_phase = True
        self.current_leader = "player"
        self.player_played = None
        self.computer_played = None
        self.trick_ready = False
        self.marriage_pending = False
        self.marriage_announcement = None
        self.marriage_time = None
        self.player_marriages_announced = set()
        self.computer_marriages_announced = set()
        self.computer_marriage_processed = False
        self.player_won_cards = []
        self.computer_won_cards = []
        self.game_closed = False
        self.message += " New round started. Your turn to lead."
        logger.info("Round reset complete.")

    def close_game(self):
        """
        Called when the player clicks the "Close" button.
        This stops drawing from the deck and marks that the game was closed.
        """
        logger.info("Player chose to close the game (end first phase).")
        self.first_phase = False
        self.game_closed = True  # Mark that the human closed the game.
        self.message = "You closed the game. Now in second phase, follow suit if possible."
        logger.debug("Game closed flag set; switching to second phase.")

    def switch_trump(self):
        # Allow the switch only if the player is the leader.
        logger.info("Player attempting trump switch.")
        if self.current_leader != "player":
            self.message = "You can only switch trump 9 when you are leading."
            logger.warning("Trump switch failed: player is not the leader.")
            return

        trump9 = ("9", self.trump_suit)
        if trump9 in self.player_hand:
            # Remove trump 9 from the player's hand
            self.player_hand.remove(trump9)
            # Add the current trump announcement card to the player's hand
            self.player_hand.append(self.trump_card)
            # Now set the trump announcement card to trump9
            self.trump_card = trump9
            self.message = "Trump 9 switch successful!"
            logger.info("Trump switch successful: Player switched trump card with trump 9.")
        else:
            self.message = "You do not have the trump 9."
            logger.warning("Trump switch failed: Player does not have trump 9.")

    def announce_marriage(self):
        # Only allow marriage if the human is in lead and has not yet announced one this round.
        logger.info("Player requested marriage announcement.")
        if self.current_leader != "player":
            self.message = "You can only announce marriage when you're in lead."
            logger.warning("Marriage announcement failed: player is not in lead.")
            return
        # Set a flag so that the next card click will be interpreted as the marriage selection.
        self.marriage_pending = True
        self.message = "Marriage pending: click a King or Queen from your hand to announce marriage."
        logger.debug("Marriage pending flag set; waiting for player to select appropriate card.")

    def pause_game(self):
        # Call the callback that was passed to GamePlay to change the state.
        logger.info("Pause game triggered by player.")
        if hasattr(self, 'pause_callback'):
            self.pause_callback()
            logger.info("Pause callback invoked; game state should now be 'pause'.")
        else:
            logger.error("Pause callback not defined in GamePlay.")