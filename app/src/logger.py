"""
universal-code-merger v2 — JSONL run logger.
Log: <project_root>/logs/run_history.jsonl
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config_loader import MergerConfig

_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def log_run(
        cfg: "MergerConfig",
        output_path: Path,
        files_merged: int,
        files_skipped: int,
        errors: list[str],
        warnings: list[str],
        duration: float,
) -> None:
    log_dir  = _ROOT / cfg.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "run_history.jsonl"

    entry = {
        "ts":            datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "profile":       cfg.profile_name,
        "source":        str(cfg.source),
        "output":        str(output_path),
        "author":        cfg.author or "",
        "files_merged":  files_merged,
        "files_skipped": files_skipped,
        "errors":        len(errors),
        "warnings":      len(warnings),
        "duration_sec":  round(duration, 4),
        "dry_run":       cfg.dry_run,
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Log      : {log_file}")
    except OSError as exc:
        print(f"[WARN] Could not write run log: {exc}")
