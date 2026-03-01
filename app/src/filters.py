"""
universal-code-merger v2
Filter Engine

Handles all include/exclude decisions for files and directories.
Supports:
  - Extension whitelist (frozenset)
  - Directory blacklist (frozenset)
  - Filename blacklist (set of glob patterns  -> fnmatch)
  - Pattern blacklist  (list of glob patterns -> fnmatch via re)
  - Whitelist override (list of exact filenames — always included)
  - Max file size check
  - Max depth check
  - Secret filename warning
"""

import fnmatch
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config_loader import MergerConfig

# ---------------------------------------------------------------------------
# Sensitive filename fragments — warn but do not auto-exclude
# ---------------------------------------------------------------------------
_SECRET_FRAGMENTS = (
    ".env", "secret", "password", "passwd",
    "credential", "token", "apikey", "api_key",
    "private_key", "id_rsa", "id_ed25519",
)


class FilterEngine:
    """
    Central filter engine.
    Instantiate once per run with a MergerConfig, then call
    .should_include_file() and .should_traverse_dir() per path.
    """

    def __init__(self, cfg: "MergerConfig") -> None:
        self.cfg = cfg

        # ------------------------------------------------------------------
        # Glob patterns -> compiled regex via fnmatch.translate()
        # fnmatch.translate converts  "*.min.js"  ->  valid regex like
        # "(?s:.*\\.min\\.js)\\Z"  which re.compile() accepts without error.
        # ------------------------------------------------------------------
        self._pattern_regexes: list[re.Pattern] = [
            re.compile(fnmatch.translate(p))
            for p in cfg.blacklist_patterns
            if p.strip()  # skip empty strings
        ]

        # Lowercase extension set for case-insensitive matching
        self._whitelist_ext = frozenset(
            e.lower() for e in cfg.whitelist_ext
        )

        # Lowercase blacklist dirs for case-insensitive matching
        self._blacklist_dirs = frozenset(
            d.lower() for d in cfg.blacklist_dirs
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def should_traverse_dir(self, dir_path: Path, root: Path) -> bool:
        """
        Return True if the directory should be walked into.
        Excludes dirs matching the blacklist (by name or relative path).
        """
        name = dir_path.name.lower()
        rel_posix = dir_path.relative_to(root).as_posix().lower()

        # Match by directory name
        if name in self._blacklist_dirs:
            return False

        # Match by relative path segment
        # e.g. "configs/base" should block  configs/base  subtree
        for blocked in self._blacklist_dirs:
            if rel_posix == blocked or rel_posix.startswith(blocked + "/"):
                return False

        # Max depth check
        if self.cfg.max_depth is not None:
            depth = len(dir_path.relative_to(root).parts)
            if depth > self.cfg.max_depth:
                return False

        return True

    def should_include_file(
            self,
            file_path: Path,
            root: Path,
    ) -> tuple[bool, str]:
        """
        Return (include: bool, reason: str).

        Decision order:
          1. Whitelist override  -> always include
          2. Extension check     -> exclude if not whitelisted
          3. Filename blacklist  -> exclude if glob matches name
          4. Pattern blacklist   -> exclude if glob matches name
          5. File size check     -> exclude if too large
          6. Secret warning      -> include but warn
        """
        name = file_path.name
        ext = file_path.suffix.lower()

        # 1. Whitelist override — always include regardless of other rules
        if name in self.cfg.whitelist_files:
            return True, "whitelist_override"

        # 2. Extension whitelist
        if ext not in self._whitelist_ext:
            return False, f"ext_not_whitelisted ({ext})"

        # 3. Filename blacklist — glob match against bare filename
        for pattern in self.cfg.blacklist_files:
            if fnmatch.fnmatch(name, pattern):
                return False, f"blacklist_file ({pattern})"

        # 4. Pattern blacklist — compiled regex from glob patterns
        for regex in self._pattern_regexes:
            if regex.match(name):
                return False, f"blacklist_pattern ({regex.pattern})"

        # 5. File size check
        if self.cfg.max_file_size_kb is not None:
            size_kb = file_path.stat().st_size / 1024
            if size_kb > self.cfg.max_file_size_kb:
                return False, f"too_large ({size_kb:.1f} KB)"

        # 6. Secret warning — include but flag
        if self.cfg.warn_on_secrets:
            name_lower = name.lower()
            for fragment in _SECRET_FRAGMENTS:
                if fragment in name_lower:
                    print(f"  [WARN] Possible secret file included: {file_path.relative_to(root)}")
                    break

        return True, "ok"
