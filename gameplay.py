import pygame
import random
import math

from constants import CARD_HEIGHT, CARD_WIDTH, CARD_SPACING, MARGIN, CARD_VALUES
from ui import Button
from ai import JustRandom

# ---------------------------
# GamePlay Class Definition (Revised Rules & Draw Modification)
# ---------------------------
class GamePlay:
    def __init__(self, screen, end_game_callback):
        self.end_game_callback = end_game_callback
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()

        # Load background image (or fallback)
        try:
            self.background = pygame.image.load("backgrounds/game_background.jpg")
            self.background = pygame.transform.scale(self.background, (self.screen_width, self.screen_height))
        except Exception as e:
            print("Error loading background:", e)
            self.background = pygame.Surface((self.screen_width, self.screen_height))
            self.background.fill((0, 128, 0))

        # Load card back image.
        try:
            self.card_back = pygame.image.load("cards/back.png")
            self.card_back = pygame.transform.scale(self.card_back, (CARD_WIDTH, CARD_HEIGHT))
        except Exception as e:
            print("Error loading card back:", e)
            self.card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            self.card_back.fill((0, 0, 128))

        # Load card images.
        self.card_images = {}
        self.ranks = ["9", "J", "Q", "K", "10", "A"]
        self.suits = ["H", "D", "C", "S"]
        for suit in self.suits:
            for rank in self.ranks:
                filename = f"cards/{rank}{suit}.png"
                try:
                    img = pygame.image.load(filename)
                    img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                    self.card_images[(rank, suit)] = img
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    placeholder = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
                    placeholder.fill((200, 200, 200))
                    self.card_images[(rank, suit)] = placeholder

        # Build a 24-card deck.
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)

        # Deal cards in two rounds of 3 cards each.
        self.player_hand = [self.deck.pop() for _ in range(3)]
        self.computer_hand = [self.deck.pop() for _ in range(3)]
        self.player_hand += [self.deck.pop() for _ in range(3)]
        self.computer_hand += [self.deck.pop() for _ in range(3)]

        # Reveal trump card.
        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None

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
        
        self.marriage_pending = False       # Waiting for human to select a card for marriage
        self.marriage_announcement = None     # Will hold a tuple of the two cards forming the marriage
        self.marriage_time = None             # Timestamp when marriage was announced
        self.player_marriages_announced = set()      # A set of suits already announced by the human.
        self.computer_marriages_announced = set()    # A set of suits already announced by the computer.
        
        self.player_won_cards = []
        self.computer_won_cards = []
        
        self.game_closed = False

        # Feedback message.
        self.message = "Your turn to lead."

        # Create the opponent instance.
        self.opponent = JustRandom()

        # ---------------------------
        # Define Zones (with Equal Margins)
        # ---------------------------
        # Zone A: Opponent’s hand.
        self.A_rect = pygame.Rect(MARGIN, MARGIN, self.screen_width - 2 * MARGIN, 150)
        # Zone B: Player’s hand.
        self.B_rect = pygame.Rect(MARGIN, self.screen_height - MARGIN - 150, self.screen_width - 2 * MARGIN, 150)
        # Zone C: Central area for trick cards.
        self.C_rect = pygame.Rect(390, 260, 500, 200)
        # Inside C: D (opponent’s played card) and E (player’s played card).
        self.D_rect = pygame.Rect(self.C_rect.x, self.C_rect.y, self.C_rect.width // 2, self.C_rect.height)
        self.E_rect = pygame.Rect(self.C_rect.x + self.C_rect.width // 2, self.C_rect.y, self.C_rect.width // 2, self.C_rect.height)
        # Zone F: “End Trick” button.
        self.F_rect = pygame.Rect(self.C_rect.right + 10, self.C_rect.y + (self.C_rect.height - 50) // 2, 100, 50)

        # Group the deck (draw pile) and trump card on the left, centered vertically.
        group_height = 150
        group_y = (self.screen_height - group_height) // 2
        self.I_rect = pygame.Rect(MARGIN, group_y, 100, 150)       # Deck.
        self.H_rect = pygame.Rect(MARGIN + 100 + 10, group_y, 100, 150)  # Trump card.
        
        # New Zone T: Trump suit text, to the right of Zone H.
        self.T_rect = pygame.Rect(self.H_rect.right + 10, self.H_rect.y + (self.H_rect.height // 2) - 20, 150, 40)

        # (Keep existing zones for remaining deck count, etc.)
        # For the round points, you might have something like:
        self.G_rect = pygame.Rect(self.screen_width - MARGIN - 100, self.B_rect.y - 70, 100, 40)
        # New Zone OG: Overall game points display, placed above Zone G.
        self.OG_rect = pygame.Rect(self.screen_width - MARGIN - 100, self.G_rect.y - 50, 100, 40)
        
        # New Zone W: Display won cards by the player in the round.
        # For instance, a rectangle in the bottom-right corner.
        self.W_rect = pygame.Rect(self.screen_width - MARGIN - 200, self.B_rect.y, 180, 150)

        # Zone J: Remaining deck count.
        self.J_rect = pygame.Rect(MARGIN, self.B_rect.y - 70, 80, 40)
        # New Zone K: Close button, placed under Zone J.
        self.K_rect = pygame.Rect(MARGIN, self.J_rect.bottom + 10, 80, 40)
        # New Zone L: Switch button, placed to the right of Zone J.
        self.L_rect = pygame.Rect(self.J_rect.right + 10, self.J_rect.y, 80, 40)
        # New Zone M: Marriage button, placed under Zone L.
        self.M_rect = pygame.Rect(self.L_rect.x, self.L_rect.bottom + 10, 80, 40)
        # Zone G: Points display remains unchanged.
        self.G_rect = pygame.Rect(self.screen_width - MARGIN - 100, self.B_rect.y - 70, 100, 40)

        # Close button for Zone K.
        self.close_button = Button(self.K_rect, "Close", self.close_game, pygame.font.SysFont('Arial', 20))
        self.switch_button = Button(self.L_rect, "Switch", self.switch_trump, pygame.font.SysFont('Arial', 20))
        self.marriage_button = Button(self.M_rect, "Marriage", self.announce_marriage, pygame.font.SysFont('Arial', 20))
        
        # Variables for shake animation
        self.shake_card_index = None   # The index of the card to shake (if any)
        self.shake_start_time = 0        # When the shake started (in milliseconds)
        self.shake_duration = 500        # Duration of the shake animation in milliseconds

    def get_game_state(self):
        """
        Return a dictionary with current game state details.
        """
        return {
            "player_played": self.player_played,
            "player_round_points": self.player_round_points,
            "computer_round_points": self.computer_round_points,
            "remaining_deck": self.deck.copy(),
            "trump_card": self.trump_card,
            "trump_suit": self.trump_suit,
            "computer_hand": self.computer_hand.copy(),
            "player_hand": self.player_hand.copy(),
            "first_phase": self.first_phase,
            "current_leader": self.current_leader
        }

    def draw(self):
        # Draw the background.
        self.screen.blit(self.background, (0, 0))
        font_small = pygame.font.SysFont('Arial', 20)

        # --- Draw Opponent’s Hand (Zone A) as Card Backs ---
        if self.computer_hand:
            num_cards = len(self.computer_hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.A_rect.x + (self.A_rect.width - total_width) // 2
            y = self.A_rect.y + (self.A_rect.height - CARD_HEIGHT) // 2
            for i in range(num_cards):
                pos = (start_x + i * (CARD_WIDTH + CARD_SPACING), y)
                self.screen.blit(self.card_back, pos)

        # --- Draw Player’s Hand (Zone B) with Grey-out & Shake Effects ---
        if self.player_hand:
            num_cards = len(self.player_hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.B_rect.x + (self.B_rect.width - total_width) // 2
            y = self.B_rect.y + (self.B_rect.height - CARD_HEIGHT) // 2

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
        if self.marriage_announcement is not None:
            current_time = pygame.time.get_ticks()
            if current_time - self.marriage_time < 3000:
                card1, card2 = self.marriage_announcement
                img1 = self.card_images.get(card1)
                img2 = self.card_images.get(card2)
                if img1 and img2:
                    total_width = CARD_WIDTH * 2 + 10
                    x = self.C_rect.centerx - total_width // 2
                    y = self.C_rect.centery - CARD_HEIGHT // 2
                    self.screen.blit(img1, (x, y))
                    self.screen.blit(img2, (x + CARD_WIDTH + 10, y))
            else:
                self.marriage_announcement = None

        # Draw played cards (Zone C).
        if self.computer_played:
            img = self.card_images.get(self.computer_played)
            if img:
                rect = img.get_rect(center=self.D_rect.center)
                self.screen.blit(img, rect)
        if self.player_played:
            img = self.card_images.get(self.player_played)
            if img:
                rect = img.get_rect(center=self.E_rect.center)
                self.screen.blit(img, rect)

        # Draw the "End Trick" button (Zone F).
        pygame.draw.rect(self.screen, (180, 180, 250), self.F_rect)
        et_text = font_small.render("End Trick", True, (0, 0, 0))
        et_rect = et_text.get_rect(center=self.F_rect.center)
        self.screen.blit(et_text, et_rect)

        # Draw deck (Zone I), trump card (Zone H), remaining deck count (Zone J), and other UI elements.
        if self.deck:
            deck_img = pygame.transform.scale(self.card_back, (self.I_rect.width, self.I_rect.height))
            self.screen.blit(deck_img, (self.I_rect.x, self.I_rect.y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.I_rect)
        if self.trump_card:
            trump_img = pygame.transform.scale(self.card_images.get(self.trump_card), (self.H_rect.width, self.H_rect.height))
            self.screen.blit(trump_img, (self.H_rect.x, self.H_rect.y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.H_rect)
        pygame.draw.rect(self.screen, (250, 250, 200), self.J_rect)
        count_text = font_small.render(str(len(self.deck)), True, (0, 0, 0))
        count_rect = count_text.get_rect(center=self.J_rect.center)
        self.screen.blit(count_text, count_rect)

        # Draw additional buttons.
        if self.first_phase:
            self.close_button.draw(self.screen)
        else:
            sp_text = font_small.render("2nd Phase", True, (0, 0, 0))
            sp_rect = sp_text.get_rect(center=self.K_rect.center)
            pygame.draw.rect(self.screen, (200, 250, 200), self.K_rect)
            self.screen.blit(sp_text, sp_rect)
        self.switch_button.draw(self.screen)
        self.marriage_button.draw(self.screen)

        # Draw trump suit text (Zone T).
        trump_text = f"Trump Suit: ({self.trump_suit})" if self.trump_suit else "No Trump"
        trump_surface = font_small.render(trump_text, True, (0, 0, 0))
        trump_rect = trump_surface.get_rect(center=self.T_rect.center)
        pygame.draw.rect(self.screen, (250, 250, 250), self.T_rect)
        self.screen.blit(trump_surface, trump_rect)

        # Draw overall game points (Zone OG).
        game_points_text = f"Game: {self.player_game_points} - {self.computer_game_points}"
        game_points_surface = font_small.render(game_points_text, True, (0, 0, 0))
        game_points_rect = game_points_surface.get_rect(center=self.OG_rect.center)
        pygame.draw.rect(self.screen, (250, 250, 200), self.OG_rect)
        self.screen.blit(game_points_surface, game_points_rect)

        # Draw round points (Zone G).
        pygame.draw.rect(self.screen, (250, 200, 200), self.G_rect)
        points_text = font_small.render(f"Pts: {self.player_round_points}-{self.computer_round_points}", True, (0, 0, 0))
        points_rect = points_text.get_rect(center=self.G_rect.center)
        self.screen.blit(points_text, points_rect)

        # Draw the player's won cards (Zone W).
        if self.player_won_cards:
            offset = 20  # Overlap offset.
            x = self.W_rect.x
            y = self.W_rect.y
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

        # Draw feedback message.
        msg_text = font_small.render(self.message, True, (255, 255, 255))
        msg_rect = msg_text.get_rect(center=(self.screen_width // 2, self.B_rect.y - 30))
        self.screen.blit(msg_text, msg_rect)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        # Let the buttons process the event first.
        self.close_button.handle_event(event)
        self.switch_button.handle_event(event)
        self.marriage_button.handle_event(event)

        pos = event.pos

        # If the "End Trick" button is clicked, process it immediately.
        if self.F_rect.collidepoint(pos):
            if self.trick_ready:
                self.resolve_trick()
            return

        # If a trick is in progress, ignore further clicks.
        if self.trick_ready:
            return

        # Determine the allowed suit when in the second phase.
        allowed_suit = None
        if not self.first_phase and self.current_leader == "computer" and self.computer_played:
            allowed_suit = self.computer_played[1]

        # Determine what valid moves are based on the player's hand.
        if allowed_suit:
            player_has_follow = any(card[1] == allowed_suit for card in self.player_hand)
            player_has_trump = any(card[1] == self.trump_suit for card in self.player_hand)
        else:
            player_has_follow = False
            player_has_trump = False

        num_cards = len(self.player_hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.B_rect.x + (self.B_rect.width - total_width) // 2
        y = self.B_rect.y + (self.B_rect.height - CARD_HEIGHT) // 2

        # Loop over each card in the player's hand to see if it was clicked.
        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i * (CARD_WIDTH + CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                # If a marriage announcement is pending, handle that first.
                if self.marriage_pending:
                    selected_card = self.player_hand[i]
                    # Check if the card is eligible for marriage (must be "K" or "Q").
                    if selected_card[0] not in ("K", "Q"):
                        self.marriage_pending = False
                        self.message = "Invalid card selection for marriage. Marriage cancelled."
                        return  # Cancel the marriage announcement.
                    suit = selected_card[1]
                    # Cancel if marriage for this suit has already been announced.
                    if suit in self.player_marriages_announced:
                        self.marriage_pending = False
                        self.message = f"Marriage for suit {suit} has already been announced. Marriage cancelled."
                        return
                    # Determine the required partner: if King then partner must be Queen; if Queen then partner must be King.
                    if selected_card[0] == "K":
                        partner = ("Q", suit)
                    elif selected_card[0] == "Q":
                        partner = ("K", suit)
                    # If the matching partner is not in the hand, cancel marriage.
                    if partner not in self.player_hand:
                        self.marriage_pending = False
                        self.message = "You don't have the matching card for marriage. Marriage cancelled."
                        return
                    # Valid marriage: record the announcement.
                    self.marriage_announcement = (selected_card, partner)
                    self.marriage_time = pygame.time.get_ticks()
                    self.marriage_pending = False
                    self.player_marriages_announced.add(suit)
                    points = 40 if suit == self.trump_suit else 20
                    self.player_round_points += points
                    self.message = f"Marriage announced in {suit}! +{points} points."
                    return

                # Otherwise, process the card as a normal move.
                valid_move = True
                if not self.first_phase and allowed_suit:
                    # When following in the second phase:
                    # - If the player holds cards of the led suit and trump cards, they may play either.
                    # - If they have only cards of the led suit, they must play one.
                    # - If they have only trump cards, they must play one.
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
                    # Trigger the shake animation for this card.
                    self.shake_card_index = i
                    self.shake_start_time = pygame.time.get_ticks()
                    return

                # Process the card normally based on whose turn it is.
                if self.current_leader == "player":
                    self.player_lead(i)
                else:
                    self.player_follow(i)
                break

    def player_lead(self, card_index):
        """
        Called when the player leads.
        After the player leads, have the computer respond as follower.
        """
        self.player_played = self.player_hand.pop(card_index)
        state = self.get_game_state()
        self.computer_played = self.opponent.play(state, self.computer_hand)
        self.trick_ready = True
        self.message = "Trick ready. Click 'End Trick' to resolve."
        self.current_leader = "player"

    def player_follow(self, card_index):
        """
        Called when the player follows.
        """
        self.player_played = self.player_hand.pop(card_index)
        self.trick_ready = True
        self.message = "Trick ready. Click 'End Trick' to resolve."

    def player_follow_by_click(self, pos):
        """
        Helper to select the card the player clicked when following.
        """
        num_cards = len(self.player_hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.B_rect.x + (self.B_rect.width - total_width) // 2
        y = self.B_rect.y + (self.B_rect.height - CARD_HEIGHT) // 2
        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i*(CARD_WIDTH+CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                self.player_follow(i)
                break

    def computer_lead(self):
        current_time = pygame.time.get_ticks()
        
        # If there is a pending marriage announcement, wait until 3 seconds have passed.
        if self.marriage_announcement is not None:
            delta = current_time - self.marriage_time
            print("DEBUG: current_time:", current_time, "marriage_time:", self.marriage_time, "delta:", delta)
            if delta < 3000:
                self.message = "Computer announced marriage. Waiting to lead..."
                return  # Wait until the marriage display period is over.
            else:
                # Once 5 seconds have passed, mark that marriage as handled:
                # Add the announced suit to the set so it won’t be re-announced.
                suit_announced = self.marriage_announcement[0][1]
                self.computer_marriages_announced.add(suit_announced)
                self.marriage_announcement = None

        # If no marriage is pending, check for a valid marriage.
        if self.marriage_announcement is None:
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
                print("DEBUG: Computer announced marriage:", marriage_found)
                return  # Delay leading until the marriage announcement is displayed.
        
        # Otherwise, proceed to lead normally.
        state = self.get_game_state()
        self.computer_played = self.opponent.play(state, self.computer_hand)
        self.current_leader = "computer"
        self.message = "Computer leads. Your turn to follow."
        self.trick_ready = False

    def resolve_trick(self):
        """
        Determine the trick winner, add points, and update the leader.
        Then call draw_cards (which now also handles the last-trick bonus).
        If the computer wins the trick, automatically have it lead.
        """
        winner = self.determine_trick_winner(self.player_played, self.computer_played)
        trick_points = CARD_VALUES[self.player_played[0]] + CARD_VALUES[self.computer_played[0]]
        # (The extra 10 points for the last trick will be handled in draw_cards.)
        if winner == "player":
            self.player_round_points += trick_points
            self.player_tricks += 1
            self.message = f"You win the trick and earn {trick_points} points!"
            self.current_leader = "player"
            # Record the won cards for display.
            self.player_won_cards.extend([self.player_played, self.computer_played])
        elif winner == "computer":
            self.computer_round_points += trick_points
            self.computer_tricks += 1
            self.message = f"Computer wins the trick and earns {trick_points} points!"
            self.current_leader = "computer"
            self.computer_won_cards.extend([self.player_played, self.computer_played])
        else:
            self.message = "Tie trick! No points awarded."

        self.player_played = None
        self.computer_played = None
        self.trick_ready = False

        if self.first_phase:
            self.draw_cards(winner)
        self.check_round_end()
        # If computer is now leader, have it lead automatically (even in second phase).
        if self.current_leader == "computer":
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
            return leader
        if follower_card[1] == trump and leader_card[1] != trump:
            return follower

        # Rule 2(a): If neither card is trump (or both are trump) and the follower did not follow suit,
        # then the leader wins.
        if follower_card[1] != lead_suit:
            return leader

        # Rule 2(b): Both cards are of the lead suit (or both are trump), so compare point values.
        if CARD_VALUES[leader_card[0]] >= CARD_VALUES[follower_card[0]]:
            return leader
        else:
            return follower

    def draw_cards(self, trick_winner):
        """
        In first phase, after a trick the winner draws first and the loser draws second.
        If, after the winner’s draw the deck becomes empty, then the loser draws the trump-announcement card
        (which counts as the last card) and the winner is awarded an extra 10 points.
        Then, the game switches to second phase.
        """
        if self.deck:
            if trick_winner == "player":
                self.player_hand.append(self.deck.pop())
                if not self.deck and self.trump_card is not None:
                    # Last card: loser draws the trump card.
                    self.computer_hand.append(self.trump_card)
                    self.trump_card = None
                    self.player_round_points += 10  # extra 10 points bonus
                else:
                    if self.deck:
                        self.computer_hand.append(self.deck.pop())
            elif trick_winner == "computer":
                self.computer_hand.append(self.deck.pop())
                if not self.deck and self.trump_card is not None:
                    self.player_hand.append(self.trump_card)
                    self.trump_card = None
                    self.computer_round_points += 10  # extra 10 points bonus
                else:
                    if self.deck:
                        self.player_hand.append(self.deck.pop())
            if not self.deck:
                self.first_phase = False
        else:
            self.first_phase = False

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
        # Only check for round end when both hands are empty.
        if len(self.player_hand) > 0 or len(self.computer_hand) > 0:
            return  # Round is not over yet.

        # --- Round has ended because both hands are empty. ---

        # First, handle the case where the game was closed.
        if self.game_closed:
            # Assume only the human can close the game.
            if self.player_round_points < 66:
                # The human closed but did not reach 66; award 1 game point to the computer.
                self.computer_game_points += 1
                self.message = "You closed the game but didn't reach 66. Computer gets 1 game point as penalty."
                # Reset the flag for the next round.
                self.game_closed = False
                # End the round.
                if self.player_game_points >= 11 or self.computer_game_points >= 11:
                    self.message += " Game Over."
                    self.end_game_callback()
                else:
                    self.reset_round()
                return
            else:
                # If closed and the human did reach 66, then clear the flag and continue with normal scoring.
                self.game_closed = False

        # Now, determine scoring based on round points.
        if self.player_round_points >= 66 or self.computer_round_points >= 66:
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
            elif loser_points < 33:
                game_points = 2
            else:
                game_points = 1
        else:
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
        else:
            self.message = "Round ended in a tie. No game points awarded."

        # Check for overall game end.
        if self.player_game_points >= 11 or self.computer_game_points >= 11:
            self.message += " Game Over."
            self.end_game_callback()
        else:
            self.reset_round()

    def reset_round(self):
        """
        Reset for a new round: rebuild the deck, re-deal cards, and reset round points and trick counts.
        """
        self.deck = [(rank, suit) for suit in self.suits for rank in self.ranks]
        random.shuffle(self.deck)
        self.player_hand = [self.deck.pop() for _ in range(3)]
        self.computer_hand = [self.deck.pop() for _ in range(3)]
        self.player_hand += [self.deck.pop() for _ in range(3)]
        self.computer_hand += [self.deck.pop() for _ in range(3)]
        self.trump_card = self.deck.pop() if self.deck else None
        self.trump_suit = self.trump_card[1] if self.trump_card else None
        self.player_round_points = 0
        self.computer_round_points = 0
        self.player_tricks = 0
        self.computer_tricks = 0
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
        self.player_won_cards = []
        self.computer_won_cards = []
        self.game_closed = False
        self.message += " New round started. Your turn to lead."

    def close_game(self):
        """
        Called when the player clicks the "Close" button.
        This stops drawing from the deck and marks that the game was closed.
        """
        self.first_phase = False
        self.game_closed = True  # Mark that the human closed the game.
        self.message = "You closed the game. Now in second phase, follow suit if possible."

    def switch_trump(self):
        # Allow the switch only if the player is the leader.
        if self.current_leader != "player":
            self.message = "You can only switch trump 9 when you are leading."
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
        else:
            self.message = "You do not have the trump 9."

    def announce_marriage(self):
        # Only allow marriage if the human is in lead and has not yet announced one this round.
        if self.current_leader != "player":
            self.message = "You can only announce marriage when you're in lead."
            return
        # Set a flag so that the next card click will be interpreted as the marriage selection.
        self.marriage_pending = True
        self.message = "Marriage pending: click a King or Queen from your hand to announce marriage."
