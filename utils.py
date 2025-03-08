import sys
import os

def resource_path(relative_path):
    """
    Get absolute path to resource, works for development and PyInstaller.
    When bundled, PyInstaller stores the data in a temporary folder referenced by sys._MEIPASS.
    """
    try:
        # If PyInstaller created a temporary folder, use that.
        base_path = sys._MEIPASS
    except Exception:
        # Otherwise, use the current working directory.
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
