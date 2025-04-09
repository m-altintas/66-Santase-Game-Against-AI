import pygame
import datetime
import csv

from log_config import logger

# ---------------------------
# Button Class Definition
# ---------------------------
class Button:
    """
    A clickable rectangular UI element that executes a callback when clicked.
    """
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
            logger.debug("Button clicked: '%s'", self.text)
            self.callback()

# ---------------------------
# MainMenu and PlayMenu
# ---------------------------
class MainMenu:
    """
    The primary entry menu where the user can choose to Play, view Help, or go to Settings.
    """
    def __init__(self, screen, play_callback, help_callback, settings_callback):
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

        self.play_callback = play_callback
        self.help_callback = help_callback
        self.settings_callback = settings_callback

        self.buttons.append(Button(
            (button_x, start_y, button_width, button_height),
            "Play", self.play_callback, self.button_font
        ))
        self.buttons.append(Button(
            (button_x, start_y + button_height + spacing, button_width, button_height),
            "Help", self.help_callback, self.button_font
        ))
        self.buttons.append(Button(
            (button_x, start_y + 2*(button_height + spacing), button_width, button_height),
            "Settings", self.settings_callback, self.button_font
        ))

        logger.info("MainMenu initialized with header: %s", self.header_text)

    def draw(self):
        self.screen.fill((255, 255, 255))
        header_surface = self.font.render(self.header_text, True, (0, 0, 0))
        header_rect = header_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(header_surface, header_rect)
        for button in self.buttons:
            button.draw(self.screen)

    def handle_events(self, event):
        for button in self.buttons:
            button.handle_event(event)


