from pathlib import Path

from pathspec import PathSpec

from repo_distiller.config import load_yaml, load_gitignore


class TestLoadYaml:
    def test_none_returns_empty_dict(self):
        assert load_yaml(None) == {}

    def test_valid_yaml(self, tmp_path):
        f = tmp_path / "cfg.yaml"
        f.write_text("paths:\n  - src/\n  - lib/\n")
        result = load_yaml(f)
        assert result == {"paths": ["src/", "lib/"]}

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        assert load_yaml(f) == {}


class TestLoadGitignore:
    def test_no_gitignore_returns_none(self, tmp_path):
        assert load_gitignore(tmp_path) is None

    def test_parses_gitignore(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("*.pyc\nbuild/\n")
        spec = load_gitignore(tmp_path)
        assert isinstance(spec, PathSpec)
        assert spec.match_file("foo.pyc")
        assert spec.match_file("build/output.txt")
        assert not spec.match_file("main.py")
