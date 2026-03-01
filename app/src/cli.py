"""
universal-code-merger v2
CLI Entry Point

Usage:
    python main.py <path/to/project>
    python main.py --profile project
    python main.py --profile project --dry-run
    python main.py --list-profiles
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.config_loader import build_config, list_profiles
from src.merger import merge


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ucm",
        description="universal-code-merger v2 -- Merge codebases into AI-ready files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py <path/to/project>\n"
            "  python main.py --profile project\n"
            "  python main.py --profile project --dry-run\n"
            "  python main.py --list-profiles\n"
        ),
    )

    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Source directory to merge (overrides profile source)",
    )
    parser.add_argument(
        "--profile", "-p",
        metavar="NAME",
        default=None,
        help="Load a named profile from configs/<NAME>.json",
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Preview collected files without writing output",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List all available profiles and exit",
    )

    return parser


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_cli() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # --list-profiles
    # ------------------------------------------------------------------
    if args.list_profiles:
        profiles = list_profiles()
        if not profiles:
            print("[INFO] No profiles found in configs/")
        else:
            print("[INFO] Available profiles:")
            for name in profiles:
                print(f"  - {name}")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Normalise source path — resolve backslashes, relative paths, UNC
    # This is the single point where raw shell input is sanitised.
    # ------------------------------------------------------------------
    raw_source: Optional[str] = None
    if args.source:
        raw_source = str(Path(args.source).resolve())

    # ------------------------------------------------------------------
    # Build layered config
    # ------------------------------------------------------------------
    try:
        cfg = build_config(
            profile=args.profile,
            cli_source=raw_source,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Configuration error:\n  {exc}")
        sys.exit(1)

    # Apply dry-run CLI flag (highest priority)
    if args.dry_run:
        cfg.dry_run = True

    # ------------------------------------------------------------------
    # Validate source
    # ------------------------------------------------------------------
    if not cfg.source:
        print("[ERROR] No source directory specified.")
        print("        Use a positional argument or set 'source' in a profile.\n")
        parser.print_help()
        sys.exit(1)

    # ------------------------------------------------------------------
    # Run merger
    # ------------------------------------------------------------------
    merge(cfg)
