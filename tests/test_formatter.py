from io import StringIO

from repo_distiller.formatter import write_output, SEPARATOR


class TestWriteOutput:
    def test_writes_tree_and_files(self, tmp_path):
        (tmp_path / "hello.py").write_text("print('hi')")
        tree = ["root/", "└── hello.py"]
        files = [tmp_path / "hello.py"]

        out = StringIO()
        write_output(out, tree, files, tmp_path)
        result = out.getvalue()

        assert "root/" in result
        assert "└── hello.py" in result
        assert "FILE: hello.py" in result
        assert "print('hi')" in result
        assert SEPARATOR in result

    def test_handles_binary_file(self, tmp_path):
        (tmp_path / "img.bin").write_bytes(b"\x80\x81\x82")
        tree = ["root/"]
        files = [tmp_path / "img.bin"]

        out = StringIO()
        write_output(out, tree, files, tmp_path)
        result = out.getvalue()

        assert "[Skipped: binary or non-UTF8 file]" in result

    def test_empty_files_list(self, tmp_path):
        tree = ["root/"]
        out = StringIO()
        write_output(out, tree, [], tmp_path)
        result = out.getvalue()

        assert "root/" in result
        assert SEPARATOR not in result

    def test_multiple_files(self, tmp_path):
        (tmp_path / "a.py").write_text("a")
        (tmp_path / "b.py").write_text("b")
        tree = ["root/"]
        files = [tmp_path / "a.py", tmp_path / "b.py"]

        out = StringIO()
        write_output(out, tree, files, tmp_path)
        result = out.getvalue()

        assert "FILE: a.py" in result
        assert "FILE: b.py" in result