class PlayMenu:
    """
    A submenu where the user chooses an AI strategy before starting the game.
    """
    def __init__(self, screen, ai_select_callback):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 36)
        self.button_font = pygame.font.SysFont('Arial', 24)
        self.buttons = []

        screen_width, screen_height = self.screen.get_size()
        button_width = 250
        button_height = 50
        spacing = 20
        start_y = (screen_height - (4 * button_height + 3 * spacing)) // 2

        self.buttons.append(Button(
            ((screen_width - button_width) // 2, start_y, button_width, button_height),
            "Extra: Just Random", 
            lambda: ai_select_callback("JustRandom"), 
            self.button_font
        ))
        self.buttons.append(Button(
            ((screen_width - button_width) // 2, start_y + (button_height + spacing),
             button_width, button_height),
            "Trick-Based Greedy", 
            lambda: ai_select_callback("TrickBasedGreedy"), 
            self.button_font
        ))
        self.buttons.append(Button(
            ((screen_width - button_width) // 2, start_y + 2*(button_height + spacing),
            button_width, button_height),
            "MCTS", 
            lambda: ai_select_callback("MCTS"), 
            self.button_font
        ))
        self.buttons.append(Button(
            ((screen_width - button_width) // 2, start_y + 3*(button_height + spacing),
             button_width, button_height),
            "Expectiminimax", 
            lambda: ai_select_callback("Expectiminimax"), 
            self.button_font
        ))
        
        logger.info("PlayMenu initialized with %d buttons.", len(self.buttons))

    def draw(self):
        self.screen.fill((255, 255, 255))
        header_surface = self.font.render("Play Menu", True, (0, 0, 0))
        header_rect = header_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(header_surface, header_rect)
        for button in self.buttons:
            button.draw(self.screen)

    def handle_events(self, event):
        for button in self.buttons:
            button.handle_event(event)


class EndGameScreen:
    """
    A screen displayed after the game ends, showing the outcome and enabling
    saving statistics or returning to the main menu.
    """
    def __init__(self, screen, player_game_points, computer_game_points, main_menu_callback):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.player_game_points = player_game_points
        self.computer_game_points = computer_game_points
        self.main_menu_callback = main_menu_callback

        if self.player_game_points >= 11:
            self.outcome_text = "You Win!"
        else:
            self.outcome_text = "You Lose!"

        self.font_large = pygame.font.SysFont('Arial', 60)
        self.font_medium = pygame.font.SysFont('Arial', 30)
        self.font_small = pygame.font.SysFont('Arial', 20)

        self.outcome_rect = pygame.Rect(0, 50, self.screen_width, 80)
        self.stats_rect = pygame.Rect(0, 150, self.screen_width, 50)
        self.save_button_rect = pygame.Rect(self.screen_width / 2 - 150, self.screen_height - 150, 130, 50)
        self.main_menu_button_rect = pygame.Rect(self.screen_width / 2 + 20, self.screen_height - 150, 130, 50)

        self.save_button = Button(self.save_button_rect, "Save Statistics", self.save_statistics, self.font_small)
        self.main_menu_button = Button(self.main_menu_button_rect, "Main Menu", self.main_menu_callback, self.font_small)

        self.feedback_message = ""
        logger.info("EndGameScreen initialized with outcome: %s (Player: %d, Computer: %d)",
                    self.outcome_text, self.player_game_points, self.computer_game_points)

    def draw(self):
        self.screen.fill((255, 255, 255))

        outcome_color = (0, 128, 0) if "Win" in self.outcome_text else (255, 0, 0)
        outcome_surface = self.font_large.render(self.outcome_text, True, outcome_color)
        outcome_rect = outcome_surface.get_rect(center=self.outcome_rect.center)
        self.screen.blit(outcome_surface, outcome_rect)

        stats_text = f"Game Points: You {self.player_game_points} - Computer {self.computer_game_points}"
        stats_surface = self.font_medium.render(stats_text, True, (0, 0, 0))
        stats_rect = stats_surface.get_rect(center=self.stats_rect.center)
        self.screen.blit(stats_surface, stats_rect)

        self.save_button.draw(self.screen)
        self.main_menu_button.draw(self.screen)

        if self.feedback_message:
            feedback_surface = self.font_small.render(self.feedback_message, True, (0, 0, 0))
            feedback_rect = feedback_surface.get_rect(center=(self.screen_width / 2, self.screen_height - 50))
            self.screen.blit(feedback_surface, feedback_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.save_button.handle_event(event)
            self.main_menu_button.handle_event(event)

    def save_statistics(self):
        filename = f"statistics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, mode="w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Player Game Points", "Computer Game Points"])
                writer.writerow([self.player_game_points, self.computer_game_points])
            self.feedback_message = f"Statistics saved to {filename}"
            logger.debug(self.feedback_message)
        except Exception as e:
            self.feedback_message = f"Error saving statistics: {e}"
            logger.debug(self.feedback_message)


class PauseMenu:
    """
    The menu displayed when the game is paused. Allows continuing,
    restarting, viewing help, or returning to the main menu.
    """
    def __init__(self, screen, continue_callback, help_callback, restart_callback, main_menu_callback):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 36)
        self.button_font = pygame.font.SysFont('Arial', 24)
        self.continue_callback = continue_callback
        self.help_callback = help_callback
        self.restart_callback = restart_callback
        self.main_menu_callback = main_menu_callback
        self.buttons = []

        screen_width, screen_height = self.screen.get_size()
        button_width = 250
        button_height = 50
        spacing = 20
        start_y = (screen_height - (4 * button_height + 3 * spacing)) // 2
        start_x = (screen_width - button_width) // 2

        self.buttons.append(Button(
            (start_x, start_y, button_width, button_height),
            "Continue", self.continue_callback, self.button_font
        ))
        self.buttons.append(Button(
            (start_x, start_y + button_height + spacing, button_width, button_height),
            "Help", self.help_callback, self.button_font
        ))
        self.buttons.append(Button(
            (start_x, start_y + 2*(button_height + spacing), button_width, button_height),
            "Restart Game", self.restart_callback, self.button_font
        ))
        self.buttons.append(Button(
            (start_x, start_y + 3*(button_height + spacing), button_width, button_height),
            "Main Menu", self.main_menu_callback, self.button_font
        ))

        logger.info("PauseMenu initialized with %d buttons.", len(self.buttons))

    def draw(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        title_surface = self.font.render("Paused", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        for button in self.buttons:
            button.draw(self.screen)

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)


class HelpScreen:
    """
    Displays a scrollable help text with the rules of Santase,
    plus a button to return to the previous screen.
    """
    def __init__(self, screen, go_back_callback):
        self.screen = screen
        self.go_back_callback = go_back_callback

        self.font_title = pygame.font.SysFont("Arial", 48)
        self.font_text = pygame.font.SysFont("Arial", 24)
        self.font_button = pygame.font.SysFont("Arial", 20)

        self.help_text = (
            "Santase (66) - Rules and How to Play\n\n"
            "Overview:\n"
            "  This is a two-player game played against a computer opponent. "
            "The game uses a 24-card deck (cards: 9, J, Q, K, 10, A in four suits).\n\n"
            "Game Phases:\n"
            "  1. First Phase: Cards are dealt in rounds and after each trick, "
            "the winner draws a card first and the loser next.\nThe trump card is revealed "
            "and its suit becomes the trump suit. In this phase, players draw cards.\n"
            "  2. Second Phase: Once the deck is exhausted or the player 'closes' the game, "
            "no further cards are drawn.\nThe follower must either follow suit if possible or play "
            "a trump card if available. If neither is available, any card may be played\n(though it will likely lose the trick).\n\n"
            "Trick Resolution & Scoring:\n"
            "  - Card point values: 9=0, J=2, Q=3, K=4, 10=10, A=11.\n"
            "  - When both cards follow suit (or both are trump), the card with the higher point value wins. "
            "If one card is trump and the other isn’t,\nthe trump wins. If the follower fails to follow suit when "
            "able, the leader wins automatically.\n\n"
            "Special Moves:\n"
            "  - Marriage Announcement: If you hold both a King and Queen of the same suit, you may announce a marriage. "
            "If the suit is trump,\nyou gain 40 points; otherwise, 20 points. Each suit can be used for marriage only once per round.\n"
            "  - Trump 9 Switch: When leading, if you have the trump 9, you may swap it with the current trump card.\n\n"
            "Round & Game Scoring:\n"
            "  - A round ends when both players’ hands are empty. Then, game points are awarded based on the margin:\n"
            "      • If a player has 66+ points and the opponent has between 33 and 66 (or both have 66+), the winner gets 1 game point.\n"
            "      • If one player has 66+ and the opponent has less than 33, the winner gets 2 game points.\n"
            "      • If one player has 66+ and the opponent hasn’t won any tricks, the winner gets 3 game points.\n"
            "      • If a player closes the game expecting to reach 66 but fails, the opponent is awarded 1 game point as a penalty.\n"
            "      • If neither player reaches 66, the player with the higher points gets 1 game point.\n"
            "  - The overall game ends when one player reaches 11 game points.\n\n"
            "User Interface:\n"
            "  - Main Menu: Access options such as Play, Help, and Settings.\n"
            "  - Play Menu: Start a game against a computer opponent.\n"
            "  - Gameplay: The computer’s hand is shown at the top (face-down), your hand at the bottom (face-up), "
            "and the played cards in the center.\nSpecial buttons let you announce marriage, switch trump, or close the game.\n"
            "  - Pause Menu: Accessible via the top-right of the gameplay screen; it allows you to continue, get help, restart the game,\nor return to the main menu.\n\n"
            "Controls:\n"
            "  - Click on cards to play them, following the rules about following suit and playing trump cards when required.\n"
            "  - Use on-screen buttons for special moves and menu options.\n\n"
            "Enjoy the game and good luck!"
        )

        self.lines = self.help_text.split("\n")
        self.line_height = self.font_text.get_linesize()
        self.content_height = len(self.lines) * self.line_height

        self.view_rect = pygame.Rect(40, 120, self.screen.get_width() - 80, self.screen.get_height() - 160)
        self.scroll_offset = 0
        self.max_scroll = max(0, self.content_height - self.view_rect.height)

        self.back_button = Button((20, 20, 120, 40), "Go Back", self.go_back_callback, self.font_button)
        logger.info("HelpScreen initialized with %d lines of text.", len(self.lines))

    def draw(self):
        self.screen.fill((30, 30, 30))

        title_surface = self.font_title.render("Help & Rules", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 60))
        self.screen.blit(title_surface, title_rect)

        y = self.view_rect.y - self.scroll_offset
        for line in self.lines:
            if y + self.line_height > self.view_rect.y and y < self.view_rect.y + self.view_rect.height:
                line_surface = self.font_text.render(line, True, (200, 200, 200))
                self.screen.blit(line_surface, (self.view_rect.x, y))
            y += self.line_height

        pygame.draw.rect(self.screen, (100, 100, 100), self.view_rect, 2)
        self.back_button.draw(self.screen)

    def handle_event(self, event):
        self.back_button.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - self.line_height)
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.line_height)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Mouse wheel up
                self.scroll_offset = max(0, self.scroll_offset - self.line_height)
            elif event.button == 5:  # Mouse wheel down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.line_height)


