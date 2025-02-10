# ---------------------------
# Constants
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