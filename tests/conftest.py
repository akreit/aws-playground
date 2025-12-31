"""Pytest configuration."""
import sys
from pathlib import Path

# Add src/lambdas to the path so we can import the modules
src_path = Path(__file__).parent.parent / "src" / "lambdas"
sys.path.insert(0, str(src_path))
