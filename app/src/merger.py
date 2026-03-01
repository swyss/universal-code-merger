"""
universal-code-merger v2
Core Merge Engine

Walks the source directory, applies the FilterEngine,
and writes all collected file contents into a single output file.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.filters import FilterEngine
from src.logger import log_run

if TYPE_CHECKING:
    from src.config_loader import MergerConfig


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_output_path(cfg: "MergerConfig") -> Path:
    """
    Build the timestamped output file path.
    Creates the output directory if it does not exist.

    Output is always placed INSIDE the source root:
        <source>/outputs/prefix_YYYY-MM-DD_HH-MM-SS.txt
    """
    root = Path(cfg.source)
    out_dir = (
        Path(cfg.output_dir)  # absolute path — use as-is
        if Path(cfg.output_dir).is_absolute()
        else root / cfg.output_dir  # relative — anchor to source root ✅
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime(cfg.timestamp_format)
    filename = f"{cfg.output_prefix}_{ts}.txt"
    return out_dir / filename


def _build_header(cfg: "MergerConfig", output_path: Path, file_count: int) -> str:
    """
    Build the metadata header written at the top of the merged file.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"src:{cfg.source} ts:{ts}\n"
        f"---\n"
        f"# universal-code-merger v2\n"
        f"# Profile  : {cfg.profile_name}\n"
        f"# Source   : {cfg.source}\n"
        f"# Author   : {cfg.author or '-'}\n"
        f"# Created  : {ts}\n"
        f"# Files    : {file_count}\n"
        f"# Dry-Run  : {cfg.dry_run}\n"
        f"# Notes    : {cfg.notes or '-'}\n"
        f"# {'=' * 60}\n"
        f"# output  : {output_path}\n"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def merge(cfg: "MergerConfig") -> None:
    """
    Main entry point for the merge engine.

    Steps:
      1. Build FilterEngine from config
      2. Walk source directory tree
      3. Apply directory + file filters
      4. Collect passing files
      5. Write (or preview in dry-run) merged output
      6. Append run to JSONL log
    """
    start_time = datetime.now()
    source_root = Path(cfg.source)

    if not source_root.exists():
        print(f"[ERROR] Source directory not found: {source_root}")
        return

    output_path = _resolve_output_path(cfg)
    engine = FilterEngine(cfg)

    print(f"[INFO] Scanning : {source_root}")

    if cfg.dry_run:
        print(f"[INFO] Mode     : DRY-RUN (no output written)")

    print(f"[INFO] Output   : {output_path}")
    print()

    # ------------------------------------------------------------------
    # Walk & collect
    # ------------------------------------------------------------------
    collected: list[Path] = []
    skipped: int = 0
    errors: list[str] = []
    warnings: list[str] = []

    for dirpath, dirs, files in os.walk(source_root):
        current_dir = Path(dirpath)

        # --- Filter subdirectories in-place (controls os.walk recursion) ---
        dirs[:] = sorted(
            d for d in dirs
            if engine.should_traverse_dir(current_dir / d, source_root)
        )

        # --- Filter files ---
        for filename in sorted(files):
            file_path = current_dir / filename

            try:
                include, reason = engine.should_include_file(
                    file_path, source_root
                )
            except OSError as exc:
                errors.append(str(file_path))
                print(f"  [ERR] {file_path.relative_to(source_root)} ({exc})")
                continue

            if include:
                collected.append(file_path)
                rel = file_path.relative_to(source_root)
                print(f"  [OK] {rel}")
            else:
                skipped += 1

    # ------------------------------------------------------------------
    # Write output (skip if dry-run)
    # ------------------------------------------------------------------
    duration = (datetime.now() - start_time).total_seconds()

    if not cfg.dry_run and collected:
        header = _build_header(cfg, output_path, len(collected))

        try:
            with open(output_path, "w", encoding=cfg.encoding) as fout:
                fout.write(header + "\n")

                for file_path in collected:
                    rel = file_path.relative_to(source_root)
                    fout.write(f"---\n# {rel}\n")

                    try:
                        content = file_path.read_text(
                            encoding=cfg.encoding, errors="replace"
                        )
                        fout.write(content)
                        fout.write("\n")
                    except OSError as exc:
                        errors.append(str(file_path))
                        fout.write(f"[READ ERROR: {exc}]\n")

        except OSError as exc:
            print(f"\n[ERROR] Could not write output file: {exc}")
            return

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()

    if cfg.dry_run:
        print(f"[DRY-RUN] Would merge : {len(collected)} file(s)")
        print(f"[DRY-RUN] Skipped     : {skipped}")
    else:
        print(f"[DONE] {len(collected)} file(s) -> {output_path}")
        print(f"[INFO] Skipped  : {skipped}")
        print(f"[INFO] Errors   : {len(errors)}")
        print(f"[INFO] Duration : {duration:.2f}s")

    # ------------------------------------------------------------------
    # JSONL run log
    # ------------------------------------------------------------------
    if not cfg.dry_run:
        log_run(
            cfg=cfg,
            output_path=output_path,
            files_merged=len(collected),
            files_skipped=skipped,
            errors=errors,
            warnings=warnings,
            duration=duration,
        )
