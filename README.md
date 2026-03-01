# universal-code-merger

Recursively collects all relevant source files from a directory
and merges them into a single compact text file.
Useful for feeding entire codebases into AI tools or code reviews.

## Usage

```bash
python merger.py <source_folder> [output_file]
```

**Examples:**
```bash
python merger.py ./src
python merger.py ./src output.txt
python merger.py D:\repos\myproject merged.txt
```

## Supported File Types

`.py` `.ts` `.js` `.vue` `.json` `.toml` `.yml` `.yaml`
`.xml` `.html` `.css` `.md` `.txt` `.env` `.config`

## Ignored Directories

`node_modules` `__pycache__` `.git` `.venv` `venv`
`dist` `build` `.env.local` `root`

## Output Format

```
src:/absolute/path ts:2026-03-01 07:30:00
---
# relative/path/to/file.py
<file content>
---
```

## Requirements

- Python 3.8+ (stdlib only — zero dependencies)

## License

MIT License
