# Changelog

## 0.4.0

- Add `info` command to show repo statistics
- Change `-e` / `--exclude` to accept individual paths (repeatable), e.g. `-e a.txt -e b.txt`
- Move YAML exclude config file to `--exclude-file` flag

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
