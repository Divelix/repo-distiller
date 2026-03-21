# repo-distiller

Convert a code repository into a single text file for LLM prompting.

When working with an LLM on a codebase, you often need to share the full context of a project. `repo-distiller` walks a repository, renders a directory tree, and concatenates all relevant source files into one clean text file you can paste into a prompt or attach to a conversation.

## Installation

```bash
pip install repo-distiller
```

## Usage

```bash
repo-distiller distill <repo> -o <output> [options]
```

### Arguments

| Argument | Description |
| --- | --- |
| `repo` | Path to the repository root |
| `-o`, `--output` | Output file path, or `-` for stdout |
| `-i`, `--include` | Path to an include config YAML (optional) |
| `-e`, `--exclude` | Path to an exclude config YAML (optional) |
| `--no-default-excludes` | Disable built-in exclusion rules |
| `--dry-run` / `--list` | List files that would be included without writing output |
| `-v`, `--verbose` | Show progress information on stderr |

### Basic example

```bash
repo-distiller distill ./my-project -o context.txt
```

This writes a directory tree followed by the contents of every file, respecting `.gitignore` (including nested `.gitignore` files) and skipping common noise (lock files, `__pycache__`, `.venv`, `node_modules`, etc.).

### Write to stdout

```bash
repo-distiller distill ./my-project -o - | pbcopy
```

### Preview files without writing

```bash
repo-distiller distill ./my-project --dry-run
```

### Output format

```text
my-project/
├── src/
│   ├── main.py
│   └── utils.py
└── pyproject.toml

==============================
FILE: src/main.py
==============================
<file contents>

==============================
FILE: src/utils.py
==============================
<file contents>
```

### Include config

Limit the output to specific paths, extensions, or file sizes:

```yaml
# include.yaml
paths:
  - src/
extensions:
  - .py
  - .ts
limits:
  max_file_size_kb: 256
```

```bash
repo-distiller distill ./my-project -o context.txt -i include.yaml
```

### Exclude config

Suppress additional paths or extensions beyond the defaults:

```yaml
# exclude.yaml
paths:
  - tests/
  - docs/
extensions:
  - .md
  - .txt
```

```bash
repo-distiller distill ./my-project -o context.txt -e exclude.yaml
```

> When `-e` is provided, `.gitignore` is **not** loaded automatically — the exclude config takes full control.

### Combining both

```bash
repo-distiller distill ./my-project -o context.txt -i include.yaml -e exclude.yaml
```

## Default exclusions

The following are excluded by default (disable with `--no-default-excludes`):

- Directories: `.git`, `__pycache__`, `.venv`, `venv`, `node_modules`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `dist`, `build`, `.eggs`
- Suffixes: `.egg-info`
- Files: common lock files (e.g. `uv.lock`, `package-lock.json`), `.gitignore`, `LICENSE`

## License

MIT