class SettingsPage:
    """
    A page to toggle developer mode and return to the main menu.
    """
    def __init__(self, screen, developer_mode, toggle_callback, back_callback):
        self.screen = screen
        self.developer_mode = developer_mode
        self.toggle_callback = toggle_callback
        self.back_callback = back_callback

        self.font = pygame.font.SysFont("Arial", 36)
        self.button_font = pygame.font.SysFont("Arial", 24)
        screen_width, screen_height = self.screen.get_size()
        button_width = 250
        button_height = 50
        spacing = 20

        self.toggle_button = Button(
            ((screen_width - button_width) // 2, (screen_height // 2) - button_height - spacing,
             button_width, button_height),
            f"Developer Mode: {'ON' if self.developer_mode else 'OFF'}",
            self.toggle,
            self.button_font
        )
        self.back_button = Button(
            ((screen_width - button_width) // 2, (screen_height // 2) + spacing,
             button_width, button_height),
            "Back",
            self.back_callback,
            self.button_font
        )

    def toggle(self):
        self.developer_mode = not self.developer_mode
        self.toggle_button.text = f"Developer Mode: {'ON' if self.developer_mode else 'OFF'}"
        self.toggle_callback(self.developer_mode)

    def draw(self):
        self.screen.fill((255, 255, 255))
        title_surface = self.font.render("Settings", True, (0, 0, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        self.toggle_button.draw(self.screen)
        self.back_button.draw(self.screen)

    def handle_event(self, event):
        self.toggle_button.handle_event(event)
        self.back_button.handle_event(event)
