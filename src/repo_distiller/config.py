from pathlib import Path
import yaml
from pathspec import PathSpec


def load_yaml(path: Path | None) -> dict:
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


def load_gitignore(repo: Path) -> PathSpec | None:
    """Parse the .gitignore file in a repository root into a PathSpec.

    Args:
        repo: Path to the repository root directory.

    Returns:
        A PathSpec compiled from the .gitignore patterns, or None if no
        .gitignore file exists.
    """
    gitignore = repo / ".gitignore"
    if not gitignore.exists():
        return None

    patterns = gitignore.read_text(encoding="utf-8").splitlines()
    return PathSpec.from_lines("gitignore", patterns)
