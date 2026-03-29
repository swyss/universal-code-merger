"""
universal-code-merger v2 — Config loader.

Layer order (last wins):
    1. configs/base/global_config.json   — global defaults
    2. configs/<profile>.json            — project overrides  (additive lists)
    3. configs/base/.env                 — personal overrides
    4. CLI arguments                     — runtime overrides
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Project root:  app/src/config_loader.py -> app/src -> app -> ROOT
ROOT: Path = Path(__file__).resolve().parent.parent.parent
GLOBAL_CONFIG: Path = ROOT / "configs" / "base" / "global_config.json"
ENV_FILE: Path = ROOT / "configs" / "base" / ".env"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError(f"Config is empty: {path}")
    return json.loads(raw)


def _read_env(path: Path = ENV_FILE) -> dict[str, str]:
    """Minimal .env parser — no external dependencies."""
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if key.strip() and value:
            result[key.strip()] = value
    return result


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------

@dataclass
class MergerConfig:
    # ── Paths ────────────────────────────────────────────────────────────
    source: str = ""
    output_dir: str = "outputs"
    log_dir: str = "logs"
    output_prefix: str = "merged"
    profile_name: str = "default"

    # ── Behaviour ────────────────────────────────────────────────────────
    encoding: str = "utf-8"
    timestamp_format: str = "%Y-%m-%d_%H-%M-%S"
    max_file_size_kb: Optional[int] = 500
    max_depth: Optional[int] = None
    dry_run: bool = False
    warn_on_secrets: bool = True

    # ── Filters ──────────────────────────────────────────────────────────
    whitelist_ext: frozenset = field(default_factory=frozenset)
    blacklist_dirs: frozenset = field(default_factory=frozenset)
    blacklist_files: set = field(default_factory=set)
    blacklist_patterns: list = field(default_factory=list)
    whitelist_files: list = field(default_factory=list)

    # ── Meta ─────────────────────────────────────────────────────────────
    author: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_config(
        profile: Optional[str] = None,
        cli_source: Optional[str] = None,
) -> MergerConfig:

    # 1 — Global defaults
    g = _read_json(GLOBAL_CONFIG)
    cfg = MergerConfig(
        output_dir       = g.get("output_dir", "outputs"),
        log_dir          = g.get("log_dir", "logs"),
        encoding         = g.get("encoding", "utf-8"),
        timestamp_format = g.get("timestamp_format", "%Y-%m-%d_%H-%M-%S"),
        max_file_size_kb = g.get("max_file_size_kb", 500),
        max_depth        = g.get("max_depth"),
        dry_run          = g.get("dry_run", False),
        warn_on_secrets  = g.get("warn_on_secrets", True),
        whitelist_ext    = frozenset(g.get("whitelist_ext", [])),
        blacklist_dirs   = frozenset(g.get("blacklist_dirs", [])),
        blacklist_files  = set(g.get("blacklist_files", [])),
        blacklist_patterns = g.get("blacklist_patterns", []),
    )

    # 2 — Profile overrides (lists are additive)
    if profile:
        profile_path = ROOT / "configs" / f"{profile}.json"
        if profile_path.exists():
            p = _read_json(profile_path)
            cfg.profile_name     = p.get("profile_name", profile)
            cfg.source           = p.get("source", cfg.source)
            cfg.output_prefix    = p.get("output_prefix", profile)
            cfg.notes            = p.get("notes", "")
            cfg.max_file_size_kb = p.get("max_file_size_kb", cfg.max_file_size_kb)
            cfg.max_depth        = p.get("max_depth", cfg.max_depth)
            cfg.whitelist_files  = p.get("whitelist_files", [])
            # Additive merging — profile extends, never replaces globals
            cfg.whitelist_ext    |= frozenset(p.get("whitelist_ext", []))
            cfg.blacklist_dirs   |= frozenset(p.get("blacklist_dirs", []))
            cfg.blacklist_files  |= set(p.get("blacklist_files", []))
            cfg.blacklist_patterns += p.get("blacklist_patterns", [])
        else:
            print(f"[WARN] Profile not found: {profile_path}")

    # 3 — .env personal overrides
    env = _read_env()
    if "UCM_OUTPUT_DIR" in env: cfg.output_dir  = env["UCM_OUTPUT_DIR"]
    if "UCM_AUTHOR"     in env: cfg.author       = env["UCM_AUTHOR"]
    if "UCM_DEFAULT_PROFILE" in env and not profile:
        cfg.profile_name = env["UCM_DEFAULT_PROFILE"]

    # 4 — CLI (highest priority)
    if cli_source:
        cfg.source = str(Path(cli_source).resolve())

    return cfg


def list_profiles() -> list[str]:
    """Return sorted profile names from configs/ (excludes base/)."""
    cfg_path = ROOT / "configs"
    if not cfg_path.exists():
        return []
    return sorted(
        p.stem for p in cfg_path.glob("*.json")
        if p.parent.name != "base"
    )
