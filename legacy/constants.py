import pygame

# ---------------------------
# Constants
# ---------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MARGIN = 20

CARD_WIDTH = 100
CARD_HEIGHT = 150
CARD_SPACING = 20

# Card point values used for trick scoring
CARD_VALUES = {
    "9": 0,
    "J": 2,
    "Q": 3,
    "K": 4,
    "10": 10,
    "A": 11
}

MARRIAGE_DONE_EVENT = pygame.USEREVENT + 5
