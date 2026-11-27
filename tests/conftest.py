import sys
from pathlib import Path

from hypothesis import settings

sys.path.insert(0, str(Path(__file__).parent))

settings.register_profile("ci", max_examples=300, deadline=None)
settings.register_profile("thorough", max_examples=10_000, deadline=None)
settings.load_profile("ci")
