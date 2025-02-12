import logging
import os
import datetime

# Define a folder to store log files.
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create a log filename with current date and time.
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILENAME = os.path.join(LOG_DIR, f"last-game-played-{current_time}.txt")

# Create and configure the logger.
logger = logging.getLogger("SantaseLogger")
logger.setLevel(logging.DEBUG)

# Define a formatter with timestamp, log level, and message.
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# File handler: logs all DEBUG and above messages.
file_handler = logging.FileHandler(LOG_FILENAME)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler: logs INFO and above messages.
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# (Optional) Prevent propagation to avoid duplicate messages.
logger.propagate = False
