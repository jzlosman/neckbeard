# Configuration

Neckbeard loads exactly `<Git-root>/.neckbeard.toml`. The file must be a regular
file (not a symlink) with a `[scope]` table and the required boolean
`allow_dependency_changes`.

```toml
[scope]
allow_dependency_changes = false
allow = ["src/**", "tests/**"]
deny = ["src/generated/**"]
max_files = 10
max_additions = 500
max_deletions = 200
```

## Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `allow_dependency_changes` | yes | Boolean approval for changed dependency-sensitive filenames. |
| `allow` | no | Array of full-path glob strings. If non-empty, every changed path must match one. |
| `deny` | no | Array of full-path glob strings. Any match fails, even if `allow` matches. |
| `max_files` | no | Non-negative integer cap on changed paths. |
| `max_additions` | no | Non-negative integer cap on added text lines. |
| `max_deletions` | no | Non-negative integer cap on deleted text lines. |

Patterns are repository-relative POSIX paths. `*` matches zero or more
non-slash characters, `?` one non-slash character, and `**` zero or more
characters including slashes. A pattern matches the whole path. Dotfiles are
ordinary paths. Leading slashes, backslashes, and `.` or `..` path segments
are rejected rather than normalized.

## What is measured

`neckbeard check` compares the complete working tree with `HEAD`, including
staged, unstaged, and non-ignored untracked files. `--base REV` chooses a
specific committed base. An unborn repository using the default base compares
against Git's empty tree; an invalid explicit base is an error.

Renames are deliberately counted as a deletion plus an addition. Git numstat
measures tracked text changes; untracked text files are counted locally.
Binary, symlinked, or otherwise unmeasurable files produce an explicit
`unmeasurable-file` violation rather than being silently undercounted.

## Dependency-sensitive catalog

A changed path whose basename is one of the following requires
`allow_dependency_changes = true`:

- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`
- `Pipfile`, `Pipfile.lock`, `poetry.lock`, `uv.lock`
- `package.json`, `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`,
  `pnpm-lock.yaml`
- `Cargo.toml`, `Cargo.lock`, `go.mod`, `go.sum`

This fixed v1 catalog is filename-only. Neckbeard does not parse manifests,
auto-detect package ecosystems, or make exceptions. Enabling approval does not
disable path rules or limits.

## Results

A policy pass exits 0, a policy violation exits 1, and an invocation, policy,
repository, base, or Git error exits 2. Use `neckbeard check --json` for the
single-object machine-readable result. Neckbeard is a post-change mechanical
check, not a sandbox or a substitute for tests, security controls, or review.
