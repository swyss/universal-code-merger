"""
universal-code-merger v2 — CLI entry point.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.config_loader import build_config, list_profiles
from src.merger import merge


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ucm",
        description="universal-code-merger v2 — merge codebases into AI-ready files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py path/to/project\n"
            "  python main.py --profile project\n"
            "  python main.py --profile project --dry-run\n"
            "  python main.py --list-profiles\n"
        ),
    )
    parser.add_argument(
        "source", nargs="?", default=None,
        help="Source directory to merge (overrides profile source)",
    )
    parser.add_argument(
        "--profile", "-p", metavar="NAME", default=None,
        help="Profile from configs/<NAME>.json",
    )
    parser.add_argument(
        "--dry-run", "-d", action="store_true",
        help="Preview collected files without writing output",
    )
    parser.add_argument(
        "--list-profiles", action="store_true",
        help="List available profiles and exit",
    )
    return parser


def run_cli() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # List profiles
    if args.list_profiles:
        profiles = list_profiles()
        if profiles:
            print("[INFO] Available profiles:")
            for name in profiles:
                print(f"  - {name}")
        else:
            print("[INFO] No profiles found in configs/")
        sys.exit(0)

    # Resolve source path (handles backslashes, relative, UNC)
    cli_source: Optional[str] = (
        str(Path(args.source).resolve()) if args.source else None
    )

    # Build layered config
    try:
        cfg = build_config(profile=args.profile, cli_source=cli_source)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Config: {exc}")
        sys.exit(1)

    if args.dry_run:
        cfg.dry_run = True

    if not cfg.source:
        print("[ERROR] No source directory specified.")
        print("        Pass a path or set 'source' in a profile.\n")
        parser.print_help()
        sys.exit(1)

    merge(cfg)
