from pathlib import Path

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

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
    def _make_gitignore(self, patterns):
        return PathSpec.from_lines(GitWildMatchPattern, patterns)

    def test_default_excluded(self, tmp_path):
        f = tmp_path / "__pycache__" / "mod.pyc"
        f.parent.mkdir()
        f.touch()
        assert is_excluded(f, tmp_path, {}, None)

    def test_gitignore_match(self, tmp_path):
        f = tmp_path / "output.log"
        f.touch()
        gi = self._make_gitignore(["*.log"])
        assert is_excluded(f, tmp_path, {}, gi)

    def test_config_path_excluded(self, tmp_path):
        f = tmp_path / "vendor" / "lib.py"
        f.parent.mkdir()
        f.touch()
        assert is_excluded(f, tmp_path, {"paths": ["vendor/"]}, None)

    def test_config_extension_excluded(self, tmp_path):
        f = tmp_path / "image.png"
        f.touch()
        assert is_excluded(f, tmp_path, {"extensions": [".png"]}, None)

    def test_not_excluded(self, tmp_path):
        f = tmp_path / "main.py"
        f.touch()
        assert not is_excluded(f, tmp_path, {}, None)


class TestIsIncluded:
    def test_no_include_paths_includes_all(self, tmp_path):
        f = tmp_path / "anything.py"
        assert is_included(f, tmp_path, {})

    def test_matching_prefix(self, tmp_path):
        f = tmp_path / "src" / "app.py"
        assert is_included(f, tmp_path, {"paths": ["src/"]})

    def test_non_matching_prefix(self, tmp_path):
        f = tmp_path / "tests" / "test.py"
        assert not is_included(f, tmp_path, {"paths": ["src/"]})


class TestFileAllowed:
    def test_regular_file_allowed(self, tmp_path):
        f = tmp_path / "main.py"
        f.write_text("print('hi')")
        assert file_allowed(f, tmp_path, {}, {}, None)

    def test_directory_not_allowed(self, tmp_path):
        d = tmp_path / "subdir"
        d.mkdir()
        assert not file_allowed(d, tmp_path, {}, {}, None)

    def test_excluded_file_not_allowed(self, tmp_path):
        f = tmp_path / "uv.lock"
        f.write_text("lock content")
        assert not file_allowed(f, tmp_path, {}, {}, None)

    def test_not_included_file_not_allowed(self, tmp_path):
        f = tmp_path / "other" / "file.py"
        f.parent.mkdir()
        f.write_text("x")
        assert not file_allowed(f, tmp_path, {"paths": ["src/"]}, {}, None)

    def test_extension_filter(self, tmp_path):
        py = tmp_path / "app.py"
        py.write_text("x")
        txt = tmp_path / "notes.txt"
        txt.write_text("x")
        inc = {"extensions": [".py"]}
        assert file_allowed(py, tmp_path, inc, {}, None)
        assert not file_allowed(txt, tmp_path, inc, {}, None)

    def test_file_too_large(self, tmp_path):
        f = tmp_path / "big.py"
        f.write_bytes(b"x" * (513 * 1024))
        assert not file_allowed(f, tmp_path, {}, {}, None)

    def test_custom_size_limit(self, tmp_path):
        f = tmp_path / "medium.py"
        f.write_bytes(b"x" * (2 * 1024))
        inc_small = {"limits": {"max_file_size_kb": 1}}
        inc_large = {"limits": {"max_file_size_kb": 3}}
        assert not file_allowed(f, tmp_path, inc_small, {}, None)
        assert file_allowed(f, tmp_path, inc_large, {}, None)


class TestCollectFiles:
    def test_collects_and_sorts(self, tmp_path):
        (tmp_path / "b.py").write_text("b")
        (tmp_path / "a.py").write_text("a")
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "c.py").write_text("c")
        result = collect_files(tmp_path, {}, {}, None)
        names = [f.name for f in result]
        assert names == ["a.py", "b.py", "c.py"]

    def test_excludes_default(self, tmp_path):
        (tmp_path / "ok.py").write_text("ok")
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "mod.pyc").write_text("cached")
        result = collect_files(tmp_path, {}, {}, None)
        assert all("__pycache__" not in str(f) for f in result)


class TestBuildTree:
    def test_simple_tree(self, tmp_path):
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "main.py").write_text("x")
        (tmp_path / "README.md").write_text("x")
        lines = build_tree(tmp_path, {}, None)
        assert lines[0] == f"{tmp_path.name}/"
        text = "\n".join(lines)
        assert "src" in text
        assert "main.py" in text
        assert "README.md" in text

    def test_excludes_default_dirs(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("x")
        (tmp_path / "app.py").write_text("x")
        lines = build_tree(tmp_path, {}, None)
        text = "\n".join(lines)
        assert ".git" not in text
        assert "app.py" in text
