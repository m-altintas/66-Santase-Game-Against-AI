import pygame
import random
import math

from constants import CARD_HEIGHT, CARD_WIDTH, CARD_SPACING, MARGIN, CARD_VALUES, MARRIAGE_DONE_EVENT
from ui import Button
from player import HumanPlayer, AIPlayer
from log_config import logger
from utils import resource_path

# ---------------------------
# GamePlay Class Definition
# ---------------------------
class GamePlay:
    def __init__(self, screen, end_game_callback, ai_strategy="JustRandom", developer_mode=False):
        logger.info("Initializing GamePlay.")
        self.end_game_callback = end_game_callback
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.developer_mode = developer_mode
        
        self.card_animation = None

        logger.debug("Screen dimensions: %d x %d", self.screen_width, self.screen_height)

        # Load background image or fallback to a green surface
        try:
            self.background = pygame.image.load(resource_path("assets/backgrounds/game_background.jpg"))
            self.background = pygame.transform.scale(self.background, (self.screen_width, self.screen_height))
            logger.info("Background image loaded and scaled.")
        except Exception as e:
            logger.error("Error loading background image: %s", e)
            self.background = pygame.Surface((self.screen_width, self.screen_height))
            self.background.fill((0, 128, 0))

        # Load card back image or fallback
        try:
            self.card_back = pygame.image.load(resource_path("assets/cards/back.png"))
            self.card_back = pygame.transform.scale(self.card_back, (CARD_WIDTH, CARD_HEIGHT))
            logger.info("Card back image loaded.")
        except Exception as e:
            logger.error("Error loading card back: %s", e)
            self.card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.card_back.fill((0, 0, 128))

        # Load card images
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

        # Build the deck and shuffle
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        logger.debug("Deck built and shuffled with %d cards.", len(self.deck))

        # Create players
        self.player = HumanPlayer()
        self.opponent = AIPlayer(strategy=ai_strategy)

        # Deal cards (6 each)
        self.player.hand = [self.deck.pop() for _ in range(6)]
        self.opponent.hand = [self.deck.pop() for _ in range(6)]
        logger.debug("Player hand: %s", self.player.hand)
        logger.debug("Opponent hand: %s", self.opponent.hand)

        # Reveal trump card
        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None
        logger.info("Trump card revealed: %s", self.trump_card)

        # Reset played cards and state
        self.player.played_card = None
        self.opponent.played_card = None
        self.trick_ready = False
        self.first_phase = True  # The initial phase where players draw cards
        self.current_leader = "player"

        # Points, animation flags, and announcements
        self.player.round_points = 0
        self.opponent.round_points = 0
        self.player_game_points = 0
        self.opponent_game_points = 0
        self.ongoing_animation = False
        self.marriage_announcement = None
        self.marriage_time = None
        self.game_closed = False
        self.message = "Your turn to lead."

        # UI zones
        self.zones = self.init_zones()

        # Buttons
        self.close_button = Button(self.zones['K'], "Close", self.close_game, pygame.font.SysFont('Arial', 20))
        self.switch_button = Button(self.zones['L'], "Switch", self.switch_trump, pygame.font.SysFont('Arial', 20))
        self.marriage_button = Button(self.zones['M'], "Marriage", self.announce_marriage, pygame.font.SysFont('Arial', 20))

        self.shake_card_index = None
        self.shake_start_time = 0
        self.shake_duration = 500

        pause_button_rect = pygame.Rect(self.screen_width - MARGIN - 100, MARGIN, 100, 40)
        self.pause_button = Button(pause_button_rect, "Pause", self.pause_game, pygame.font.SysFont('Arial', 20))

        logger.info("GamePlay initialized successfully.")

    def init_zones(self):
        """
        Define important UI regions for card placement, deck, trump, etc.
        """
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

    def switch_to_second_phase(self):
        """
        Common method to exit the first phase and enter the second phase.
        """
        self.first_phase = False
        logger.info("Switching to second phase.")

    def get_game_state(self):
        """
        Gather current game-related info for the AI or debug.
        """
        if self.current_leader == "player" and self.player.played_card:
            allowed_suit = self.player.played_card[1]
            leader_card = self.player.played_card
        elif self.current_leader == "opponent" and self.opponent.played_card:
            allowed_suit = self.opponent.played_card[1]
            leader_card = self.opponent.played_card
        else:
            allowed_suit = None
            leader_card = None

        return {
            "player_played": self.player.played_card,
            "opponent_played": self.opponent.played_card,
            "player_round_points": self.player.round_points,
            "opponent_round_points": self.opponent.round_points,
            "remaining_deck": self.deck.copy(),
            "trump_card": self.trump_card,
            "trump_suit": self.trump_suit,
            "opponent_hand": self.opponent.hand.copy(),
            "player_hand": self.player.hand.copy(),
            "first_phase": self.first_phase,
            "current_leader": self.current_leader,
            "allowed_suit": allowed_suit,
            "leader_card": leader_card,
            "player_known_cards": list(self.player.known_cards),
        }

    def draw(self):
        """
        Draw all elements: background, hands, played cards, deck, UI elements, etc.
        """
        self.screen.blit(self.background, (0, 0))
        font_small = pygame.font.SysFont('Arial', 20)

        # Opponent's hand (Zone A)
        if self.opponent.hand:
            num_cards = len(self.opponent.hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.zones['A'].x + (self.zones['A'].width - total_width) // 2
            y = self.zones['A'].y + (self.zones['A'].height - CARD_HEIGHT) // 2
            
            for i, card in enumerate(self.opponent.hand):
                if self.card_animation and self.card_animation.card == card:
                    continue
                
                pos = (start_x + i * (CARD_WIDTH + CARD_SPACING), y)
                if self.developer_mode:
                    # Show the actual card image in developer mode
                    img = self.card_images.get(card)
                    self.screen.blit(img if img else self.card_back, pos)
                else:
                    self.screen.blit(self.card_back, pos)

        # Player's hand (Zone B)
        if self.player.hand:
            num_cards = len(self.player.hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
            y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2

            allowed_suit = None
            if (
                not self.first_phase
                and self.current_leader == "opponent"
                and self.opponent.played_card
            ):
                allowed_suit = self.opponent.played_card[1]

            for i, card in enumerate(self.player.hand):
                pos_x = start_x + i * (CARD_WIDTH + CARD_SPACING)
                # Apply shake animation if needed
                if self.shake_card_index is not None and i == self.shake_card_index:
                    elapsed = pygame.time.get_ticks() - self.shake_start_time
                    if elapsed < self.shake_duration:
                        offset = int(10 * math.sin((elapsed / 50.0) * math.pi))
                        pos_x += offset
                    else:
                        self.shake_card_index = None
                pos = (pos_x, y)

                card_img = self.card_images.get(card)
                valid_move = True
                if not self.first_phase and allowed_suit:
                    if any(c[1] == allowed_suit for c in self.player.hand):
                        valid_move = (card[1] == allowed_suit)
                    elif any(c[1] == self.trump_suit for c in self.player.hand):
                        valid_move = (card[1] == self.trump_suit)
                if not valid_move and card_img:
                    card_img = card_img.copy()
                    card_img.set_alpha(100)

                self.screen.blit(card_img if card_img else self.card_back, pos)

        # Marriage announcement
        if self.marriage_announcement is not None:
            current_time = pygame.time.get_ticks()
            if current_time - self.marriage_time < 3000:
                card1, card2 = self.marriage_announcement
                img1 = self.card_images.get(card1)
                img2 = self.card_images.get(card2)
                if img1 and img2:
                    total_width = CARD_WIDTH * 2 + 10
                    x = self.zones['C'].centerx - total_width // 2
                    y = self.zones['C'].centery - CARD_HEIGHT // 2
                    self.screen.blit(img1, (x, y))
                    self.screen.blit(img2, (x + CARD_WIDTH + 10, y))
                self.ongoing_animation = True
            else:
                self.marriage_announcement = None
                self.ongoing_animation = False

        # Played cards (Zone C)
        if self.opponent.played_card:
            img = self.card_images.get(self.opponent.played_card)
            if img:
                rect = img.get_rect(center=self.zones['D'].center)
                self.screen.blit(img, rect)
        if self.player.played_card:
            img = self.card_images.get(self.player.played_card)
            if img:
                rect = img.get_rect(center=self.zones['E'].center)
                self.screen.blit(img, rect)

        # "End Trick" button (Zone F)
        pygame.draw.rect(self.screen, (180, 180, 250), self.zones['F'])
        et_text = font_small.render("End Trick", True, (0, 0, 0))
        et_rect = et_text.get_rect(center=self.zones['F'].center)
        self.screen.blit(et_text, et_rect)

        # Deck (Zone I) and trump card (Zone H)
        if self.deck:
            deck_img = pygame.transform.scale(self.card_back, (self.zones['I'].width, self.zones['I'].height))
            self.screen.blit(deck_img, (self.zones['I'].x, self.zones['I'].y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.zones['I'])

        if self.trump_card:
            trump_img = self.card_images.get(self.trump_card)
            if trump_img:
                trump_img = pygame.transform.scale(trump_img, (self.zones['H'].width, self.zones['H'].height))
                self.screen.blit(trump_img, (self.zones['H'].x, self.zones['H'].y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.zones['H'])

        # Remaining deck count (Zone J)
        pygame.draw.rect(self.screen, (250, 250, 200), self.zones['J'])
        count_text = font_small.render(str(len(self.deck)), True, (0, 0, 0))
        count_rect = count_text.get_rect(center=self.zones['J'].center)
        self.screen.blit(count_text, count_rect)

        # Close or 2nd Phase text (Zone K)
        if self.first_phase:
            self.close_button.draw(self.screen)
        else:
            sp_text = font_small.render("2nd Phase", True, (0, 0, 0))
            sp_rect = sp_text.get_rect(center=self.zones['K'].center)
            pygame.draw.rect(self.screen, (200, 250, 200), self.zones['K'])
            self.screen.blit(sp_text, sp_rect)

        self.switch_button.draw(self.screen)
        self.marriage_button.draw(self.screen)

        # Trump suit text (Zone T)
        trump_text = f"Trump Suit: ({self.trump_suit})" if self.trump_suit else "No Trump"
        trump_surface = font_small.render(trump_text, True, (0, 0, 0))
        trump_rect = trump_surface.get_rect(center=self.zones['T'].center)
        pygame.draw.rect(self.screen, (250, 250, 250), self.zones['T'])
        self.screen.blit(trump_surface, trump_rect)

        # Overall game points (Zone OG)
        game_points_text = f"Game: {self.player_game_points} - {self.opponent_game_points}"
        game_points_surface = font_small.render(game_points_text, True, (0, 0, 0))
        game_points_rect = game_points_surface.get_rect(center=self.zones['OG'].center)
        pygame.draw.rect(self.screen, (250, 250, 200), self.zones['OG'])
        self.screen.blit(game_points_surface, game_points_rect)

        # Round points (Zone G)
        pygame.draw.rect(self.screen, (250, 200, 200), self.zones['G'])
        points_text = font_small.render(
            f"Pts: {self.player.round_points}-{self.opponent.round_points}",
            True,
            (0, 0, 0)
        )
        points_rect = points_text.get_rect(center=self.zones['G'].center)
        self.screen.blit(points_text, points_rect)

        # Player's won cards (Zone W)
        if self.player.won_cards:
            offset = 20
            x = self.zones['W'].x
            y = self.zones['W'].y
            scale_factor = 0.5
            thumb_width = int(CARD_WIDTH * scale_factor)
            thumb_height = int(CARD_HEIGHT * scale_factor)
            for card in self.player.won_cards:
                img = self.card_images.get(card)
                if img:
                    thumb = pygame.transform.scale(img, (thumb_width, thumb_height))
                    self.screen.blit(thumb, (x, y))
                else:
                    card_text = f"{card[0]}{card[1]}"
                    text_surface = pygame.font.SysFont('Arial', 16).render(card_text, True, (0, 0, 0))
                    self.screen.blit(text_surface, (x, y))
                x += offset

        self.pause_button.draw(self.screen)
        msg_text = font_small.render(self.message, True, (255, 255, 255))
        msg_rect = msg_text.get_rect(center=(self.screen_width // 2, self.zones['B'].y - 30))
        self.screen.blit(msg_text, msg_rect)
        
        # Finally, draw any active card animation
        if self.card_animation:
            (anim_pos, finished) = self.card_animation.update_position()
            # Get the card image
            card_tuple = self.card_animation.card
            card_img = self.card_images.get(card_tuple, self.card_back)
            
            card_w, card_h = card_img.get_size()
            blit_x = anim_pos[0] - card_w // 2
            blit_y = anim_pos[1] - card_h // 2
    
            # Blit the animating card
            self.screen.blit(card_img, (blit_x, blit_y))

            if finished:
                # If the animation has reached the end, call on_complete
                if self.card_animation.on_complete:
                    self.card_animation.on_complete()

    def handle_event(self, event):
        """
        Handle mouse clicks, button interactions, etc.
        """
        if self.ongoing_animation:
            return
        if self.card_animation:
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        self.pause_button.handle_event(event)
        self.close_button.handle_event(event)
        self.switch_button.handle_event(event)
        self.marriage_button.handle_event(event)

        pos = event.pos
        logger.debug("Mouse click at position: %s", pos)

        if self.zones['F'].collidepoint(pos):
            if self.trick_ready:
                logger.info("End Trick button clicked.")
                self.resolve_trick()
            return

        if self.trick_ready:
            logger.debug("Trick already ready; ignoring additional clicks.")
            return

        allowed_suit = None
        if (
            not self.first_phase
            and self.current_leader == "opponent"
            and self.opponent.played_card
        ):
            allowed_suit = self.opponent.played_card[1]
            logger.debug("Allowed suit for following: %s", allowed_suit)

        # Check if player clicked on a card in hand
        num_cards = len(self.player.hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
        y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2

        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i * (CARD_WIDTH + CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                logger.info("Player clicked on card at index %d.", i)

                # If marriage is pending, handle that first
                if self.player.marriage_pending:
                    selected_card = self.player.hand[i]
                    if selected_card[0] not in ("K", "Q"):
                        self.player.marriage_pending = False
                        self.message = "Marriage cancelled."
                        return
                    suit = selected_card[1]
                    if suit in self.player.marriages_announced:
                        self.player.marriage_pending = False
                        self.message = f"Marriage for {suit} already announced. Cancelled."
                        return
                    partner = ("Q", suit) if selected_card[0] == "K" else ("K", suit)
                    if partner not in self.player.hand:
                        self.player.marriage_pending = False
                        self.message = "Matching card not found. Marriage cancelled."
                        return
                    self.marriage_announcement = (selected_card, partner)
                    self.marriage_time = pygame.time.get_ticks()
                    self.player.marriage_pending = False
                    self.ongoing_animation = True
                    self.player.marriages_announced.add(suit)
                    points = 40 if suit == self.trump_suit else 20
                    self.player.round_points += points
                    self.player.known_cards.add(selected_card)
                    self.player.known_cards.add(partner)
                    self.message = f"Marriage announced in {suit}! +{points} points."
                    return

                # Otherwise, play a normal card
                valid_move = True
                if not self.first_phase and allowed_suit:
                    if any(card[1] == allowed_suit for card in self.player.hand):
                        valid_move = (self.player.hand[i][1] == allowed_suit)
                    elif any(card[1] == self.trump_suit for card in self.player.hand):
                        valid_move = (self.player.hand[i][1] == self.trump_suit)
                if not valid_move:
                    msg = f"You must play a {allowed_suit} card"
                    if any(card[1] == self.trump_suit for card in self.player.hand):
                        msg += " or a trump card"
                    self.message = msg + "."
                    self.shake_card_index = i
                    self.shake_start_time = pygame.time.get_ticks()
                    return

                if self.current_leader == "player":
                    self.start_player_card_animation(i, is_lead=True)
                else:
                    self.start_player_card_animation(i, is_lead=False)
                    
                break

    def _player_play_card(self, card_index, move_type="move"):
        """
        Pop a card from player's hand and set it as played_card.
        """
        try:
            card = self.player.hand.pop(card_index)
            self.player.played_card = card
            logger.debug("Player %s card: %s. New hand: %s", move_type, card, self.player.hand)
            return card
        except Exception as e:
            logger.error("Error in player %s: %s", move_type, e)
            return None

    def start_player_card_animation(self, card_index, is_lead=True):
        """
        Create a CardAnimation for the player's chosen card so it 'flies' to the table.
        Once complete, we handle the usual lead/follow logic in a callback.
        """

        # 1) Identify the card and its start position in the player's hand
        if card_index < 0 or card_index >= len(self.player.hand):
            return  # just in case

        selected_card = self.player.hand[card_index]

        # 2) Compute the card's current on-screen position
        #    (similar to handle_event's logic for card_rect)
        num_cards = len(self.player.hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2 + card_index*(CARD_WIDTH+CARD_SPACING)
        start_y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT)//2

        # 3) Decide the end position (Zone E if player is leading, or E if following).
        #    Actually, your code uses Zone E for the player's card, whether leading or following.
        end_rect = self.zones['E']
        end_x, end_y = end_rect.center

        # 4) Create the animation with a small duration in ms (e.g., 300)
        duration = 300
        if is_lead:
            on_complete = lambda: self._on_player_card_animation_done(card_index, was_lead=True)
        else:
            on_complete = lambda: self._on_player_card_animation_done(card_index, was_lead=False)

        self.card_animation = CardAnimation(
            card=selected_card,
            start_pos=(start_x, start_y),
            end_pos=(end_x, end_y),
            duration=duration,
            on_complete=on_complete
        )

    def _on_player_card_animation_done(self, card_index, was_lead=True):
        """
        This callback runs once the card animation finishes. 
        We remove the card from the player's hand, set played_card, 
        and do the typical lead or follow logic.
        """
        # Clear the CardAnimation from the game state
        anim = self.card_animation
        self.card_animation = None
        if not anim:
            return  # safety check

        # Pop the card
        try:
            card = self.player.hand.pop(card_index)
            self.player.played_card = card
            logger.debug("Player card animation done. Freed card: %s. Hand now: %s", card, self.player.hand)
        except Exception as e:
            logger.error("Error removing card from player's hand after animation: %s", e)
            return

        # If it was a lead:
        if was_lead:
            card  = self.opponent.play_card(self.get_game_state())
            self.start_opponent_card_animation(card, is_lead=False)
            logger.info("Opponent responded with: %s", card)
            self.trick_ready = True
            self.message = "Trick ready. Click 'End Trick' to resolve."
            self.current_leader = "player"
        else:
            # If it was a follow
            self.trick_ready = True
            self.message = "Trick ready. Click 'End Trick' to resolve."

        # (Done!)

    def start_opponent_card_animation(self, card, is_lead=True):
        """
        Animate the opponent's chosen card from its position in the top row (Zone A)
        down to the table (Zone D if leading, or E if following).
        """
        # 1) Find the index of 'card' in the opponent's hand (to compute its exact start position)
        try:
            idx = self.opponent.hand.index(card)
        except ValueError:
            # If it’s not in the hand, maybe we just skip animation or handle error
            logger.error("Attempted to animate an opponent card that isn't in the hand: %s", card)
            return

        # 2) Calculate the card’s start position on screen
        num_cards = len(self.opponent.hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.zones['A'].x + (self.zones['A'].width - total_width) // 2 + idx * (CARD_WIDTH + CARD_SPACING)
        start_y = self.zones['A'].y + (self.zones['A'].height - CARD_HEIGHT) // 2

        # 3) Decide the end position
        #    If the AI is leading a trick, it typically goes to Zone D. If following, maybe Zone D or E,
        #    but let’s assume D for the “opponent’s side”.
        end_rect = self.zones['D'] if is_lead else self.zones['D']
        # ^ If you do want it to appear in E when following, you can set end_rect = self.zones['E'] for follow
        end_x, end_y = end_rect.center

        # 4) Create the animation with a small duration (300 ms, for example)
        duration = 300
        if is_lead:
            on_complete = lambda: self._on_opponent_card_animation_done(card, was_lead=True)
        else:
            on_complete = lambda: self._on_opponent_card_animation_done(card, was_lead=False)

        self.card_animation = CardAnimation(
            card=card,
            start_pos=(start_x, start_y),
            end_pos=(end_x, end_y),
            duration=duration,
            on_complete=on_complete
        )

    def _on_opponent_card_animation_done(self, card, was_lead=True):
        """
        Called once the AI card finishes "flying" to the table.
        Remove the card from the opponent's hand and set opponent.played_card = card.
        If it's a lead, we do typical 'lead' logic (e.g. self.current_leader = "opponent").
        If it's a follow, we finalize the trick readiness.
        """
        anim = self.card_animation
        self.card_animation = None  # Clear it

        if not anim:
            return  # safety check

        # Remove the card from the AI's hand
        try:
            self.opponent.hand.remove(card)
            self.opponent.played_card = card
            logger.debug("Opponent card animation done. Freed card: %s. Opponent hand: %s", 
                        card, self.opponent.hand)
        except Exception as e:
            logger.error("Error removing card from opponent's hand after animation: %s", e)
            return

        if was_lead:
            # If the opponent was leading, set some helpful message
            self.current_leader = "opponent"
            self.trick_ready = False  # If you want the player to follow next
            self.message = "Opponent leads. Your turn to follow."
        else:
            # If it was a follow, you might do:
            self.trick_ready = True
            self.message = "Trick ready. Click 'End Trick' to resolve."

    def computer_lead(self):
        """
        Opponent (AI) leads a trick.
        """
        logger.info("Opponent's turn to lead started.")

        # AI checks for trump switch if it has the 9 of trump in first phase
        if self.first_phase and self.trump_card is not None:
            trump_nine = ("9", self.trump_suit)
            if trump_nine in self.opponent.hand:
                self.opponent.hand.remove(trump_nine)
                self.opponent.hand.append(self.trump_card)
                old_trump = self.trump_card
                self.trump_card = trump_nine
                logger.info("AI switched the trump! %s -> %s", old_trump, trump_nine)
                self.message = "Opponent switched the trump 9!"

        # AI checks for marriage in first phase
        if self.first_phase and not self.ongoing_animation:
            for card in self.opponent.hand:
                if card[0] in ("K", "Q"):
                    partner_rank = "Q" if card[0] == "K" else "K"
                    partner = (partner_rank, card[1])
                    if partner in self.opponent.hand and card[1] not in self.opponent.marriages_announced:
                        self.opponent.marriages_announced.add(card[1])
                        self.marriage_announcement = (card, partner)
                        self.marriage_time = pygame.time.get_ticks()
                        self.ongoing_animation = True
                        points = 40 if card[1] == self.trump_suit else 20
                        self.opponent.round_points += points
                        self.message = f"Opponent announces marriage in {card[1]}! +{points} points."
                        logger.info("Opponent announced a marriage in suit %s for %d points", card[1], points)
                        pygame.time.set_timer(MARRIAGE_DONE_EVENT, 3000)
                        break

        # If a marriage was just announced, wait until the animation finishes
        current_time = pygame.time.get_ticks()
        if self.marriage_announcement is not None:
            if (current_time - self.marriage_time) < 3000:
                logger.info("AI marriage announcement active; waiting to lead...")
                self.message = "Opponent announced a marriage. Waiting to lead..."
                return
            else:
                self.marriage_announcement = None
                self.ongoing_animation = False

        # Normal AI logic to choose a card to lead  
        lead_card = self.opponent.play_card(self.get_game_state())
        self.start_opponent_card_animation(lead_card, is_lead=True)
        logger.info("Opponent leads with card: %s.", lead_card)
        self.current_leader = "opponent"
        self.message = "Opponent leads. Your turn to follow."
        self.trick_ready = False

    def resolve_trick(self):
        """
        Determine the trick winner, award trick points, and proceed with drawing cards (if first phase).
        """
        logger.info(
            "Resolving trick. Player card: %s, Opponent card: %s.",
            self.player.played_card,
            self.opponent.played_card
        )
        winner = self.determine_trick_winner(self.player.played_card, self.opponent.played_card)
        trick_points = CARD_VALUES[self.player.played_card[0]] + CARD_VALUES[self.opponent.played_card[0]]
        logger.info("Trick points: %d.", trick_points)

        if winner == "player":
            self.player.round_points += trick_points
            self.player.tricks += 1
            self.message = f"You win the trick (+{trick_points})."
            self.current_leader = "player"
            self.player.won_cards.extend([self.player.played_card, self.opponent.played_card])
            logger.info("Player wins the trick. Round points: %d.", self.player.round_points)
        elif winner == "opponent":
            self.opponent.round_points += trick_points
            self.opponent.tricks += 1
            self.message = f"Opponent wins the trick (+{trick_points})."
            self.current_leader = "opponent"
            self.opponent.won_cards.extend([self.player.played_card, self.opponent.played_card])
            logger.info("Opponent wins the trick. Round points: %d.", self.opponent.round_points)
        else:
            self.message = "Tie trick! No points awarded."
            logger.debug("Trick ended in a tie.")

        self.player.played_card = None
        self.opponent.played_card = None
        self.trick_ready = False

        if self.first_phase:
            self.draw_cards(winner)
        self.check_round_end()

        if self.current_leader == "opponent":
            logger.info("Opponent is leading next.")
            self.computer_lead()

    def determine_trick_winner(self, player_card, opponent_card):
        """
        Decide who wins the current trick.
        """
        trump = self.trump_suit
        if self.current_leader == "player":
            leader_card = player_card
            follower_card = opponent_card
            leader = "player"
            follower = "opponent"
        else:
            leader_card = opponent_card
            follower_card = player_card
            leader = "opponent"
            follower = "player"

        lead_suit = leader_card[1]
        if leader_card[1] == trump and follower_card[1] != trump:
            return leader
        if follower_card[1] == trump and leader_card[1] != trump:
            return follower

        if follower_card[1] != lead_suit:
            return leader

        if CARD_VALUES[leader_card[0]] >= CARD_VALUES[follower_card[0]]:
            return leader
        else:
            return follower

    def draw_cards(self, trick_winner):
        """
        Winner draws first, then loser, if deck remains. 
        If the deck empties, switch to second phase.
        """
        logger.info("Drawing cards after trick. Winner: %s.", trick_winner)
        if self.deck:
            if trick_winner == "player":
                card = self.deck.pop()
                self.player.hand.append(card)
                logger.debug("Player draws card: %s", card)
                if not self.deck and self.trump_card is not None:
                    self.opponent.hand.append(self.trump_card)
                    logger.debug("Opponent draws trump card: %s", self.trump_card)
                    self.trump_card = None
                    self.player.round_points += 10
                    logger.info("Player gets 10-point last trick bonus.")
                elif self.deck:
                    card = self.deck.pop()
                    self.opponent.hand.append(card)
                    logger.debug("Opponent draws card: %s", card)
            else:  # Opponent is winner
                card = self.deck.pop()
                self.opponent.hand.append(card)
                logger.debug("Opponent draws card: %s", card)
                if not self.deck and self.trump_card is not None:
                    self.player.hand.append(self.trump_card)
                    logger.debug("Player draws trump card: %s", self.trump_card)
                    self.trump_card = None
                    self.opponent.round_points += 10
                    logger.info("Opponent gets 10-point last trick bonus.")
                elif self.deck:
                    card = self.deck.pop()
                    self.player.hand.append(card)
                    logger.debug("Player draws card: %s", card)

            if not self.deck:
                self.switch_to_second_phase()
        else:
            self.switch_to_second_phase()

    def check_round_end(self):
        """
        Check if the round has ended (both hands empty),
        then calculate and assign game points if so.
        """
        logger.info("Checking if round has ended.")
        if self.player.hand or self.opponent.hand:
            return  # Round continues

        logger.info("Both hands empty; round ended.")

        # If the player closed the game but didn't reach 66
        if self.game_closed:
            if self.player.round_points < 66:
                logger.info("Player closed without reaching 66 -> Opponent gets 1 game point.")
                self.opponent_game_points += 1
                self.message = "Closed but didn't reach 66: Opponent +1 game point."
                self.game_closed = False
                if self.player_game_points >= 11 or self.opponent_game_points >= 11:
                    self.message += " Game Over."
                    self.end_game_callback()
                else:
                    self.reset_round()
                return
            else:
                self.game_closed = False

        # Determine who reached 66 or more
        if self.player.round_points >= 66 or self.opponent.round_points >= 66:
            logger.info("At least one player reached 66. Player: %d, Opponent: %d",
                        self.player.round_points, self.opponent.round_points)
            if self.player.round_points > self.opponent.round_points:
                winner = "player"
                loser_points = self.opponent.round_points
                loser_tricks = self.opponent.tricks
            else:
                winner = "opponent"
                loser_points = self.player.round_points
                loser_tricks = self.player.tricks

            if loser_tricks == 0:
                game_points = 3
            elif loser_points < 33:
                game_points = 2
            else:
                game_points = 1
        else:
            # Neither reached 66
            logger.info("Neither reached 66: awarding 1 game point to the higher pointer.")
            if self.player.round_points > self.opponent.round_points:
                winner = "player"
            elif self.opponent.round_points > self.player.round_points:
                winner = "opponent"
            else:
                winner = None
            game_points = 1

        if winner:
            if winner == "player":
                self.player_game_points += game_points
                self.message = f"You win the round! (+{game_points} game point)"
            else:
                self.opponent_game_points += game_points
                self.message = f"Opponent wins the round! (+{game_points} game point)"
            logger.info(
                "Round winner: %s, game points: %d. Overall: Player %d - Opponent %d",
                winner,
                game_points,
                self.player_game_points,
                self.opponent_game_points
            )
        else:
            self.message = "Round ended in a tie. No game points awarded."
            logger.info("Round tied. No game points awarded.")

        if self.player_game_points >= 11 or self.opponent_game_points >= 11:
            self.message += " Game Over."
            logger.info("Game over. Final: Player %d - Opponent %d",
                        self.player_game_points, self.opponent_game_points)
            self.end_game_callback()
        else:
            self.reset_round()

    def reset_round(self):
        """
        Reset the round state, rebuild and shuffle the deck, deal new hands, reveal a new trump, etc.
        """
        logger.info("Resetting round.")
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        self.player.hand = [self.deck.pop() for _ in range(6)]
        self.opponent.hand = [self.deck.pop() for _ in range(6)]
        logger.debug("New hands. Player: %s, Opponent: %s", self.player.hand, self.opponent.hand)

        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None
        logger.info("New trump card: %s", self.trump_card)

        self.player.round_points = 0
        self.opponent.round_points = 0
        self.player.tricks = 0
        self.opponent.tricks = 0
        self.first_phase = True
        self.current_leader = "player"
        self.player.played_card = None
        self.opponent.played_card = None
        self.trick_ready = False
        self.player.marriage_pending = False
        self.marriage_announcement = None
        self.marriage_time = None
        self.player.marriages_announced = set()
        self.opponent.marriages_announced = set()
        self.game_closed = False
        self.message += " New round started. Your turn to lead."
        logger.info("Round reset complete.")

    def close_game(self):
        """
        Player closes the game, forcing second phase immediately.
        """
        logger.info("Player chose to close the game.")
        self.first_phase = False
        self.game_closed = True
        self.message = "You closed the game. Second phase rules apply."

    def switch_trump(self):
        """
        Player attempts to switch the trump (9 with the face-up trump card).
        """
        logger.info("Player attempting trump switch.")
        if self.current_leader != "player":
            self.message = "You can only switch trump 9 when you lead."
            logger.warning("Trump switch failed: Player is not the leader.")
            return

        trump9 = ("9", self.trump_suit)
        if trump9 in self.player.hand:
            self.player.hand.remove(trump9)
            self.player.hand.append(self.trump_card)
            self.trump_card = trump9
            self.message = "Trump 9 switch successful!"
            logger.info("Trump switch successful.")
        else:
            self.message = "You do not have the trump 9."
            logger.warning("Trump switch failed: Player does not have trump 9.")

    def announce_marriage(self):
        """
        Player triggers the marriage announcement process.
        """
        logger.info("Player requested marriage announcement.")
        if self.current_leader != "player":
            self.message = "You can only announce marriage when you lead."
            logger.warning("Marriage announcement failed: Not in lead.")
            return
        self.player.marriage_pending = True
        self.message = "Marriage pending: click a King or Queen from your hand."

    def pause_game(self):
        """
        Pause callback to switch the game state to 'pause'.
        """
        logger.info("Pause game triggered by player.")
        if hasattr(self, 'pause_callback'):
            self.pause_callback()
        else:
            logger.error("Pause callback not defined in GamePlay.")

class CardAnimation:
    def __init__(self, card, start_pos, end_pos, duration, on_complete=None):
        """
        :param card: The (rank, suit) tuple
        :param start_pos: (x, y) where the card starts
        :param end_pos: (x, y) where the card ends
        :param duration: total milliseconds for the animation
        :param on_complete: callback function to run once finished
        """
        self.card = card
        self.start_x, self.start_y = start_pos
        self.end_x, self.end_y = end_pos
        self.duration = duration
        self.on_complete = on_complete
        self.start_time = pygame.time.get_ticks()  # record the start time

    def update_position(self):
        """Compute the current position based on elapsed time and duration."""
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        progress = elapsed / self.duration
        if progress > 1.0:
            progress = 1.0

        # Linear interpolation (lerp) along x and y
        current_x = self.start_x + (self.end_x - self.start_x) * progress
        current_y = self.start_y + (self.end_y - self.start_y) * progress
        return (current_x, current_y), (progress >= 1.0)