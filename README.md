# Universal Code Merger

## Project Description
A powerful Python tool for recursively collecting and merging source code files from project directories into a single text file. Ideal for code reviews, documentation, and AI assistants for analyzing large codebases.

## Tech Stack
**Runtime:**
- Python 3.14+ (Standard Library)
- Rich (Beautiful Terminal Output)
- PyQt6 (Optional GUI Mode)

**Features:**
- Recursive directory traversal
- Configurable file filters (Whitelist/Blacklist)
- Intelligent error handling
- Progress tracking
- Compact output formatting

## Software Architecture
**Deployment:** Single Executable (PyInstaller)
**Pattern:** Pure Python - No Dependencies Required
**Configuration:** JSON/YAML Config Files
**Output:** Structured Text Files with Metadata

## Platforms
- Command Line Interface (CLI)
- Desktop GUI (PyQt6) - Optional
- Cross-Platform (Windows/Linux/macOS)

## 🚀 Quick Start
```bash
poetry install
poetry run python code_merger.py /path/to/source --output merged_code.txt
poetry run python code_merger.py --gui  # GUI Mode
```
