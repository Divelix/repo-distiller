from pathlib import Path

from repo_distiller.config import (
    IncludeConfig,
    ExcludeConfig,
    GitIgnoreStack,
    _load_yaml,
    load_include_config,
    load_exclude_config,
    load_gitignore,
)


class TestLoadYaml:
    def test_none_returns_empty_dict(self):
        assert _load_yaml(None) == {}

    def test_valid_yaml(self, tmp_path):
        f = tmp_path / "cfg.yaml"
        f.write_text("paths:\n  - src/\n  - lib/\n")
        result = _load_yaml(f)
        assert result == {"paths": ["src/", "lib/"]}

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        assert _load_yaml(f) == {}


class TestLoadIncludeConfig:
    def test_none_returns_defaults(self):
        cfg = load_include_config(None)
        assert cfg == IncludeConfig()
        assert cfg.max_file_size_kb == 512

    def test_full_config(self, tmp_path):
        f = tmp_path / "inc.yaml"
        f.write_text(
            "paths:\n  - src/\nextensions:\n  - .py\n"
            "limits:\n  max_file_size_kb: 256\n"
        )
        cfg = load_include_config(f)
        assert cfg.paths == ["src/"]
        assert cfg.extensions == [".py"]
        assert cfg.max_file_size_kb == 256

    def test_partial_config(self, tmp_path):
        f = tmp_path / "inc.yaml"
        f.write_text("paths:\n  - lib/\n")
        cfg = load_include_config(f)
        assert cfg.paths == ["lib/"]
        assert cfg.extensions == []
        assert cfg.max_file_size_kb == 512


class TestLoadExcludeConfig:
    def test_none_returns_defaults(self):
        cfg = load_exclude_config(None)
        assert cfg == ExcludeConfig()

    def test_full_config(self, tmp_path):
        f = tmp_path / "exc.yaml"
        f.write_text("paths:\n  - vendor/\nextensions:\n  - .png\n")
        cfg = load_exclude_config(f)
        assert cfg.paths == ["vendor/"]
        assert cfg.extensions == [".png"]


class TestLoadGitignore:
    def test_no_gitignore_returns_none(self, tmp_path):
        assert load_gitignore(tmp_path) is None

    def test_returns_gitignore_stack(self, tmp_path):
        gi = tmp_path / ".gitignore"
        gi.write_text("*.pyc\nbuild/\n")
        stack = load_gitignore(tmp_path)
        assert isinstance(stack, GitIgnoreStack)
        assert stack.match_file(tmp_path / "foo.pyc")
        assert stack.match_file(tmp_path / "build" / "output.txt")
        assert not stack.match_file(tmp_path / "main.py")


class TestGitIgnoreStack:
    def test_root_patterns(self, tmp_path):
        (tmp_path / ".gitignore").write_text("*.log\n")
        stack = GitIgnoreStack(tmp_path)
        assert stack.match_file(tmp_path / "error.log")
        assert not stack.match_file(tmp_path / "app.py")

    def test_nested_patterns(self, tmp_path):
        (tmp_path / ".gitignore").write_text("")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / ".gitignore").write_text("*.tmp\n")

        stack = GitIgnoreStack(tmp_path)
        stack.push_dir(sub)

        assert stack.match_file(sub / "data.tmp")
        # Root files don't match sub's .gitignore
        assert not stack.match_file(tmp_path / "data.tmp")

    def test_push_dir_no_gitignore(self, tmp_path):
        (tmp_path / ".gitignore").write_text("*.log\n")
        sub = tmp_path / "sub"
        sub.mkdir()

        stack = GitIgnoreStack(tmp_path)
        stack.push_dir(sub)  # no .gitignore here, should not error
        assert stack.match_file(tmp_path / "error.log")
