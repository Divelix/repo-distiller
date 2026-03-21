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
    return path.relative_to(root)


def matches_any_prefix(path: Path, prefixes: list[str]) -> bool:
    return any(str(path).startswith(p) for p in prefixes)


def is_default_excluded(path: Path) -> bool:
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
    return sorted(
        p
        for p in root.rglob("*")
        if file_allowed(p, root, include_cfg, exclude_cfg, gitignore)
    )


def build_tree(root: Path, exclude_cfg: dict, gitignore: PathSpec | None) -> list[str]:
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
