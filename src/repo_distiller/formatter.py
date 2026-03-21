from io import TextIOBase
from pathlib import Path

SEPARATOR = "=" * 30


def write_output(out: TextIOBase, tree: list[str], files: list[Path], root: Path) -> None:
    """Write the distilled repository output to a text stream.

    Writes the ASCII directory tree followed by each file's contents,
    separated by header lines.

    Args:
        out: Writable text stream (file, stdout, StringIO, etc.).
        tree: Lines of the ASCII directory tree.
        files: Sorted list of absolute file paths to include.
        root: Repository root, used to compute relative paths.
    """
    out.write("\n".join(tree))
    out.write("\n\n")

    for f in files:
        r = f.relative_to(root)
        out.write(SEPARATOR + "\n")
        out.write(f"FILE: {r}\n")
        out.write(SEPARATOR + "\n")
        try:
            out.write(f.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            out.write("[Skipped: binary or non-UTF8 file]")
        out.write("\n\n")
