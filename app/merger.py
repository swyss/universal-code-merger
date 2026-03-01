"""
universal-code-merger
Merges all relevant source files recursively into one compact text file.
Usage: python merger.py <source_folder> [output_file]
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_EXT: frozenset[str] = frozenset({
    '.py', '.env', '.json', '.ts', '.js', '.toml',
    '.config', '.txt', '.md', '.yml', '.yaml',
    '.xml', '.html', '.css', '.vue',
})

IGNORE_DIRS: frozenset[str] = frozenset({
    'node_modules', '__pycache__', '.git', '.idea',
    '.venv', 'venv', 'dist', 'build', '.env.local', 'root',

})

SEP = "\n---\n"

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

def collect_files_content(source_folder: str, output_file: str = "merged.txt") -> None:
    """
    Recursively collects all supported source files and writes
    them into a single compact output file.
    """
    source_path = Path(source_folder).resolve()

    if not source_path.is_dir():
        print(f"✗ Not a directory: {source_path}")
        sys.exit(1)

    file_count = 0
    errors = 0

    try:
        with open(output_file, 'w', encoding='utf-8') as out:
            out.write(f"src:{source_path} ts:{datetime.now():%Y-%m-%d %H:%M:%S}{SEP}")

            for root, dirs, files in os.walk(source_path):
                dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)

                for file in sorted(files):
                    file_path = Path(root) / file

                    if file_path.suffix.lower() not in SUPPORTED_EXT:
                        continue

                    rel_path = file_path.relative_to(source_path)

                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        out.write(f"# {rel_path}\n")
                        out.write(content)
                        if content and not content.endswith('\n'):
                            out.write('\n')
                        out.write(SEP)
                        file_count += 1
                        print(f"  ✓ {rel_path}")

                    except Exception as exc:
                        out.write(f"# {rel_path} [ERR: {exc}]{SEP}")
                        print(f"  ✗ {rel_path}: {exc}")
                        errors += 1

        out_abs = Path(output_file).resolve()
        print(f"\n✓ {file_count} file(s) → {out_abs}")
        if errors:
            print(f"⚠  {errors} error(s) occurred.")

    except Exception as exc:
        print(f"✗ Critical error: {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python merger.py <source_folder> [output_file]")
        print("Example: python merger.py ./src merged.txt")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "merged.txt"
    collect_files_content(source, output)


if __name__ == "__main__":
    main()
