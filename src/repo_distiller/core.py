from pathlib import Path
from pathspec import PathSpec

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
}

DEFAULT_EXCLUDE_SUFFIXES = {".egg-info"}

DEFAULT_EXCLUDE_FILES = {
    # lock files
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "uv.lock",
    "Gemfile.lock",
    "Cargo.lock",
    "composer.lock",
    # git metadata
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    # licence
    "LICENSE",
    "LICENCE",
    "LICENSE.md",
    "LICENCE.md",
    "LICENSE.txt",
    "LICENCE.txt",
}


def rel(path: Path, root: Path) -> Path:
    """Compute the relative path from root to path.

    Args:
        path: The absolute path to relativize.
        root: The root directory to compute the relative path from.

    Returns:
        The portion of path that is relative to root.
    """
    return path.relative_to(root)


def matches_any_prefix(path: Path, prefixes: list[str]) -> bool:
    """Check whether a path starts with any of the given string prefixes.

    Args:
        path: The path to check.
        prefixes: A list of string prefixes to match against.

    Returns:
        True if the string representation of path starts with any prefix.
    """
    return any(str(path).startswith(p) for p in prefixes)


def is_default_excluded(path: Path) -> bool:
    """Determine whether a relative path matches any built-in exclusion rule.

    Checks the path against DEFAULT_EXCLUDE_FILES, DEFAULT_EXCLUDE_DIRS,
    and DEFAULT_EXCLUDE_SUFFIXES.

    Args:
        path: A relative path (from the repo root) to check.

    Returns:
        True if the path should be excluded by default rules.
    """
    if path.name in DEFAULT_EXCLUDE_FILES:
        return True
    return any(
        part in DEFAULT_EXCLUDE_DIRS or any(part.endswith(suf) for suf in DEFAULT_EXCLUDE_SUFFIXES)
        for part in path.parts
    )


def is_excluded(
    path: Path,
    root: Path,
    exclude_cfg: dict,
    gitignore: PathSpec | None,
) -> bool:
    """Check whether a path should be excluded from output.

    Applies default exclusions, gitignore patterns, and user-provided
    exclude configuration (paths and extensions).

    Args:
        path: Absolute path to the file or directory.
        root: Repository root directory.
        exclude_cfg: Parsed exclude YAML config with optional "paths"
            and "extensions" keys.
        gitignore: Compiled gitignore PathSpec, or None.

    Returns:
        True if the path should be excluded.
    """
    r = rel(path, root)

    if is_default_excluded(r):
        return True

    if gitignore and gitignore.match_file(str(r)):
        return True

    if matches_any_prefix(r, exclude_cfg.get("paths", [])):
        return True

    if r.suffix in exclude_cfg.get("extensions", []):
        return True

    return False


def is_included(path: Path, root: Path, include_cfg: dict) -> bool:
    """Check whether a path matches the include configuration.

    If no include paths are configured, all paths are included.

    Args:
        path: Absolute path to check.
        root: Repository root directory.
        include_cfg: Parsed include YAML config with an optional "paths" key.

    Returns:
        True if the path is included (or no include filter is set).
    """
    include_paths = include_cfg.get("paths", [])
    if not include_paths:
        return True

    return matches_any_prefix(rel(path, root), include_paths)


def file_allowed(
    path: Path,
    root: Path,
    include_cfg: dict,
    exclude_cfg: dict,
    gitignore: PathSpec | None,
) -> bool:
    """Determine whether a file should be included in the distilled output.

    Applies exclusion rules, inclusion filters, extension filters, and
    file size limits.

    Args:
        path: Absolute path to the candidate file.
        root: Repository root directory.
        include_cfg: Parsed include YAML config with optional "paths",
            "extensions", and "limits" keys.
        exclude_cfg: Parsed exclude YAML config.
        gitignore: Compiled gitignore PathSpec, or None.

    Returns:
        True if the file passes all filters and should be collected.
    """
    if not path.is_file():
        return False

    if is_excluded(path, root, exclude_cfg, gitignore):
        return False

    if not is_included(path, root, include_cfg):
        return False

    allowed_exts = include_cfg.get("extensions")
    if allowed_exts and path.suffix not in allowed_exts:
        return False

    max_kb = include_cfg.get("limits", {}).get("max_file_size_kb", 512)
    return path.stat().st_size <= max_kb * 1024


def collect_files(
    root: Path,
    include_cfg: dict,
    exclude_cfg: dict,
    gitignore: PathSpec | None,
) -> list[Path]:
    """Collect all allowed files from the repository, sorted by path.

    Recursively walks the repository and returns files that pass all
    include/exclude filters.

    Args:
        root: Repository root directory.
        include_cfg: Parsed include YAML configuration.
        exclude_cfg: Parsed exclude YAML configuration.
        gitignore: Compiled gitignore PathSpec, or None.

    Returns:
        A sorted list of absolute Paths to the allowed files.
    """
    return sorted(
        p
        for p in root.rglob("*")
        if file_allowed(p, root, include_cfg, exclude_cfg, gitignore)
    )


def build_tree(root: Path, exclude_cfg: dict, gitignore: PathSpec | None) -> list[str]:
    """Build an ASCII directory tree representation of the repository.

    Produces a list of lines resembling the ``tree`` command output,
    excluding paths matched by the exclusion rules.

    Args:
        root: Repository root directory.
        exclude_cfg: Parsed exclude YAML configuration.
        gitignore: Compiled gitignore PathSpec, or None.

    Returns:
        A list of strings representing the tree, one line per entry.
    """
    lines = []

    def walk(dir_path: Path, prefix=""):
        entries = sorted(
            [
                p
                for p in dir_path.iterdir()
                if not is_excluded(p, root, exclude_cfg, gitignore)
            ],
            key=lambda p: (p.is_file(), p.name.lower()),
        )

        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(prefix + connector + entry.name)

            if entry.is_dir():
                extension = "    " if i == len(entries) - 1 else "│   "
                walk(entry, prefix + extension)

    lines.append(f"{root.name}/")
    walk(root)
    return lines
