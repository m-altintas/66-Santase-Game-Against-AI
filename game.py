import pygame
import sys

from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from ui import MainMenu, PlayMenu, EndGameScreen
from gameplay import GamePlay

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
        self.gameplay = GamePlay(self.screen, end_game_callback=self.end_game)

    def end_game(self):
        # Create an instance of EndGameScreen using the overall game points.
        self.state = "endgame"
        self.endgame_screen = EndGameScreen(
            self.screen,
            self.gameplay.player_game_points,
            self.gameplay.computer_game_points,
            self.go_to_main_menu  # A method to transition to the main menu.
        )

    def run(self):
        while self.running:
            self.handle_events()
            
            # Check if we are in the game state.
            if self.state == "game":
                # If it's the computer's turn (leader) and it hasn't played yet, trigger computer_lead().
                if (self.gameplay.current_leader == "computer" and 
                    not self.gameplay.trick_ready and 
                    self.gameplay.computer_played is None):
                    self.gameplay.computer_lead()
                # Draw the GamePlay screen.
                self.gameplay.draw()
            elif self.state == "endgame":
                # If the game is over, draw the EndGameScreen.
                self.endgame_screen.draw()
            elif self.state == "menu":
                self.main_menu.draw()
            elif self.state == "play":
                self.play_menu.draw()
            
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.state == "endgame":
                self.endgame_screen.handle_event(event)
            elif self.state == "menu":
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
