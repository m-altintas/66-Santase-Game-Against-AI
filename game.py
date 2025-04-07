import pygame
import sys

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, MARRIAGE_DONE_EVENT
from ui import MainMenu, PlayMenu, PauseMenu, HelpScreen, EndGameScreen
from gameplay import GamePlay
from log_config import logger

# ---------------------------
# Game Class (State Manager)
# ---------------------------
class Game:
    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        logger.info("Initializing the game.")
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("66 Santase by ma")
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = "menu"
        self.developer_mode = False
        self.main_menu = MainMenu(self.screen, play_callback=self.go_to_play_menu, help_callback=self.show_help_from_main, settings_callback=self.go_to_settings)
        logger.debug("Main menu initialized.")
        self.play_menu = None
        self.gameplay = None

    def go_to_main_menu(self):
        logger.info("Returning to main menu.")
        self.state = "menu"

    def go_to_play_menu(self):
        logger.info("Switching to play menu.")
        self.state = "play"
        # Pass the ai strategy to the callback
        self.play_menu = PlayMenu(self.screen, ai_select_callback=lambda ai: self.go_to_gameplay(ai))
        logger.debug("Play menu created.")

    def go_to_gameplay(self, ai_strategy="JustRandom"):
        logger.info("Starting gameplay with strategy: %s", ai_strategy)
        self.state = "game"
        self.gameplay = GamePlay(self.screen, end_game_callback=self.end_game, ai_strategy=ai_strategy, developer_mode=self.developer_mode)
        self.gameplay.pause_callback = self.pause_game  # Set a callback
        logger.debug("Gameplay screen created.")
        
    def go_to_settings(self):
        logger.info("Switching to settings page.")
        self.state = "settings"
        # Create a SettingsPage instance, passing the current developer mode and a toggle callback.
        from ui import SettingsPage  # Ensure SettingsPage is imported
        self.settings_page = SettingsPage(self.screen, self.developer_mode, self.toggle_developer_mode, self.go_to_main_menu)

    def toggle_developer_mode(self, mode):
        self.developer_mode = mode
        logger.info("Developer mode set to %s", mode)

    def pause_game(self):
        logger.info("Game paused.")
        self.state = "pause"
        self.pause_menu = PauseMenu(
            self.screen,
            continue_callback=self.resume_game,
            help_callback=self.show_help_from_pause,
            restart_callback=self.restart_game,
            main_menu_callback=self.go_to_main_menu
        )
        logger.debug("Pause menu created.")

    def resume_game(self):
        logger.info("Resuming game from pause.")
        self.state = "game"

    def show_help_from_main(self):
        logger.info("Showing help screen (from main menu).")
        self.state = "help"
        self.help_screen = HelpScreen(self.screen, go_back_callback=self.go_to_main_menu)

    def show_help_from_pause(self):
        logger.info("Showing help screen (from pause menu).")
        self.state = "help"
        self.help_screen = HelpScreen(self.screen, go_back_callback=self.resume_pause_menu)
        
    def resume_pause_menu(self):
        logger.info("Returning to pause menu from help screen.")
        self.state = "pause"
    
    def restart_game(self):
        logger.info("Restarting game with current opponent.")
        self.state = "game"
        self.gameplay = GamePlay(self.screen, end_game_callback=self.end_game)
        self.gameplay.pause_callback = self.pause_game
        logger.debug("Gameplay screen reinitialized after restart.")

    def end_game(self):
        logger.info("Ending game.")
        # Create an instance of EndGameScreen using the overall game points.
        self.state = "endgame"
        self.endgame_screen = EndGameScreen(
            self.screen,
            self.gameplay.player_game_points,
            self.gameplay.computer_game_points,
            self.go_to_main_menu  # A method to transition to the main menu.
        )
        logger.debug("End game screen created. Final score: Player %s - Computer %s",
                     self.gameplay.player_game_points, self.gameplay.computer_game_points)

    def run(self):
        logger.info("Game loop starting.")
        while self.running:
            self.handle_events()
            
            # Draw based on current state.
            if self.state == "game":
                self.gameplay.draw()
            elif self.state == "pause":
                self.pause_menu.draw()
            elif self.state == "menu":
                self.main_menu.draw()
            elif self.state == "settings":
                self.settings_page.draw()
            elif self.state == "help":
                self.help_screen.draw()
            elif self.state == "play":
                self.play_menu.draw()
            elif self.state == "endgame":
                self.endgame_screen.draw()
            pygame.display.flip()
            self.clock.tick(60)
        logger.info("Game loop terminated.")

    def handle_events(self):
        for event in pygame.event.get():
            #logger.debug("Game has recieved event: %s", event)
            
            if event.type == pygame.QUIT:
                logger.info("QUIT event received. Exiting game loop.")
                self.running = False

            # Handle the marriage timer event.
            if event.type == MARRIAGE_DONE_EVENT:
                # Clear the marriage announcement
                if self.gameplay.marriage_announcement is not None:
                    self.gameplay.marriage_announcement = None
                    
                self.gameplay.ongoing_animation = False

                # Stop the timer
                pygame.time.set_timer(MARRIAGE_DONE_EVENT, 0)

                # If the AI is still the leader and hasn’t yet played a card:
                if self.gameplay.current_leader == "opponent" and self.gameplay.opponent.played_card is None:
                    self.gameplay.computer_lead()
                
                continue

            # Then process events for your current state.
            if self.state == "game" and self.gameplay:
                self.gameplay.handle_event(event)
            elif self.state == "pause":
                self.pause_menu.handle_event(event)
            elif self.state == "menu":
                self.main_menu.handle_events(event)
            elif self.state == "settings":
                self.settings_page.handle_event(event)
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
