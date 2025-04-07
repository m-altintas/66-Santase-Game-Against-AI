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
        logger.debug("Screen dimensions: %d x %d", self.screen_width, self.screen_height)
        
        self.developer_mode = developer_mode

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

        # Build deck and shuffle.
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        logger.debug("Deck built and shuffled with %d cards.", len(self.deck))

        # Create players.
        self.player = HumanPlayer()
        self.opponent = AIPlayer(strategy=ai_strategy)

        # Deal cards (6 cards each).
        self.player.hand = [self.deck.pop() for _ in range(6)]
        self.opponent.hand = [self.deck.pop() for _ in range(6)]
        logger.debug("Player hand: %s", self.player.hand)
        logger.debug("Opponent hand: %s", self.opponent.hand)

        # Reveal trump card.
        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None
        logger.info("Trump card revealed: %s", self.trump_card)

        # Reset played cards.
        self.player.played_card = None
        self.opponent.played_card = None

        # Game phase and trick state.
        self.trick_ready = False
        self.first_phase = True  # Drawing from deck is active.
        # Who leads the trick: "player" or "opponent".
        self.current_leader = "player"

        # Round points and overall game points.
        self.player.round_points = 0
        self.opponent.round_points = 0
        self.player_game_points = 0
        self.opponent_game_points = 0

        # Animation and marriage flags.
        self.ongoing_animation = False
        self.marriage_announcement = None  # Tuple of two cards (if marriage is announced)
        self.marriage_time = None
        self.game_closed = False
        self.message = "Your turn to lead."

        # Initialize UI zones.
        self.zones = self.init_zones()

        # Buttons for close, trump switch, and marriage.
        self.close_button = Button(self.zones['K'], "Close", self.close_game, pygame.font.SysFont('Arial', 20))
        self.switch_button = Button(self.zones['L'], "Switch", self.switch_trump, pygame.font.SysFont('Arial', 20))
        self.marriage_button = Button(self.zones['M'], "Marriage", self.announce_marriage, pygame.font.SysFont('Arial', 20))

        # Shake animation variables.
        self.shake_card_index = None
        self.shake_start_time = 0
        self.shake_duration = 500

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
        if self.current_leader == "player" and self.player.played_card:
            allowed_suit = self.player.played_card[1]
            leader_card = self.player.played_card
        elif self.current_leader == "opponent" and self.opponent.played_card:
            allowed_suit = self.opponent.played_card[1]
            leader_card = self.opponent.played_card
        else:
            allowed_suit = None
            leader_card = None

        state = {
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
        }
        return state

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        font_small = pygame.font.SysFont('Arial', 20)

        # --- Draw Opponent's Hand (Zone A) as Card Backs ---
        if self.opponent.hand:
            num_cards = len(self.opponent.hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.zones['A'].x + (self.zones['A'].width - total_width) // 2
            y = self.zones['A'].y + (self.zones['A'].height - CARD_HEIGHT) // 2
            for i, card in enumerate(self.opponent.hand):
                pos = (start_x + i * (CARD_WIDTH + CARD_SPACING), y)
                if self.developer_mode:
                    # In developer mode, show the actual card image.
                    img = self.card_images.get(card)
                    if img:
                        self.screen.blit(img, pos)
                    else:
                        self.screen.blit(self.card_back, pos)
                else:
                    # Normal mode: display the card back.
                    self.screen.blit(self.card_back, pos)

        # --- Draw Player's Hand (Zone B) ---
        if self.player.hand:
            num_cards = len(self.player.hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
            y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2

            allowed_suit = None
            # If opponent led and we must follow suit.
            if not self.first_phase and self.current_leader == "opponent" and self.opponent.played_card:
                allowed_suit = self.opponent.played_card[1]

            for i, card in enumerate(self.player.hand):
                pos_x = start_x + i * (CARD_WIDTH + CARD_SPACING)
                # Apply shake animation if needed.
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
                    # (Basic validation: if player has cards of allowed suit or trump.)
                    if any(c[1] == allowed_suit for c in self.player.hand):
                        valid_move = (card[1] == allowed_suit)
                    elif any(c[1] == self.trump_suit for c in self.player.hand):
                        valid_move = (card[1] == self.trump_suit)
                if not valid_move:
                    card_img = card_img.copy()
                    card_img.set_alpha(100)
                self.screen.blit(card_img, pos)

        # --- Draw Marriage Announcement, Played Cards, etc. ---
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

        # --- Draw Played Cards (Zone C) ---
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

        # --- Draw "End Trick" Button (Zone F) ---
        pygame.draw.rect(self.screen, (180, 180, 250), self.zones['F'])
        et_text = font_small.render("End Trick", True, (0, 0, 0))
        et_rect = et_text.get_rect(center=self.zones['F'].center)
        self.screen.blit(et_text, et_rect)

        # --- Draw Deck, Trump Card, and Remaining Count ---
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

        # --- Draw Additional Buttons ---
        if self.first_phase:
            self.close_button.draw(self.screen)
        else:
            sp_text = font_small.render("2nd Phase", True, (0, 0, 0))
            sp_rect = sp_text.get_rect(center=self.zones['K'].center)
            pygame.draw.rect(self.screen, (200, 250, 200), self.zones['K'])
            self.screen.blit(sp_text, sp_rect)
        self.switch_button.draw(self.screen)
        self.marriage_button.draw(self.screen)

        # --- Draw Trump Suit Text (Zone T) ---
        trump_text = f"Trump Suit: ({self.trump_suit})" if self.trump_suit else "No Trump"
        trump_surface = font_small.render(trump_text, True, (0, 0, 0))
        trump_rect = trump_surface.get_rect(center=self.zones['T'].center)
        pygame.draw.rect(self.screen, (250, 250, 250), self.zones['T'])
        self.screen.blit(trump_surface, trump_rect)

        # --- Draw Overall Game Points (Zone OG) ---
        game_points_text = f"Game: {self.player_game_points} - {self.opponent_game_points}"
        game_points_surface = font_small.render(game_points_text, True, (0, 0, 0))
        game_points_rect = game_points_surface.get_rect(center=self.zones['OG'].center)
        pygame.draw.rect(self.screen, (250, 250, 200), self.zones['OG'])
        self.screen.blit(game_points_surface, game_points_rect)

        # --- Draw Round Points (Zone G) ---
        pygame.draw.rect(self.screen, (250, 200, 200), self.zones['G'])
        points_text = font_small.render(f"Pts: {self.player.round_points}-{self.opponent.round_points}", True, (0, 0, 0))
        points_rect = points_text.get_rect(center=self.zones['G'].center)
        self.screen.blit(points_text, points_rect)

        # --- Draw Player's Won Cards (Zone W) ---
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

    def handle_event(self, event):
        if self.ongoing_animation:
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
        if not self.first_phase and self.current_leader == "opponent" and self.opponent.played_card:
            allowed_suit = self.opponent.played_card[1]
            logger.debug("Allowed suit for following: %s", allowed_suit)

        num_cards = len(self.player.hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
        y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2

        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i * (CARD_WIDTH + CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                logger.info("Player clicked on card at index %d.", i)
                # If marriage is pending, process that first.
                if self.player.marriage_pending:
                    selected_card = self.player.hand[i]
                    if selected_card[0] not in ("K", "Q"):
                        self.player.marriage_pending = False
                        self.message = "Marriage cancelled."
                        return
                    suit = selected_card[1]
                    if suit in self.player.marriages_announced:
                        self.player.marriage_pending = False
                        self.message = f"Marriage for {suit} already announced. Marriage cancelled."
                        return
                    partner = ("Q", suit) if selected_card[0] == "K" else ("K", suit)
                    if partner not in self.player.hand:
                        self.player.marriage_pending = False
                        self.message = "Matching card for marriage not found. Marriage cancelled."
                        return
                    self.marriage_announcement = (selected_card, partner)
                    self.marriage_time = pygame.time.get_ticks()
                    self.player.marriage_pending = False
                    self.ongoing_animation = True
                    self.player.marriages_announced.add(suit)
                    points = 40 if suit == self.trump_suit else 20
                    self.player.round_points += points
                    self.message = f"Marriage announced in {suit}! +{points} points."
                    return

                # Otherwise, process as a normal move.
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
                    self.player_lead(i)
                else:
                    self.player_follow(i)
                break

    def _player_play_card(self, card_index, move_type="move"):
        try:
            card = self.player.hand.pop(card_index)
            self.player.played_card = card
            logger.debug("Player %s card: %s. Updated hand: %s", move_type, card, self.player.hand)
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
        self.opponent.played_card = self.opponent.play_card(state)
        logger.info("Opponent responded with: %s", self.opponent.played_card)
        self.trick_ready = True
        self.message = "Trick ready. Click 'End Trick' to resolve."
        self.current_leader = "player"

    def player_follow(self, card_index):
        logger.info("Player is following with card at index %d.", card_index)
        card = self._player_play_card(card_index, "follow")
        if card is None:
            return
        logger.debug("Player followed with card: %s. Updated hand: %s", card, self.player.hand)
        self.trick_ready = True
        self.message = "Trick ready. Click 'End Trick' to resolve."

    def player_follow_by_click(self, pos):
        logger.info("Processing player follow by click at position: %s", pos)
        num_cards = len(self.player.hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.zones['B'].x + (self.zones['B'].width - total_width) // 2
        y = self.zones['B'].y + (self.zones['B'].height - CARD_HEIGHT) // 2
        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i * (CARD_WIDTH + CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                self.player_follow(i)
                break

    def computer_lead(self):
        logger.info("Opponent's turn to lead started.")
        current_time = pygame.time.get_ticks()
        if self.marriage_announcement is not None:
            delta = current_time - self.marriage_time
            if delta < 3000:
                logger.info("Marriage announcement active (delta: %d ms). Waiting to lead...", delta)
                self.message = "Opponent announced marriage. Waiting to lead..."
                return
            else:
                logger.debug("Marriage announcement period elapsed; clearing announcement.")
                self.marriage_announcement = None

        # AI marriage logic can be added here if desired.

        state = self.get_game_state()
        self.opponent.played_card = self.opponent.play_card(state)
        logger.info("Opponent leads with card: %s.", self.opponent.played_card)
        self.current_leader = "opponent"
        self.message = "Opponent leads. Your turn to follow."
        self.trick_ready = False

    def resolve_trick(self):
        logger.info("Resolving trick. Player card: %s, Opponent card: %s.", self.player.played_card, self.opponent.played_card)
        winner = self.determine_trick_winner(self.player.played_card, self.opponent.played_card)
        trick_points = CARD_VALUES[self.player.played_card[0]] + CARD_VALUES[self.opponent.played_card[0]]
        logger.info("Trick points calculated: %d.", trick_points)
        if winner == "player":
            self.player.round_points += trick_points
            self.player.tricks += 1
            self.message = f"You win the trick and earn {trick_points} points!"
            self.current_leader = "player"
            self.player.won_cards.extend([self.player.played_card, self.opponent.played_card])
            logger.info("Player wins the trick. New round points: %d.", self.player.round_points)
        elif winner == "opponent":
            self.opponent.round_points += trick_points
            self.opponent.tricks += 1
            self.message = f"Opponent wins the trick and earns {trick_points} points!"
            self.current_leader = "opponent"
            self.opponent.won_cards.extend([self.player.played_card, self.opponent.played_card])
            logger.info("Opponent wins the trick. New round points: %d.", self.opponent.round_points)
        else:
            self.message = "Tie trick! No points awarded."
            logger.info("Trick ended in a tie.")

        self.player.played_card = None
        self.opponent.played_card = None
        self.trick_ready = False

        if self.first_phase:
            self.draw_cards(winner)
        self.check_round_end()

        if self.current_leader == "opponent":
            logger.info("Opponent is leading. Initiating opponent lead.")
            self.computer_lead()

    def determine_trick_winner(self, player_card, opponent_card):
        logger.debug("Determining trick winner. Player card: %s, Opponent card: %s", player_card, opponent_card)
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
            logger.debug("Leader card is trump; leader wins.")
            return leader
        if follower_card[1] == trump and leader_card[1] != trump:
            logger.debug("Follower card is trump; follower wins.")
            return follower

        if follower_card[1] != lead_suit:
            logger.debug("Follower did not follow lead suit; leader wins.")
            return leader

        logger.debug("Comparing card values: Leader %d vs. Follower %d", CARD_VALUES[leader_card[0]], CARD_VALUES[follower_card[0]])
        if CARD_VALUES[leader_card[0]] >= CARD_VALUES[follower_card[0]]:
            logger.debug("Leader wins based on card value.")
            return leader
        else:
            logger.debug("Follower wins based on card value.")
            return follower

    def draw_cards(self, trick_winner):
        logger.info("Drawing cards after trick. Winner: %s.", trick_winner)
        if self.deck:
            if trick_winner == "player":
                card = self.deck.pop()
                self.player.hand.append(card)
                logger.debug("Player draws card: %s", card)
                if not self.deck and self.trump_card is not None:
                    self.opponent.hand.append(self.trump_card)
                    logger.debug("Deck empty; Opponent draws trump card: %s", self.trump_card)
                    self.trump_card = None
                    self.player.round_points += 10
                    logger.info("Extra 10 points awarded to player for last trick bonus.")
                elif self.deck:
                    card = self.deck.pop()
                    self.opponent.hand.append(card)
                    logger.debug("Opponent draws card: %s", card)
            elif trick_winner == "opponent":
                card = self.deck.pop()
                self.opponent.hand.append(card)
                logger.debug("Opponent draws card: %s", card)
                if not self.deck and self.trump_card is not None:
                    self.player.hand.append(self.trump_card)
                    logger.debug("Deck empty; Player draws trump card: %s", self.trump_card)
                    self.trump_card = None
                    self.opponent.round_points += 10
                    logger.info("Extra 10 points awarded to opponent for last trick bonus.")
                elif self.deck:
                    card = self.deck.pop()
                    self.player.hand.append(card)
                    logger.debug("Player draws card: %s", card)
            if not self.deck:
                self.first_phase = False
                logger.info("Deck exhausted. Switching to second phase.")
        else:
            self.first_phase = False
            logger.info("No deck remaining. Switching to second phase.")

    def check_round_end(self):
        logger.info("Checking if round has ended.")
        if len(self.player.hand) > 0 or len(self.opponent.hand) > 0:
            logger.debug("Round not ended; Player has %d cards, Opponent has %d cards.", len(self.player.hand), len(self.opponent.hand))
            return

        logger.info("Both hands empty; round has ended.")

        if self.game_closed:
            logger.info("Game was closed by player.")
            if self.player.round_points < 66:
                logger.info("Player closed the game without reaching 66. Awarding 1 game point to opponent.")
                self.opponent_game_points += 1
                self.message = "You closed the game but didn't reach 66. Opponent gets 1 game point as penalty."
                self.game_closed = False
                if self.player_game_points >= 11 or self.opponent_game_points >= 11:
                    self.message += " Game Over."
                    logger.info("Game over. Final scores - Player: %d, Opponent: %d", self.player_game_points, self.opponent_game_points)
                    self.end_game_callback()
                else:
                    logger.info("Resetting round after penalty.")
                    self.reset_round()
                return
            else:
                logger.info("Game closed but player reached 66. Clearing game_closed flag.")
                self.game_closed = False

        if self.player.round_points >= 66 or self.opponent.round_points >= 66:
            logger.info("At least one player reached 66 points (Player: %d, Opponent: %d).", self.player.round_points, self.opponent.round_points)
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
                logger.info("Opponent won 0 tricks. Awarding 3 game points to %s.", winner)
            elif loser_points < 33:
                game_points = 2
                logger.info("Opponent has less than 33 points. Awarding 2 game points to %s.", winner)
            else:
                game_points = 1
                logger.info("Awarding 1 game point to %s.", winner)
        else:
            logger.info("Neither player reached 66 points (Player: %d, Opponent: %d).", self.player.round_points, self.opponent.round_points)
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
            logger.info("Round winner: %s. Awarded %d game point(s). Overall scores - Player: %d, Opponent: %d",
                        winner, game_points, self.player_game_points, self.opponent_game_points)
        else:
            self.message = "Round ended in a tie. No game points awarded."
            logger.info("Round tied. No game points awarded.")

        if self.player_game_points >= 11 or self.opponent_game_points >= 11:
            self.message += " Game Over."
            logger.info("Game over. Final scores - Player: %d, Opponent: %d", self.player_game_points, self.opponent_game_points)
            self.end_game_callback()
        else:
            logger.info("Resetting round for next play. Overall scores - Player: %d, Opponent: %d", self.player_game_points, self.opponent_game_points)
            self.reset_round()

    def reset_round(self):
        logger.info("Resetting round.")
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        logger.debug("Deck rebuilt and shuffled. Total cards: %d", len(self.deck))
        self.player.hand = [self.deck.pop() for _ in range(6)]
        self.opponent.hand = [self.deck.pop() for _ in range(6)]
        logger.debug("New hands dealt. Player: %s, Opponent: %s", self.player.hand, self.opponent.hand)
        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None
        logger.info("New trump card: %s", self.trump_card)
        self.player.round_points = 0
        self.opponent.round_points = 0
        self.player.tricks = 0
        self.opponent.tricks = 0
        logger.debug("Round points and trick counts reset.")
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
        logger.info("Player chose to close the game (end first phase).")
        self.first_phase = False
        self.game_closed = True
        self.message = "You closed the game. Now in second phase, follow suit if possible."
        logger.debug("Game closed flag set; switching to second phase.")

    def switch_trump(self):
        logger.info("Player attempting trump switch.")
        if self.current_leader != "player":
            self.message = "You can only switch trump 9 when you are leading."
            logger.warning("Trump switch failed: player is not the leader.")
            return

        trump9 = ("9", self.trump_suit)
        if trump9 in self.player.hand:
            self.player.hand.remove(trump9)
            self.player.hand.append(self.trump_card)
            self.trump_card = trump9
            self.message = "Trump 9 switch successful!"
            logger.info("Trump switch successful: Player switched trump card with trump 9.")
        else:
            self.message = "You do not have the trump 9."
            logger.warning("Trump switch failed: Player does not have trump 9.")

    def announce_marriage(self):
        logger.info("Player requested marriage announcement.")
        if self.current_leader != "player":
            self.message = "You can only announce marriage when you're in lead."
            logger.warning("Marriage announcement failed: player is not in lead.")
            return
        self.player.marriage_pending = True
        self.message = "Marriage pending: click a King or Queen from your hand to announce marriage."
        logger.debug("Marriage pending flag set; waiting for player input.")

    def pause_game(self):
        logger.info("Pause game triggered by player.")
        if hasattr(self, 'pause_callback'):
            self.pause_callback()
            logger.info("Pause callback invoked; game state should now be 'pause'.")
        else:
            logger.error("Pause callback not defined in GamePlay.")