from pathlib import Path
import yaml
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern


def load_yaml(path: Path | None) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_gitignore(repo: Path) -> PathSpec | None:
    gitignore = repo / ".gitignore"
    if not gitignore.exists():
        return None

    patterns = gitignore.read_text(encoding="utf-8").splitlines()
    return PathSpec.from_lines(GitWildMatchPattern, patterns)
