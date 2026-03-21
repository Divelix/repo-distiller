import sys

import typer
from pathlib import Path

from .config import load_include_config, load_exclude_config, load_gitignore
from .core import build_tree, collect_files
from .formatter import write_output

app = typer.Typer(help="Distill a repository into a single prompt-friendly file")


def _log(message: str, verbose: bool) -> None:
    """Print a status message to stderr if verbose mode is enabled.

    Args:
        message: The message to print.
        verbose: Whether verbose output is enabled.
    """
    if verbose:
        typer.echo(message, err=True)


@app.command("distill")
def distill(
    repo: Path = typer.Argument(..., exists=True, file_okay=False),
    output: str = typer.Option(None, "-o", "--output",
                               help="Output file path, or '-' for stdout."),
    include: Path | None = typer.Option(None, "-i", "--include"),
    exclude: Path | None = typer.Option(None, "-e", "--exclude"),
    no_default_excludes: bool = typer.Option(
        False, "--no-default-excludes",
        help="Disable built-in exclusion rules for common dirs and files.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "--list",
        help="List files that would be included without writing output.",
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose",
        help="Show progress information on stderr.",
    ),
):
    """Convert a repository into a single text file for LLM prompting.

    Builds an ASCII directory tree and concatenates file contents, respecting
    include/exclude configuration and .gitignore patterns.

    Args:
        repo: Path to the repository root directory.
        output: Output file path, or '-' to write to stdout.
        include: Optional path to a YAML file specifying include filters.
        exclude: Optional path to a YAML file specifying exclude filters.
            When provided, .gitignore patterns are not loaded.
        no_default_excludes: If True, disable built-in exclusion rules.
        dry_run: If True, list matching files and exit without writing output.
        verbose: If True, print progress information to stderr.
    """
    repo = repo.resolve()

    include_cfg = load_include_config(include)
    exclude_cfg = load_exclude_config(exclude)
    if no_default_excludes:
        exclude_cfg.use_default_excludes = False
    gitignore = None if exclude else load_gitignore(repo)

    _log(f"Scanning {repo} ...", verbose)
    files = collect_files(repo, include_cfg, exclude_cfg, gitignore)
    _log(f"Found {len(files)} file(s).", verbose)

    if dry_run:
        for f in files:
            typer.echo(f.relative_to(repo))
        typer.echo(f"\n{len(files)} file(s) would be included.")
        return

    if not output:
        typer.echo("Error: --output is required when not using --dry-run.", err=True)
        raise typer.Exit(code=1)

    _log("Building directory tree ...", verbose)
    tree = build_tree(repo, exclude_cfg, gitignore)

    _log("Writing output ...", verbose)
    if output == "-":
        write_output(sys.stdout, tree, files, repo)
    else:
        output_path = Path(output).resolve()
        with open(output_path, "w", encoding="utf-8") as out:
            write_output(out, tree, files, repo)
        typer.echo(f"Prompt written to {output_path}")
