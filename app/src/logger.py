"""
universal-code-merger
Run Logger

Appends a structured JSONL entry to logs/run_history.jsonl
after every successful merge run.

Log location: <project_root>/logs/run_history.jsonl
"""

import json
from datetime import datetime
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config_loader import MergerConfig

# ---------------------------------------------------------------------------
# Root resolution  (app/src/logger.py -> app/src -> app -> ROOT)
# ---------------------------------------------------------------------------
_ROOT: Path = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_run(
        cfg: "MergerConfig",
        output_path: Path,
        files_merged: int,
        files_skipped: int,
        errors: list[str],
        warnings: list[str],
        duration: float,
) -> None:
    """
    Append one JSONL line to logs/run_history.jsonl.

    Parameters
    ----------
    cfg           : Active MergerConfig for this run.
    output_path   : Path to the written output file.
    files_merged  : Number of files successfully merged.
    files_skipped : Number of files excluded by filters.
    errors        : List of file paths that caused read/write errors.
    warnings      : List of warning messages emitted during the run.
    duration      : Run duration in seconds.
    """
    # Resolve log directory relative to project root
    log_dir: Path = _ROOT / cfg.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file: Path = log_dir / "run_history.jsonl"

    entry: dict = {
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "profile": cfg.profile_name,
        "source": str(cfg.source),
        "output": str(output_path),
        "author": cfg.author or "",
        "files_merged": files_merged,
        "files_skipped": files_skipped,
        "errors": len(errors),
        "warnings": len(warnings),
        "duration_sec": round(duration, 4),
        "dry_run": cfg.dry_run,
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"[INFO] Log      : {log_file}")

    except OSError as exc:
        # Logging failure is non-fatal — warn and continue
        print(f"[WARN] Could not write run log: {exc}")
