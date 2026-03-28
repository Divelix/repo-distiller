from collections import Counter
from io import TextIOBase
from pathlib import Path

from rich.console import Console
from rich.table import Table

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


def print_repo_stats(files: list[Path], repo_name: str) -> None:
    """Print a rich table with file and line counts grouped by extension.

    Args:
        files: List of absolute file paths to analyse.
        repo_name: Repository name used in the table title.
    """
    lines_by_ext: Counter[str] = Counter()
    files_by_ext: Counter[str] = Counter()

    for f in files:
        ext = f.suffix or "(no ext)"
        files_by_ext[ext] += 1
        try:
            line_count = f.read_text(encoding="utf-8", errors="replace").count("\n")
        except OSError:
            line_count = 0
        lines_by_ext[ext] += line_count

    console = Console()
    table = Table(title=f"Repository stats: {repo_name}")
    table.add_column("Extension", style="cyan")
    table.add_column("Files", justify="right", style="green")
    table.add_column("Lines", justify="right", style="yellow")
    table.add_column("% Lines", justify="right", style="magenta")

    total_lines = sum(lines_by_ext.values())
    total_files = sum(files_by_ext.values())

    for ext, lines in lines_by_ext.most_common():
        pct = (lines / total_lines * 100) if total_lines else 0
        table.add_row(ext, str(files_by_ext[ext]), f"{lines:,}", f"{pct:.1f}%")

    table.add_section()
    table.add_row(
        "Total",
        str(total_files),
        f"{total_lines:,}",
        "100.0%",
        style="bold",
    )

    console.print(table)
