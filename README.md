# universal-code-merger

Recursively collects all relevant source files from a directory tree
and merges them into a single compact, timestamped text file.
Ideal for feeding entire codebases into AI tools, code reviews, or audits.

---

## Project Structure

```
universal-code-merger/
├── app/
│   ├── main.py               # Entry point
│   └── src/
│       ├── __init__.py
│       ├── cli.py            # Argument parsing & CLI entrypoint
│       ├── config_loader.py  # Layered config system (global → profile → .env → CLI)
│       ├── filters.py        # File/directory filter engine
│       ├── logger.py         # JSONL run logger
│       └── merger.py         # Core merge engine
├── configs/
│   ├── base/
│   │   ├── global_config.json   # Global defaults (committed)
│   │   ├── .env                 # Personal overrides (NOT committed)
│   │   └── .env.example         # Template for .env (committed)
│   └── project.json             # Example project profile
├── outputs/                  # Auto-created — merged output files
├── logs/                     # Auto-created — run_history.jsonl
├── .gitignore
└── README.md
```

---

## Requirements

- Python 3.10+ (stdlib only — zero external dependencies)
- Works on Windows, macOS, Linux

---

## Quick Start

```bash
# Navigate to the app/ directory
cd path/to/universal-code-merger/app

# Merge a directory directly
python main.py path/to/your/project

# Use a named profile
python main.py --profile project

# Preview without writing output (dry-run)
python main.py --profile project --dry-run

# List all available profiles
python main.py --list-profiles
```

> **Git Bash on Windows:** Always use forward-slashes in paths.
> `C:/Users/you/myproject` — not `C:\Users\you\myproject`

> **run with profile:** Always define `source` parameter.

---

## Configuration System

Config layers are applied in order — **last wins**:

| Priority      | Source                            | Description                                    |
|---------------|-----------------------------------|------------------------------------------------|
| 1 *(lowest)*  | `configs/base/global_config.json` | Global defaults, filter lists, output settings |
| 2             | `configs/<profile>.json`          | Project-specific overrides                     |
| 3             | `configs/base/.env`               | Personal / secret overrides (never committed)  |
| 4 *(highest)* | CLI arguments                     | Runtime overrides                              |

---

### `configs/base/global_config.json` — Key Fields

| Field                       | Type        | Description                                        |
|-----------------------------|-------------|----------------------------------------------------|
| `output_dir`                | string      | Output directory (default: `outputs`)              |
| `log_dir`                   | string      | Log directory (default: `logs`)                    |
| `timestamp_format`          | string      | Timestamp format for output filenames              |
| `encoding`                  | string      | File encoding (default: `utf-8`)                   |
| `max_file_size_kb`          | int \| null | Skip files larger than N KB (`null` = unlimited)   |
| `max_depth`                 | int \| null | Max directory traversal depth (`null` = unlimited) |
| `dry_run`                   | bool        | Preview mode — no files written                    |
| `warn_on_secrets`           | bool        | Warn when sensitive filenames are included         |
| `global_whitelist_ext`      | list        | Allowed file extensions                            |
| `global_blacklist_dirs`     | list        | Directories never traversed                        |
| `global_blacklist_files`    | list        | Filename glob patterns to skip                     |
| `global_blacklist_patterns` | list        | Glob patterns matched against full filenames       |

---

### `configs/<profile>.json` — Key Fields

| Field                   | Type   | Description                                    |
|-------------------------|--------|------------------------------------------------|
| `source`                | string | Default source directory for this profile      |
| `output_prefix`         | string | Output filename prefix                         |
| `notes`                 | string | Embedded in output file header                 |
| `extra_whitelist_ext`   | list   | Additional allowed extensions                  |
| `extra_blacklist_dirs`  | list   | Additional blocked directories                 |
| `extra_blacklist_files` | list   | Additional blocked filename glob patterns      |
| `whitelist_files`       | list   | Filenames always included (bypass all filters) |

---

### `configs/base/.env` — Supported Variables

```ini
UCM_AUTHOR = yourname           # Embedded in merged output header
UCM_OUTPUT_DIR = outputs        # Override output directory
UCM_DEFAULT_PROFILE =          # Auto-load this profile if none specified
UCM_LOG_LEVEL = INFO            # Reserved for future use
```

> Copy `.env.example` to `.env` and fill in your values.
> **Never commit `.env` — it is listed in `.gitignore`.**

---

## Supported File Types (default)

`.py` `.ts` `.js` `.vue` `.json` `.toml` `.yml` `.yaml`
`.xml` `.html` `.css` `.md` `.txt` `.env` `.config`

Extend via `global_whitelist_ext` or `extra_whitelist_ext` in a profile.

---

## Ignored Directories (default)

`node_modules` `__pycache__` `.git` `.idea` `.venv` `venv`
`dist` `build` `outputs` `logs`

Extend via `global_blacklist_dirs` or `extra_blacklist_dirs` in a profile.

---

## Output Format

Each merged file starts with a metadata header followed by file sections:

```
src:/your/project ts:2026-03-01 12:55:54
---
# universal-code-merger v2
# Profile  : project
# Source   : /your/project
# Author   : yourname
# Created  : 2026-03-01 12:55:54
# Files    : 10
# Dry-Run  : False
# Notes    : -
# ============================================================
---
# app/main.py
<file content>
---
# app/src/cli.py
<file content>
---
```

---

## Run Log

Every completed run is appended to `logs/run_history.jsonl`:

```json
{
  "ts": "2026-03-01T12:55:54",
  "profile": "project",
  "source": "/your/project",
  "output": "outputs/ucm_2026-03-01_12-55-54.txt",
  "author": "yourname",
  "files_merged": 10,
  "files_skipped": 3,
  "errors": 0,
  "warnings": 0,
  "duration_sec": 0.012,
  "dry_run": false
}
```

---

## .gitignore Recommendations

```gitignore
# Personal config overrides
configs/base/.env

# Generated outputs
outputs/
logs/

# Python
__pycache__/
*.pyc
.venv/
```

---

## License

MIT License
