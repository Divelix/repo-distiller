from pathlib import Path

from repo_distiller.config import IncludeConfig, ExcludeConfig, GitIgnoreStack
from repo_distiller.core import (
    rel,
    matches_any_prefix,
    is_default_excluded,
    is_excluded,
    is_included,
    file_allowed,
    collect_files,
    build_tree,
)


def _make_gitignore(tmp_path, patterns, subdir=None):
    """Helper to create a .gitignore and return a GitIgnoreStack."""
    target = tmp_path if subdir is None else tmp_path / subdir
    target.mkdir(parents=True, exist_ok=True)
    (target / ".gitignore").write_text("\n".join(patterns) + "\n")
    return GitIgnoreStack(tmp_path)


class TestRel:
    def test_basic(self):
        assert rel(Path("/a/b/c.py"), Path("/a")) == Path("b/c.py")


class TestMatchesAnyPrefix:
    def test_matches(self):
        assert matches_any_prefix(Path("src/main.py"), ["src/"])

    def test_no_match(self):
        assert not matches_any_prefix(Path("lib/utils.py"), ["src/"])

    def test_empty_prefixes(self):
        assert not matches_any_prefix(Path("anything"), [])


class TestIsDefaultExcluded:
    def test_excluded_dir(self):
        assert is_default_excluded(Path("__pycache__/foo.pyc"))
        assert is_default_excluded(Path("node_modules/pkg/index.js"))
        assert is_default_excluded(Path(".git/config"))

    def test_excluded_suffix(self):
        assert is_default_excluded(Path("my_package.egg-info/PKG-INFO"))

    def test_excluded_file(self):
        assert is_default_excluded(Path("uv.lock"))
        assert is_default_excluded(Path("LICENSE"))
        assert is_default_excluded(Path(".gitignore"))

    def test_allowed(self):
        assert not is_default_excluded(Path("src/main.py"))
        assert not is_default_excluded(Path("README.md"))


class TestIsExcluded:
    def test_default_excluded(self, tmp_path):
        f = tmp_path / "__pycache__" / "mod.pyc"
        f.parent.mkdir()
        f.touch()
        assert is_excluded(f, tmp_path, ExcludeConfig(), None)

    def test_gitignore_match(self, tmp_path):
        f = tmp_path / "output.log"
        f.touch()
        gi = _make_gitignore(tmp_path, ["*.log"])
        assert is_excluded(f, tmp_path, ExcludeConfig(), gi)

    def test_config_path_excluded(self, tmp_path):
        f = tmp_path / "vendor" / "lib.py"
        f.parent.mkdir()
        f.touch()
        assert is_excluded(f, tmp_path, ExcludeConfig(paths=["vendor/"]), None)

    def test_config_extension_excluded(self, tmp_path):
        f = tmp_path / "image.png"
        f.touch()
        assert is_excluded(f, tmp_path, ExcludeConfig(extensions=[".png"]), None)

    def test_not_excluded(self, tmp_path):
        f = tmp_path / "main.py"
        f.touch()
        assert not is_excluded(f, tmp_path, ExcludeConfig(), None)

    def test_no_default_excludes(self, tmp_path):
        f = tmp_path / "uv.lock"
        f.touch()
        cfg = ExcludeConfig(use_default_excludes=False)
        assert not is_excluded(f, tmp_path, cfg, None)

    def test_no_default_excludes_dir(self, tmp_path):
        f = tmp_path / "__pycache__" / "mod.pyc"
        f.parent.mkdir()
        f.touch()
        cfg = ExcludeConfig(use_default_excludes=False)
        assert not is_excluded(f, tmp_path, cfg, None)


class TestIsIncluded:
    def test_no_include_paths_includes_all(self, tmp_path):
        f = tmp_path / "anything.py"
        assert is_included(f, tmp_path, IncludeConfig())

    def test_matching_prefix(self, tmp_path):
        f = tmp_path / "src" / "app.py"
        assert is_included(f, tmp_path, IncludeConfig(paths=["src/"]))

    def test_non_matching_prefix(self, tmp_path):
        f = tmp_path / "tests" / "test.py"
        assert not is_included(f, tmp_path, IncludeConfig(paths=["src/"]))


