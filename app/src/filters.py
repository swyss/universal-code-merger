"""
universal-code-merger v2 — Filter engine.

Decision order per file:
  1. whitelist_files  → always include
  2. whitelist_ext    → skip if extension not allowed
  3. blacklist_files  → skip if glob matches filename
  4. blacklist_patterns → skip if glob matches filename
  5. max_file_size_kb → skip if too large
  6. warn_on_secrets  → include but warn
"""

import fnmatch
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config_loader import MergerConfig

_SECRET_FRAGMENTS = (
    ".env", "secret", "password", "passwd", "credential",
    "token", "apikey", "api_key", "private_key", "id_rsa", "id_ed25519",
)


class FilterEngine:

    def __init__(self, cfg: "MergerConfig") -> None:
        self.cfg = cfg
        self._whitelist_ext = frozenset(e.lower() for e in cfg.whitelist_ext)
        self._blacklist_dirs = frozenset(d.lower() for d in cfg.blacklist_dirs)
        self._pattern_regexes: list[re.Pattern] = [
            re.compile(fnmatch.translate(p))
            for p in cfg.blacklist_patterns if p.strip()
        ]

    def should_traverse_dir(self, dir_path: Path, root: Path) -> bool:
        name      = dir_path.name.lower()
        rel_posix = dir_path.relative_to(root).as_posix().lower()

        for blocked in self._blacklist_dirs:
            if name == blocked:
                return False
            if rel_posix == blocked or rel_posix.startswith(blocked + "/"):
                return False

        if self.cfg.max_depth is not None:
            if len(dir_path.relative_to(root).parts) > self.cfg.max_depth:
                return False

        return True

    def should_include_file(
            self, file_path: Path, root: Path
    ) -> tuple[bool, str]:
        name = file_path.name
        ext  = file_path.suffix.lower()

        if name in self.cfg.whitelist_files:
            return True, "whitelist_override"

        if ext not in self._whitelist_ext:
            return False, f"ext_not_whitelisted ({ext})"

        for pattern in self.cfg.blacklist_files:
            if fnmatch.fnmatch(name, pattern):
                return False, f"blacklist_file ({pattern})"

        for regex in self._pattern_regexes:
            if regex.match(name):
                return False, f"blacklist_pattern ({regex.pattern})"

        if self.cfg.max_file_size_kb is not None:
            size_kb = file_path.stat().st_size / 1024
            if size_kb > self.cfg.max_file_size_kb:
                return False, f"too_large ({size_kb:.1f} KB)"

        if self.cfg.warn_on_secrets:
            name_lower = name.lower()
            if any(f in name_lower for f in _SECRET_FRAGMENTS):
                print(f"  [WARN] Possible secret: {file_path.relative_to(root)}")

        return True, "ok"
