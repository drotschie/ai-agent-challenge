"""Pytest configuration and test path setup.

Inserts the backend root directory into sys.path so test discovery and imports
work seamlessly from the workspace root without requiring cd or virtualenv activation.
"""

from pathlib import Path
import sys

# Insert the backend root directory into sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
