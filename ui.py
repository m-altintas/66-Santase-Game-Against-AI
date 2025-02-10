import pygame
import datetime
import csv

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

class EndGameScreen:
    def __init__(self, screen, player_game_points, computer_game_points, main_menu_callback):
        self.screen = screen
        self.screen_width, self.screen_height = self.screen.get_size()
        self.player_game_points = player_game_points
        self.computer_game_points = computer_game_points
        self.main_menu_callback = main_menu_callback

        # Determine outcome: if player_game_points is higher (or if player reached 11 first), the player wins.
        if self.player_game_points >= 11:
            self.outcome_text = "You Win!"
        else:
            self.outcome_text = "You Lose!"

        # Fonts
        self.font_large = pygame.font.SysFont('Arial', 60)
        self.font_medium = pygame.font.SysFont('Arial', 30)
        self.font_small = pygame.font.SysFont('Arial', 20)

        # Define Zones (using simple rectangles)
        # Outcome text zone at the top:
        self.outcome_rect = pygame.Rect(0, 50, self.screen_width, 80)
        # Statistics section (for now, just overall game points) below outcome text:
        self.stats_rect = pygame.Rect(0, 150, self.screen_width, 50)
        # Overall Game Points can be shown in stats; you can later expand this.
        # Save Statistics button zone:
        self.save_button_rect = pygame.Rect(self.screen_width/2 - 150, self.screen_height - 150, 130, 50)
        # Main Menu button zone:
        self.main_menu_button_rect = pygame.Rect(self.screen_width/2 + 20, self.screen_height - 150, 130, 50)

        # Create Button objects using your existing Button class:
        self.save_button = Button(self.save_button_rect, "Save Statistics", self.save_statistics, self.font_small)
        self.main_menu_button = Button(self.main_menu_button_rect, "Main Menu", self.main_menu_callback, self.font_small)

        # Optional: A message to display feedback (e.g. for saving errors)
        self.feedback_message = ""

    def draw(self):
        # Clear the screen (you can choose a background color, here white)
        self.screen.fill((255, 255, 255))
        
        # Draw the outcome text
        outcome_color = (0, 128, 0) if "Win" in self.outcome_text else (255, 0, 0)
        outcome_surface = self.font_large.render(self.outcome_text, True, outcome_color)
        outcome_rect = outcome_surface.get_rect(center=self.outcome_rect.center)
        self.screen.blit(outcome_surface, outcome_rect)
        
        # Draw the statistics text (for now overall game points)
        stats_text = f"Game Points: You {self.player_game_points} - Computer {self.computer_game_points}"
        stats_surface = self.font_medium.render(stats_text, True, (0, 0, 0))
        stats_rect = stats_surface.get_rect(center=self.stats_rect.center)
        self.screen.blit(stats_surface, stats_rect)
        
        # Draw the Save Statistics button
        self.save_button.draw(self.screen)
        # Draw the Main Menu button
        self.main_menu_button.draw(self.screen)
        
        # Draw any feedback message (small font) near the bottom
        if self.feedback_message:
            feedback_surface = self.font_small.render(self.feedback_message, True, (0, 0, 0))
            feedback_rect = feedback_surface.get_rect(center=(self.screen_width/2, self.screen_height - 50))
            self.screen.blit(feedback_surface, feedback_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.save_button.handle_event(event)
            self.main_menu_button.handle_event(event)
            
    def save_statistics(self):
        # Generate a filename with the current timestamp.
        filename = f"statistics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, mode="w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Player Game Points", "Computer Game Points"])
                writer.writerow([self.player_game_points, self.computer_game_points])
            self.feedback_message = f"Statistics saved to {filename}"
            print(self.feedback_message)
        except Exception as e:
            self.feedback_message = f"Error saving statistics: {e}"
            print(self.feedback_message)
