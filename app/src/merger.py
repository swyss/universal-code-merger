"""
universal-code-merger v2 — Core merge engine.
"""

import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.filters import FilterEngine
from src.logger import log_run

if TYPE_CHECKING:
    from src.config_loader import MergerConfig


# ---------------------------------------------------------------------------
# ASCII directory tree
# ---------------------------------------------------------------------------

def _build_tree(root: Path, collected: list[Path]) -> str:
    """
    Build a compact ASCII tree of all collected files, relative to root.

    Example output:
        app/
        ├── main.py
        └── src/
            ├── cli.py
            ├── config_loader.py
            ├── filters.py
            ├── logger.py
            └── merger.py
        configs/
        └── project.json
    """
    # Group files by their parent directory parts
    # dir_parts -> set of filenames
    tree: dict[tuple, list[str]] = defaultdict(list)
    for fp in collected:
        rel   = fp.relative_to(root)
        parts = rel.parts
        tree[parts[:-1]].append(parts[-1])

    # Collect all unique directory paths (including intermediate)
    all_dirs: set[tuple] = set()
    for dir_parts in tree:
        for i in range(len(dir_parts) + 1):
            all_dirs.add(dir_parts[:i])
    sorted_dirs = sorted(all_dirs)

    lines: list[str] = []

    def _render_dir(dir_parts: tuple, indent: str, is_last: bool) -> None:
        if dir_parts:  # skip root itself
            connector = "└── " if is_last else "├── "
            lines.append(f"{indent}{connector}{dir_parts[-1]}/")
            child_indent = indent + ("    " if is_last else "│   ")
        else:
            child_indent = ""

        # Child directories
        child_dirs = sorted(
            d for d in sorted_dirs
            if len(d) == len(dir_parts) + 1 and d[:len(dir_parts)] == dir_parts
        )
        # Files in this directory
        files = sorted(tree.get(dir_parts, []))

        total_children = len(child_dirs) + len(files)
        for idx, child in enumerate(child_dirs):
            is_child_last = (idx == total_children - 1) and not files
            _render_dir(child, child_indent, is_child_last)

        for idx, fname in enumerate(files):
            connector = "└── " if idx == len(files) - 1 else "├── "
            lines.append(f"{child_indent}{connector}{fname}")

    _render_dir((), "", False)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output path resolver
# ---------------------------------------------------------------------------

def _resolve_output_path(cfg: "MergerConfig") -> Path:
    root    = Path(cfg.source)
    out_dir = (
        Path(cfg.output_dir)
        if Path(cfg.output_dir).is_absolute()
        else root / cfg.output_dir
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    ts       = datetime.now().strftime(cfg.timestamp_format)
    return out_dir / f"{cfg.output_prefix}_{ts}.txt"


# ---------------------------------------------------------------------------
# Header builder
# ---------------------------------------------------------------------------

def _build_header(cfg: "MergerConfig", file_count: int, tree: str) -> str:
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep = "=" * 60
    lines = [
        f"src:{cfg.source} ts:{ts}",
        "---",
        "# universal-code-merger v2",
        f"# Profile  : {cfg.profile_name}",
        f"# Source   : {cfg.source}",
        f"# Author   : {cfg.author or '-'}",
        f"# Created  : {ts}",
        f"# Files    : {file_count}",
        f"# Dry-Run  : {cfg.dry_run}",
        f"# Notes    : {cfg.notes or '-'}",
        f"# {sep}",
        "#",
        "# Directory Structure",
        "# ---",
    ]
    for tree_line in tree.splitlines():
        lines.append(f"# {tree_line}" if tree_line else "#")
    lines.append(f"# {sep}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def merge(cfg: "MergerConfig") -> None:
    start_time  = datetime.now()
    source_root = Path(cfg.source)

    if not source_root.exists():
        print(f"[ERROR] Source directory not found: {source_root}")
        return

    output_path = _resolve_output_path(cfg)
    engine      = FilterEngine(cfg)

    print(f"[INFO] Scanning : {source_root}")
    if cfg.dry_run:
        print("[INFO] Mode     : DRY-RUN (no output written)")
    print(f"[INFO] Output   : {output_path}")
    print()

    # ── Walk & collect ────────────────────────────────────────────────
    collected: list[Path] = []
    skipped:   int        = 0
    errors:    list[str]  = []
    warnings:  list[str]  = []

    for dirpath, dirs, files in os.walk(source_root):
        current_dir = Path(dirpath)

        dirs[:] = sorted(
            d for d in dirs
            if engine.should_traverse_dir(current_dir / d, source_root)
        )

        for filename in sorted(files):
            file_path = current_dir / filename
            try:
                include, reason = engine.should_include_file(file_path, source_root)
            except OSError as exc:
                errors.append(str(file_path))
                print(f"  [ERR] {file_path.relative_to(source_root)} — {exc}")
                continue

            if include:
                collected.append(file_path)
                print(f"  [OK]  {file_path.relative_to(source_root)}")
            else:
                skipped += 1

    # ── Write output ──────────────────────────────────────────────────
    duration = (datetime.now() - start_time).total_seconds()

    if not cfg.dry_run and collected:
        tree   = _build_tree(source_root, collected)
        header = _build_header(cfg, len(collected), tree)

        try:
            with open(output_path, "w", encoding=cfg.encoding) as fout:
                fout.write(header + "\n\n")
                for file_path in collected:
                    rel = file_path.relative_to(source_root)
                    fout.write(f"---\n# {rel}\n")
                    try:
                        content = file_path.read_text(encoding=cfg.encoding, errors="replace")
                        fout.write(content)
                        if not content.endswith("\n"):
                            fout.write("\n")
                    except OSError as exc:
                        errors.append(str(file_path))
                        fout.write(f"[READ ERROR: {exc}]\n")
        except OSError as exc:
            print(f"\n[ERROR] Could not write output: {exc}")
            return

    # ── Summary ───────────────────────────────────────────────────────
    print()
    if cfg.dry_run:
        print(f"[DRY-RUN] Would merge : {len(collected)} file(s)")
        print(f"[DRY-RUN] Skipped     : {skipped}")
    else:
        print(f"[DONE] Merged   : {len(collected)} file(s) → {output_path}")
        print(f"[INFO] Skipped  : {skipped}")
        print(f"[INFO] Errors   : {len(errors)}")
        print(f"[INFO] Duration : {duration:.3f}s")

        log_run(
            cfg=cfg,
            output_path=output_path,
            files_merged=len(collected),
            files_skipped=skipped,
            errors=errors,
            warnings=warnings,
            duration=duration,
        )
