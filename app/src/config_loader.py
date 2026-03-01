"""
universal-code-merger v2
Config Loader

File location : app/src/config_loader.py

Path resolution:
    app/src/config_loader.py
      -> .parent = app/src
      -> .parent = app
      -> .parent = ROOT (project root)

Base config files:
    configs/base/global_config.json
    configs/base/.env

Merge order (last wins):
    global_config.json -> profile .json -> .env -> CLI args
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Root & base config paths
# ---------------------------------------------------------------------------

# app/src/config_loader.py -> parent = app/src -> parent = app -> parent = ROOT
ROOT: Path = Path(__file__).resolve().parent.parent.parent

BASE_DIR: Path = ROOT / "configs" / "base"
GLOBAL_CONFIG_PATH: Path = BASE_DIR / "global_config.json"
ENV_PATH: Path = BASE_DIR / ".env"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _load_env(path: Path = ENV_PATH) -> dict:
    """
    Minimal .env parser — no external dependencies.
    Skips blank lines and comments (#).
    """
    env: dict = {}
    if not path.exists():
        return env

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value:
            env[key] = value

    return env


def _load_json(path: Path) -> dict:
    """
    Read and parse a JSON file.
    Raises FileNotFoundError if missing, ValueError if empty or invalid.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            f"Expected location: configs/base/global_config.json"
        )

    raw = path.read_text(encoding="utf-8").strip()

    if not raw:
        raise ValueError(
            f"Config file is empty: {path}\n"
            "Please add valid JSON content."
        )

    return json.loads(raw)


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------

@dataclass
class MergerConfig:
    # Paths
    source: str = ""
    output_dir: str = "outputs"
    config_dir: str = "configs"
    log_dir: str = "logs"
    output_prefix: str = "merged"
    profile_name: str = "default"

    # Behaviour
    timestamp_format: str = "%Y-%m-%d_%H-%M-%S"
    max_file_size_kb: Optional[int] = 500
    max_depth: Optional[int] = None
    dry_run: bool = False
    encoding: str = "utf-8"
    warn_on_secrets: bool = True

    # Filter sets
    whitelist_ext: frozenset = field(default_factory=frozenset)
    blacklist_dirs: frozenset = field(default_factory=frozenset)
    blacklist_files: set = field(default_factory=set)
    blacklist_patterns: list = field(default_factory=list)
    whitelist_files: list = field(default_factory=list)

    # Meta
    author: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Config builder
# ---------------------------------------------------------------------------

def build_config(
        profile: Optional[str] = None,
        cli_source: Optional[str] = None,
) -> MergerConfig:
    """
    Build a MergerConfig by layering configs in order:
        1. configs/base/global_config.json  (base defaults)
        2. configs/<profile>.json           (project overrides)
        3. configs/base/.env               (personal / secret overrides)
        4. CLI arguments                    (highest priority)
    """

    # ------------------------------------------------------------------
    # 1. Global config — configs/base/global_config.json
    # ------------------------------------------------------------------
    g = _load_json(GLOBAL_CONFIG_PATH)

    cfg = MergerConfig(
        output_dir=g.get("output_dir", "outputs"),
        config_dir=g.get("config_dir", "configs"),
        log_dir=g.get("log_dir", "logs"),
        timestamp_format=g.get("timestamp_format", "%Y-%m-%d_%H-%M-%S"),
        max_file_size_kb=g.get("max_file_size_kb", 500),
        max_depth=g.get("max_depth", None),
        dry_run=g.get("dry_run", False),
        encoding=g.get("encoding", "utf-8"),
        warn_on_secrets=g.get("warn_on_secrets", True),
        whitelist_ext=frozenset(g.get("global_whitelist_ext", [])),
        blacklist_dirs=frozenset(g.get("global_blacklist_dirs", [])),
        blacklist_files=set(g.get("global_blacklist_files", [])),
        blacklist_patterns=g.get("global_blacklist_patterns", []),
    )

    # ------------------------------------------------------------------
    # 2. Project profile — configs/<profile>.json
    # ------------------------------------------------------------------
    if profile:
        profile_path = ROOT / cfg.config_dir / f"{profile}.json"
        if profile_path.exists():
            p = _load_json(profile_path)
            cfg.profile_name = p.get("profile_name", profile)
            cfg.source = p.get("source", cfg.source)
            cfg.output_prefix = p.get("output_prefix", profile)
            cfg.notes = p.get("notes", "")
            cfg.max_file_size_kb = p.get("max_file_size_kb", cfg.max_file_size_kb)
            cfg.max_depth = p.get("max_depth", cfg.max_depth)
            cfg.whitelist_files = p.get("whitelist_files", [])

            # Additive — never replace globals
            cfg.whitelist_ext |= frozenset(p.get("extra_whitelist_ext", []))
            cfg.blacklist_dirs |= frozenset(p.get("extra_blacklist_dirs", []))
            cfg.blacklist_files |= set(p.get("extra_blacklist_files", []))
            cfg.blacklist_patterns += p.get("extra_blacklist_patterns", [])
        else:
            print(f"[WARN] Profile not found: {profile_path}")

    # ------------------------------------------------------------------
    # 3. .env overrides — configs/base/.env
    # ------------------------------------------------------------------
    env = _load_env()

    if "UCM_OUTPUT_DIR" in env:
        cfg.output_dir = env["UCM_OUTPUT_DIR"]
    if "UCM_AUTHOR" in env:
        cfg.author = env["UCM_AUTHOR"]
    if "UCM_DEFAULT_PROFILE" in env and not profile:
        cfg.profile_name = env["UCM_DEFAULT_PROFILE"]

    # ------------------------------------------------------------------
    # 4. CLI override — resolve & normalise the raw path immediately.
    #    Path.resolve() handles backslashes, forward slashes, relative
    #    paths, and UNC paths correctly on all platforms.
    # ------------------------------------------------------------------
    if cli_source:
        cfg.source = str(Path(cli_source).resolve())

    return cfg


# ---------------------------------------------------------------------------
# Profile discovery helper
# ---------------------------------------------------------------------------

def list_profiles(config_dir: str = "configs") -> list[str]:
    """
    Return all profile names available in configs/.
    Excludes the base/ subdirectory.
    """
    cfg_path = ROOT / config_dir
    if not cfg_path.exists():
        return []
    return sorted(
        p.stem for p in cfg_path.glob("*.json")
        if p.parent.name != "base"
    )
