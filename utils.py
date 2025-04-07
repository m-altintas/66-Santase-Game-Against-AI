import sys
import os

def resource_path(relative_path):
    """
    Get absolute path to a resource, works for both development and PyInstaller.
    When bundled, PyInstaller stores data files in a temporary folder referenced by sys._MEIPASS.
    """
    try:
        # If running under PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        # Otherwise, use the current directory
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
