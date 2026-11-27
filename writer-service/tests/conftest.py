"""Додає папку тестів у sys.path, щоб тести могли імпортувати writer_fakes.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
