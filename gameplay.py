import pygame
import random
import math

from constants import CARD_HEIGHT, CARD_WIDTH, CARD_SPACING, MARGIN, CARD_VALUES, NORMAL_ORDER, TRUMP_ORDER
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

            # Determine allowed suit when in second phase and player is following.
            allowed_suit = None
            if not self.first_phase:
                if self.current_leader == "computer" and self.computer_played:
                    allowed_suit = self.computer_played[1]
            has_valid = any(card[1] == allowed_suit for card in self.player_hand) if allowed_suit else False

            for i, card in enumerate(self.player_hand):
                pos_x = start_x + i * (CARD_WIDTH + CARD_SPACING)

                # If this card is set to shake (invalid click), calculate a shake offset.
                if self.shake_card_index is not None and i == self.shake_card_index:
                    elapsed = pygame.time.get_ticks() - self.shake_start_time
                    if elapsed < self.shake_duration:
                        # Use a sine function for a smooth oscillation; adjust magnitude (10) as needed.
                        offset = int(10 * math.sin((elapsed / 50.0) * math.pi))
                        pos_x += offset
                    else:
                        # Shake is done; reset the shake variables.
                        self.shake_card_index = None

                pos = (pos_x, y)
                card_img = self.card_images.get(card)

                # In second phase: if an allowed suit is required and the player holds valid card(s),
                # grey out cards that do not match the allowed suit.
                if not self.first_phase and allowed_suit and has_valid and card[1] != allowed_suit:
                    card_img = card_img.copy()  # Make a copy so the original image isn’t modified.
                    card_img.set_alpha(100)     # Lower opacity (adjust value as needed).

                self.screen.blit(card_img, pos)

        # --- Draw the Marriage Announcement, Played Cards, Deck, Buttons, etc. ---
        # (Keep your existing drawing code below here.)
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
        # (Retain your existing drawing code for these zones.)
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

        # Draw the additional buttons.
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
        msg_rect = msg_text.get_rect(center=(self.screen_width//2, self.B_rect.y - 30))
        self.screen.blit(msg_text, msg_rect)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        # Let buttons process the event first.
        self.close_button.handle_event(event)
        self.switch_button.handle_event(event)
        self.marriage_button.handle_event(event)

        pos = event.pos

        # If the "End Trick" button is clicked, process it immediately.
        if self.F_rect.collidepoint(pos):
            if self.trick_ready:
                self.resolve_trick()
            return

        # If a trick is in progress, ignore additional clicks.
        if self.trick_ready:
            return

        # Determine the allowed suit when in the second phase.
        allowed_suit = None
        if not self.first_phase:
            if self.current_leader == "computer" and self.computer_played:
                allowed_suit = self.computer_played[1]
        has_valid = any(card[1] == allowed_suit for card in self.player_hand) if allowed_suit else False

        # Calculate the area for the player's hand.
        num_cards = len(self.player_hand)
        total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
        start_x = self.B_rect.x + (self.B_rect.width - total_width) // 2
        y = self.B_rect.y + (self.B_rect.height - CARD_HEIGHT) // 2

        # Loop over each card in the player's hand to check if it was clicked.
        for i in range(num_cards):
            card_rect = pygame.Rect(start_x + i * (CARD_WIDTH + CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(pos):
                # If in second phase and the player must follow suit but clicked a card of a different suit...
                if not self.first_phase and allowed_suit and has_valid and self.player_hand[i][1] != allowed_suit:
                    self.message = f"You must follow suit ({allowed_suit})."
                    # Record the index and current time to trigger the shake animation.
                    self.shake_card_index = i
                    self.shake_start_time = pygame.time.get_ticks()
                    return  # Do not process the invalid click.
                # Otherwise, process the click normally based on turn.
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
        Determine trick winner using Santase rules.
        The first card played sets the lead suit.
        A trump card beats any non-trump.
        If both cards are trump (or both non-trump), compare using the appropriate order.
        If the follower does not follow suit while having the option, the leader wins.
        """
        lead_suit = player_card[1] if self.current_leader == "player" else computer_card[1]
        trump = self.trump_suit

        if player_card[1] == trump and computer_card[1] != trump:
            return "player"
        if computer_card[1] == trump and player_card[1] != trump:
            return "computer"
        if player_card[1] == trump and computer_card[1] == trump:
            return "player" if TRUMP_ORDER[player_card[0]] > TRUMP_ORDER[computer_card[0]] else "computer"
        if self.current_leader == "player":
            if computer_card[1] != lead_suit:
                return "player"
        else:
            if player_card[1] != lead_suit:
                return "computer"
        return "player" if NORMAL_ORDER[player_card[0]] > NORMAL_ORDER[computer_card[0]] else "computer"

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
        Check if a player has reached 66 round points.
        Award game points based on margins and reset the round if necessary.
        """
        if self.player_round_points >= 66 or self.computer_round_points >= 66:
            if self.player_round_points > self.computer_round_points:
                winner = "player"
                diff = self.computer_round_points
            else:
                winner = "computer"
                diff = self.player_round_points

            if diff < 33:
                game_points = 2
            elif diff == 0:
                game_points = 3
            else:
                game_points = 1

            if winner == "player":
                self.player_game_points += game_points
                self.message = f"You win the round! (+{game_points} game point)"
            else:
                self.computer_game_points += game_points
                self.message = f"Computer wins the round! (+{game_points} game point)"

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
        self.message += " New round started. Your turn to lead."

    def close_game(self):
        """
        Called when the player chooses to close the game.
        This disables drawing from the deck and switches to second phase.
        """
        self.first_phase = False
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
