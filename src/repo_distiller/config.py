from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pathspec import PathSpec


@dataclass
class IncludeConfig:
    """Configuration controlling which files to include in output.

    Attributes:
        paths: Path prefixes to include. If empty, all paths are included.
        extensions: File extensions to include (e.g. [".py", ".js"]).
            If empty, all extensions are allowed.
        max_file_size_kb: Maximum file size in kilobytes. Files larger
            than this are skipped.
    """

    paths: list[str] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)
    max_file_size_kb: int = 512


@dataclass
class ExcludeConfig:
    """Configuration controlling which files to exclude from output.

    Attributes:
        paths: Path prefixes to exclude.
        extensions: File extensions to exclude (e.g. [".png", ".bin"]).
        use_default_excludes: Whether to apply built-in exclusion rules
            for common directories, files, and suffixes.
    """

    paths: list[str] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)
    use_default_excludes: bool = True


def _load_yaml(path: Path | None) -> dict:
    """Load a YAML configuration file and return its contents as a dict.

    Args:
        path: Path to the YAML file, or None to return an empty config.

    Returns:
        Parsed YAML contents as a dictionary, or an empty dict if path
        is None or the file is empty.
    """
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_include_config(path: Path | None) -> IncludeConfig:
    """Load an include configuration from a YAML file.

    Args:
        path: Path to the YAML file, or None for default config.

    Returns:
        An IncludeConfig populated from the file, or defaults if path is None.
    """
    raw = _load_yaml(path)
    limits = raw.get("limits", {})
    return IncludeConfig(
        paths=raw.get("paths", []),
        extensions=raw.get("extensions", []),
        max_file_size_kb=limits.get("max_file_size_kb", 512),
    )


def load_exclude_config(path: Path | None) -> ExcludeConfig:
    """Load an exclude configuration from a YAML file.

    Args:
        path: Path to the YAML file, or None for default config.

    Returns:
        An ExcludeConfig populated from the file, or defaults if path is None.
    """
    raw = _load_yaml(path)
    return ExcludeConfig(
        paths=raw.get("paths", []),
        extensions=raw.get("extensions", []),
    )


class GitIgnoreStack:
    """Accumulates .gitignore patterns from nested directories.

    Each .gitignore's patterns are matched relative to the directory
    containing that .gitignore file, following standard git behavior.

    Attributes:
        root: The repository root directory.
    """

    def __init__(self, root: Path):
        """Initialize the stack, loading the root .gitignore if present.

        Args:
            root: The repository root directory.
        """
        self.root = root
        self._specs: list[tuple[Path, PathSpec]] = []
        self._load_if_exists(root)

    def _load_if_exists(self, dir_path: Path) -> None:
        """Load a .gitignore from dir_path if the file exists.

        Args:
            dir_path: Directory to check for a .gitignore file.
        """
        gi = dir_path / ".gitignore"
        if gi.exists():
            patterns = gi.read_text(encoding="utf-8").splitlines()
            spec = PathSpec.from_lines("gitignore", patterns)
            self._specs.append((dir_path, spec))

    def push_dir(self, dir_path: Path) -> None:
        """Register a directory, loading its .gitignore if present.

        Call this for each directory encountered during traversal so that
        nested .gitignore patterns are accumulated.

        Args:
            dir_path: Absolute path to the directory being entered.
        """
        self._load_if_exists(dir_path)

    def match_file(self, path: Path) -> bool:
        """Check whether a path matches any loaded .gitignore pattern.

        Each spec is tested against the path relative to that spec's
        directory, matching standard git semantics. Directory paths are
        tested with a trailing separator so that directory-only patterns
        (ending with ``/``) match correctly.

        Args:
            path: Absolute path to check.

        Returns:
            True if the path matches any .gitignore pattern.
        """
        is_dir = path.is_dir()
        for base, spec in self._specs:
            try:
                rel_str = str(path.relative_to(base))
            except ValueError:
                continue
            # Append '/' for directories so patterns like "dir/" match.
            if is_dir:
                rel_str += "/"
            if spec.match_file(rel_str):
                return True
        return False


def load_gitignore(repo: Path) -> GitIgnoreStack | None:
    """Create a GitIgnoreStack for a repository, loading the root .gitignore.

    Args:
        repo: Path to the repository root directory.

    Returns:
        A GitIgnoreStack instance, or None if no .gitignore file exists
        at the repository root.
    """
    gitignore = repo / ".gitignore"
    if not gitignore.exists():
        return None

    return GitIgnoreStack(repo)