class TestFileAllowed:
    def test_regular_file_allowed(self, tmp_path):
        f = tmp_path / "main.py"
        f.write_text("print('hi')")
        assert file_allowed(f, tmp_path, IncludeConfig(), ExcludeConfig(), None)

    def test_directory_not_allowed(self, tmp_path):
        d = tmp_path / "subdir"
        d.mkdir()
        assert not file_allowed(d, tmp_path, IncludeConfig(), ExcludeConfig(), None)

    def test_excluded_file_not_allowed(self, tmp_path):
        f = tmp_path / "uv.lock"
        f.write_text("lock content")
        assert not file_allowed(f, tmp_path, IncludeConfig(), ExcludeConfig(), None)

    def test_not_included_file_not_allowed(self, tmp_path):
        f = tmp_path / "other" / "file.py"
        f.parent.mkdir()
        f.write_text("x")
        assert not file_allowed(f, tmp_path, IncludeConfig(paths=["src/"]), ExcludeConfig(), None)

    def test_extension_filter(self, tmp_path):
        py = tmp_path / "app.py"
        py.write_text("x")
        txt = tmp_path / "notes.txt"
        txt.write_text("x")
        inc = IncludeConfig(extensions=[".py"])
        assert file_allowed(py, tmp_path, inc, ExcludeConfig(), None)
        assert not file_allowed(txt, tmp_path, inc, ExcludeConfig(), None)

    def test_file_too_large(self, tmp_path):
        f = tmp_path / "big.py"
        f.write_bytes(b"x" * (513 * 1024))
        assert not file_allowed(f, tmp_path, IncludeConfig(), ExcludeConfig(), None)

    def test_custom_size_limit(self, tmp_path):
        f = tmp_path / "medium.py"
        f.write_bytes(b"x" * (2 * 1024))
        inc_small = IncludeConfig(max_file_size_kb=1)
        inc_large = IncludeConfig(max_file_size_kb=3)
        assert not file_allowed(f, tmp_path, inc_small, ExcludeConfig(), None)
        assert file_allowed(f, tmp_path, inc_large, ExcludeConfig(), None)


class TestCollectFiles:
    def test_collects_and_sorts(self, tmp_path):
        (tmp_path / "b.py").write_text("b")
        (tmp_path / "a.py").write_text("a")
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "c.py").write_text("c")
        result = collect_files(tmp_path, IncludeConfig(), ExcludeConfig(), None)
        names = [f.name for f in result]
        assert names == ["a.py", "b.py", "c.py"]

    def test_excludes_default(self, tmp_path):
        (tmp_path / "ok.py").write_text("ok")
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "mod.pyc").write_text("cached")
        result = collect_files(tmp_path, IncludeConfig(), ExcludeConfig(), None)
        assert all("__pycache__" not in str(f) for f in result)

    def test_nested_gitignore(self, tmp_path):
        """Nested .gitignore in a subdirectory excludes files within it."""
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / ".gitignore").write_text("*.log\n")
        (sub / "app.py").write_text("x")
        (sub / "debug.log").write_text("x")
        (tmp_path / "root.log").write_text("x")

        # Root .gitignore required for GitIgnoreStack creation.
        (tmp_path / ".gitignore").write_text("")
        gi = GitIgnoreStack(tmp_path)

        result = collect_files(tmp_path, IncludeConfig(), ExcludeConfig(), gi)
        names = [f.name for f in result]
        assert "app.py" in names
        assert "debug.log" not in names
        # root.log is not matched by sub/.gitignore
        assert "root.log" in names


class TestBuildTree:
    def test_simple_tree(self, tmp_path):
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "main.py").write_text("x")
        (tmp_path / "README.md").write_text("x")
        lines = build_tree(tmp_path, ExcludeConfig(), None)
        assert lines[0] == f"{tmp_path.name}/"
        text = "\n".join(lines)
        assert "src" in text
        assert "main.py" in text
        assert "README.md" in text

    def test_excludes_default_dirs(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("x")
        (tmp_path / "app.py").write_text("x")
        lines = build_tree(tmp_path, ExcludeConfig(), None)
        text = "\n".join(lines)
        assert ".git" not in text
        assert "app.py" in text

    def test_nested_gitignore_in_tree(self, tmp_path):
        """Nested .gitignore excludes matching entries from the tree."""
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / ".gitignore").write_text("secret/\n")
        secret = sub / "secret"
        secret.mkdir()
        (secret / "key.pem").write_text("x")
        (sub / "visible.py").write_text("x")

        (tmp_path / ".gitignore").write_text("")
        gi = GitIgnoreStack(tmp_path)

        lines = build_tree(tmp_path, ExcludeConfig(), gi)
        text = "\n".join(lines)
        assert "visible.py" in text
        assert "secret" not in text
