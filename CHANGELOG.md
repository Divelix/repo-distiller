# Changelog

## 0.3.0

- Use typed dataclasses (`IncludeConfig`, `ExcludeConfig`) instead of raw dicts for configuration
- Short-circuit directory traversal via `os.walk` pruning to skip excluded dirs early
- Add `--no-default-excludes` flag to disable built-in exclusion rules
- Support nested `.gitignore` files (patterns scoped to their directory)
- Extract output formatting into a dedicated `formatter` module
- Add stdout support (`--output -`)
- Add `--dry-run` / `--list` mode to preview included files without writing output
- Add `--verbose` flag for progress feedback on stderr

## 0.2.0

- Exclude folders from summary (.git, lockfiles, etc.)
