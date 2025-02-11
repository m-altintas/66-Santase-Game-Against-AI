import pygame
import sys

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, MARRIAGE_DONE_EVENT
from ui import MainMenu, PlayMenu, PauseMenu, HelpScreen, EndGameScreen
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
        self.main_menu = MainMenu(self.screen, play_callback=self.go_to_play_menu, help_callback=self.show_help_from_main)
        self.play_menu = None
        self.gameplay = None

    def go_to_main_menu(self):
        self.state = "menu"

    def go_to_play_menu(self):
        self.state = "play"
        self.play_menu = PlayMenu(self.screen, just_play_callback=self.go_to_gameplay)

    def go_to_gameplay(self):
        self.state = "game"
        self.gameplay = GamePlay(self.screen, end_game_callback=self.end_game)
        self.gameplay.pause_callback = self.pause_game  # Set a callback

    def pause_game(self):
        self.state = "pause"
        # Create a PauseMenu instance with appropriate callbacks.
        self.pause_menu = PauseMenu(
            self.screen,
            continue_callback=self.resume_game,
            help_callback=self.show_help_from_pause,
            restart_callback=self.restart_game,
            main_menu_callback=self.go_to_main_menu
        )

    def resume_game(self):
        self.state = "game"

    def show_help_from_main(self):
        self.state = "help"
        self.help_screen = HelpScreen(self.screen, go_back_callback=self.go_to_main_menu)

    def show_help_from_pause(self):
        self.state = "help"
        self.help_screen = HelpScreen(self.screen, go_back_callback=self.resume_pause_menu)
        
    def resume_pause_menu(self):
        self.state = "pause"
    
    def restart_game(self):
        # For a restart, you can simply reinitialize the gameplay screen.
        self.state = "game"
        self.gameplay = GamePlay(self.screen, end_game_callback=self.end_game)
        # (Make sure to also reassign pause_callback)
        self.gameplay.pause_callback = self.pause_game

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
            if self.state == "game":
                self.gameplay.draw()
            elif self.state == "pause":
                self.pause_menu.draw()
            elif self.state == "menu":
                self.main_menu.draw()
            elif self.state == "help":
                self.help_screen.draw()
            elif self.state == "play":
                self.play_menu.draw()
            elif self.state == "endgame":
                self.endgame_screen.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Handle the marriage timer event.
            if event.type == MARRIAGE_DONE_EVENT:
                # Clear the marriage announcement.
                if self.gameplay.marriage_announcement is not None:
                    self.gameplay.marriage_announcement = None
                # Cancel the timer.
                pygame.time.set_timer(MARRIAGE_DONE_EVENT, 0)
                # Mark that the computer has already processed its marriage this trick.
                self.gameplay.computer_marriage_processed = True
                # Force the computer to resume its turn if it is still the leader.
                if self.gameplay.current_leader == "computer" and self.gameplay.computer_played is None:
                    self.gameplay.computer_lead()
                continue

            # Then process events for your current state.
            if self.state == "game" and self.gameplay:
                self.gameplay.handle_event(event)
            elif self.state == "pause":
                self.pause_menu.handle_event(event)
            elif self.state == "menu":
                self.main_menu.handle_events(event)
            elif self.state == "help":
                self.help_screen.handle_event(event)
            elif self.state == "play" and self.play_menu:
                self.play_menu.handle_events(event)
            elif self.state == "endgame":
                self.endgame_screen.handle_event(event)

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
