import pygame
import sys
import random

# ---------------------------
# Global Constants
# ---------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MARGIN = 20

CARD_WIDTH = 100
CARD_HEIGHT = 150
CARD_SPACING = 20

# Card point values for trick scoring.
CARD_VALUES = {
    "9": 0,
    "J": 2,
    "Q": 3,
    "K": 4,
    "10": 10,
    "A": 11
}

# Trick ranking orders:
NORMAL_ORDER = {"A": 6, "10": 5, "K": 4, "Q": 3, "J": 2, "9": 1}
TRUMP_ORDER = {"9": 6, "A": 5, "10": 4, "K": 3, "Q": 2, "J": 1}

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

# ---------------------------
# Button Class Definition
# ---------------------------
class Button:
    def __init__(self, rect, text, callback, font,
                 bg_color=(200, 200, 200), text_color=(0, 0, 0)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.callback()

# ---------------------------
# MainMenu and PlayMenu Definitions
# ---------------------------
class MainMenu:
    def __init__(self, screen, play_callback):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 36)
        self.button_font = pygame.font.SysFont('Arial', 24)
        self.header_text = "66 Santase by ma"
        self.buttons = []
        screen_width, screen_height = self.screen.get_size()
        button_width = 200
        button_height = 50
        button_x = (screen_width - button_width) // 2
        start_y = (screen_height // 2) - button_height - 20
        spacing = 20

        self.buttons.append(Button(
            (button_x, start_y, button_width, button_height),
            "Play", play_callback, self.button_font))
        self.buttons.append(Button(
            (button_x, start_y + button_height + spacing, button_width, button_height),
            "Help", lambda: print("Help button clicked"), self.button_font))
        self.buttons.append(Button(
            (button_x, start_y + 2*(button_height + spacing), button_width, button_height),
            "Settings", lambda: print("Settings button clicked"), self.button_font))

    def draw(self):
        self.screen.fill((255, 255, 255))
        header_surface = self.font.render(self.header_text, True, (0, 0, 0))
        header_rect = header_surface.get_rect(center=(self.screen.get_width()//2, 100))
        self.screen.blit(header_surface, header_rect)
        for button in self.buttons:
            button.draw(self.screen)

    def handle_events(self, event):
        for button in self.buttons:
            button.handle_event(event)

class PlayMenu:
    def __init__(self, screen, just_play_callback):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 36)
        self.button_font = pygame.font.SysFont('Arial', 24)
        self.buttons = []
        screen_width, screen_height = self.screen.get_size()
        button_width = 200
        button_height = 50
        button_x = (screen_width - button_width) // 2
        start_y = screen_height // 2 - button_height // 2

        self.buttons.append(Button(
            (button_x, start_y, button_width, button_height),
            "Just Play Random", just_play_callback, self.button_font))

    def draw(self):
        self.screen.fill((255, 255, 255))
        header_surface = self.font.render("Play Menu", True, (0, 0, 0))
        header_rect = header_surface.get_rect(center=(self.screen.get_width()//2, 100))
        self.screen.blit(header_surface, header_rect)
        for button in self.buttons:
            button.draw(self.screen)

    def handle_events(self, event):
        for button in self.buttons:
            button.handle_event(event)

# ---------------------------
# GamePlay Class Definition (Revised Rules & Draw Modification)
# ---------------------------
class GamePlay:
    def __init__(self, screen):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()

        # Load background image (or fallback)
        try:
            self.background = pygame.image.load("backgrounds/game_background.png")
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

        # Zone J: Remaining deck count.
        self.J_rect = pygame.Rect(MARGIN, self.B_rect.y - 70, 80, 40)
        # Zone K: Button to “close” the game (end first phase).
        self.K_rect = pygame.Rect(self.J_rect.right + 10, self.B_rect.y - 70, 80, 40)
        # Zone G: Points display.
        self.G_rect = pygame.Rect(self.screen_width - MARGIN - 100, self.B_rect.y - 70, 100, 40)

        # Close button for Zone K.
        self.close_button = Button(self.K_rect, "Close", self.close_game, pygame.font.SysFont('Arial', 20))

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
        self.screen.blit(self.background, (0, 0))
        font_small = pygame.font.SysFont('Arial', 20)

        # Draw opponent’s hand (Zone A) as card backs.
        if self.computer_hand:
            num_cards = len(self.computer_hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.A_rect.x + (self.A_rect.width - total_width) // 2
            y = self.A_rect.y + (self.A_rect.height - CARD_HEIGHT) // 2
            for i in range(num_cards):
                pos = (start_x + i * (CARD_WIDTH + CARD_SPACING), y)
                self.screen.blit(self.card_back, pos)

        # Draw player’s hand (Zone B) face-up.
        if self.player_hand:
            num_cards = len(self.player_hand)
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.B_rect.x + (self.B_rect.width - total_width) // 2
            y = self.B_rect.y + (self.B_rect.height - CARD_HEIGHT) // 2
            for i, card in enumerate(self.player_hand):
                pos = (start_x + i * (CARD_WIDTH + CARD_SPACING), y)
                self.screen.blit(self.card_images.get(card), pos)

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

        # Draw "End Trick" button (Zone F).
        pygame.draw.rect(self.screen, (180, 180, 250), self.F_rect)
        et_text = font_small.render("End Trick", True, (0, 0, 0))
        et_rect = et_text.get_rect(center=self.F_rect.center)
        self.screen.blit(et_text, et_rect)

        # Draw deck (Zone I).
        if self.deck:
            deck_img = pygame.transform.scale(self.card_back, (self.I_rect.width, self.I_rect.height))
            self.screen.blit(deck_img, (self.I_rect.x, self.I_rect.y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.I_rect)
        # Draw trump card (Zone H).
        if self.trump_card:
            trump_img = pygame.transform.scale(self.card_images.get(self.trump_card), (self.H_rect.width, self.H_rect.height))
            self.screen.blit(trump_img, (self.H_rect.x, self.H_rect.y))
        else:
            pygame.draw.rect(self.screen, (50, 50, 50), self.H_rect)

        # Draw remaining deck count (Zone J).
        pygame.draw.rect(self.screen, (250, 250, 200), self.J_rect)
        count_text = font_small.render(str(len(self.deck)), True, (0, 0, 0))
        count_rect = count_text.get_rect(center=self.J_rect.center)
        self.screen.blit(count_text, count_rect)

        # Draw Close button (Zone K) only in first phase.
        if self.first_phase:
            self.close_button.draw(self.screen)
        else:
            sp_text = font_small.render("2nd Phase", True, (0, 0, 0))
            sp_rect = sp_text.get_rect(center=self.K_rect.center)
            pygame.draw.rect(self.screen, (200, 250, 200), self.K_rect)
            self.screen.blit(sp_text, sp_rect)

        # Draw points (Zone G).
        pygame.draw.rect(self.screen, (250, 200, 200), self.G_rect)
        points_text = font_small.render(f"Pts: {self.player_round_points}-{self.computer_round_points}", True, (0, 0, 0))
        points_rect = points_text.get_rect(center=self.G_rect.center)
        self.screen.blit(points_text, points_rect)

        # Draw feedback message.
        msg_text = font_small.render(self.message, True, (255, 255, 255))
        msg_rect = msg_text.get_rect(center=(self.screen_width//2, self.B_rect.y - 30))
        self.screen.blit(msg_text, msg_rect)

    def handle_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        pos = event.pos

        # If Close button clicked (first phase).
        if self.first_phase and self.K_rect.collidepoint(pos):
            self.close_game()
            return

        # If "End Trick" button clicked.
        if self.F_rect.collidepoint(pos):
            if self.trick_ready:
                self.resolve_trick()
            return

        # Determine turn based on leader.
        if self.current_leader == "player":
            # Player leads: check clicks in Zone B.
            num_cards = len(self.player_hand)
            if num_cards == 0:
                return
            total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
            start_x = self.B_rect.x + (self.B_rect.width - total_width) // 2
            y = self.B_rect.y + (self.B_rect.height - CARD_HEIGHT) // 2
            for i in range(num_cards):
                card_rect = pygame.Rect(start_x + i*(CARD_WIDTH+CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
                if card_rect.collidepoint(pos):
                    self.player_lead(i)
                    break
        else:
            # Computer leads; player is following.
            # In second phase enforce follow suit if possible.
            allowed_suit = self.computer_played[1] if self.computer_played else None
            if not self.first_phase and allowed_suit is not None:
                if any(card[1] == allowed_suit for card in self.player_hand):
                    valid = False
                    num_cards = len(self.player_hand)
                    total_width = num_cards * CARD_WIDTH + (num_cards - 1) * CARD_SPACING
                    start_x = self.B_rect.x + (self.B_rect.width - total_width) // 2
                    y = self.B_rect.y + (self.B_rect.height - CARD_HEIGHT) // 2
                    for i, card in enumerate(self.player_hand):
                        card_rect = pygame.Rect(start_x + i*(CARD_WIDTH+CARD_SPACING), y, CARD_WIDTH, CARD_HEIGHT)
                        if card_rect.collidepoint(pos) and card[1] == allowed_suit:
                            valid = True
                            self.player_follow(i)
                            break
                    if not valid:
                        self.message = f"You must follow suit ({allowed_suit})."
                else:
                    self.player_follow_by_click(pos)
            else:
                self.player_follow_by_click(pos)

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
        """
        If computer is leader, automatically choose and play a lead card.
        """
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
        elif winner == "computer":
            self.computer_round_points += trick_points
            self.computer_tricks += 1
            self.message = f"Computer wins the trick and earns {trick_points} points!"
            self.current_leader = "computer"
        else:
            self.message = "Tie trick! No points awarded."

        self.player_played = None
        self.computer_played = None
        self.trick_ready = False

        if self.first_phase:
            self.draw_cards(winner)
        self.check_round_end()
        if self.current_leader == "computer" and self.first_phase:
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
        self.message += " New round started. Your turn to lead."

    def close_game(self):
        """
        Called when the player chooses to close the game.
        This disables drawing from the deck and switches to second phase.
        """
        self.first_phase = False
        self.message = "You closed the game. Now in second phase, follow suit if possible."

# ---------------------------
# Game Class (State Manager)
# ---------------------------
class Game:
    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("66 Santase by ma")
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = "menu"
        self.main_menu = MainMenu(self.screen, play_callback=self.go_to_play_menu)
        self.play_menu = None
        self.gameplay = None

    def go_to_play_menu(self):
        self.state = "play"
        self.play_menu = PlayMenu(self.screen, just_play_callback=self.go_to_gameplay)

    def go_to_gameplay(self):
        self.state = "game"
        self.gameplay = GamePlay(self.screen)

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.state == "menu":
                self.main_menu.handle_events(event)
            elif self.state == "play" and self.play_menu:
                self.play_menu.handle_events(event)
            elif self.state == "game" and self.gameplay:
                self.gameplay.handle_event(event)

    def draw(self):
        if self.state == "menu":
            self.main_menu.draw()
        elif self.state == "play" and self.play_menu:
            self.play_menu.draw()
        elif self.state == "game" and self.gameplay:
            self.gameplay.draw()

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
