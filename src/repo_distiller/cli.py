import typer
from pathlib import Path

from .config import load_yaml, load_gitignore
from .core import build_tree, collect_files

app = typer.Typer(help="Distill a repository into a single prompt-friendly file")


@app.command("distill")
def distill(
    repo: Path = typer.Argument(..., exists=True, file_okay=False),
    output: Path = typer.Option(..., "-o", "--output"),
    include: Path | None = typer.Option(None, "-i", "--include"),
    exclude: Path | None = typer.Option(None, "-e", "--exclude"),
):
    """
    Convert a repository into a single text file.
    """
    repo = repo.resolve()
    output = output.resolve()

    include_cfg = load_yaml(include)
    exclude_cfg = load_yaml(exclude)
    gitignore = None if exclude else load_gitignore(repo)

    tree = build_tree(repo, exclude_cfg, gitignore)
    files = collect_files(repo, include_cfg, exclude_cfg, gitignore)

    with open(output, "w", encoding="utf-8") as out:
        out.write("\n".join(tree))
        out.write("\n\n")

        for f in files:
            r = f.relative_to(repo)
            out.write("=" * 30 + "\n")
            out.write(f"FILE: {r}\n")
            out.write("=" * 30 + "\n")
            try:
                out.write(f.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                out.write("[Skipped: binary or non-UTF8 file]")
            out.write("\n\n")

    typer.echo(f"Prompt written to {output}")
