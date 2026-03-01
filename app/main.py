"""
universal-code-merger v2
Application entry point.

Run from the app/ directory:
    python main.py <path/to/project>
    python main.py --profile project
    python main.py --profile project --dry-run
    python main.py --list-profiles
"""

import sys
from pathlib import Path

# Ensure app/ is on sys.path so src.* imports resolve correctly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.cli import run_cli

if __name__ == "__main__":
    run_cli()
