# Neckbeard

[![CI](https://github.com/jzlosman/neckbeard/actions/workflows/ci.yml/badge.svg)](https://github.com/jzlosman/neckbeard/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Coverage gate](https://img.shields.io/badge/coverage-%E2%89%A590%25-21A36A)](https://github.com/jzlosman/neckbeard/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-172033)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-portable-D9545D)](skills/neckbeard/SKILL.md)

**A Git diff scope fence for coding agents.** Neckbeard reads a
repository-owned `.neckbeard.toml`, measures the complete working-tree diff,
and returns a deterministic pass, failure, or operational error.

Ponytail tells an agent to prefer the smallest correct change. Neckbeard
independently checks whether the resulting diff remains inside a repository's
mechanical path and size budget. It does not judge correctness, quality,
security, or semantic minimality.

> Neckbeard is **not a security boundary or sandbox**. It observes changes
> after they exist and cannot prevent reads, commands, external side effects,
> or policy editing by a process with repository write access. Use permissions,
> isolated workspaces, tests, and review for those controls.

## Install from source

Neckbeard is not published to PyPI. Clone a source checkout, then install it
with Python 3.11+ and Git available:

```sh
git clone <your-clone-url>
cd neckbeard
uv tool install .
# or: python -m pip install .
neckbeard --version
```

For development tools, install `requirements-dev.txt` in an isolated
environment (for example, `uv venv && uv pip install -r requirements-dev.txt`).

## Use

Commit a policy at the Git repository root:

```toml
[scope]
allow_dependency_changes = false
allow = ["src/**", "tests/**", "README.md"]
deny = ["src/generated/**", "secrets/**"]
max_files = 8
max_additions = 400
max_deletions = 150
```

All fields except `allow_dependency_changes` are optional. A non-empty `allow`
list requires every changed path to match; `deny` always wins. Patterns match
the full repository-relative POSIX path: `*` excludes `/`, `?` is one
non-`/` character, and `**` may include `/`. Leading `/`, backslashes, and `.`
or `..` path segments are invalid. These examples are covered by the CLI
contract tests.

Run against the current `HEAD` by default, or name a committed comparison
revision:

```sh
neckbeard check
neckbeard check --base main
neckbeard check --json
```

Text output is concise:

```text
PASS base=<commit> files=2 additions=12 deletions=3
FAIL path-denied secrets/token.txt; max-files
ERROR policy-error: missing .neckbeard.toml
```

`--json` writes one stable JSON object to stdout, including `base`, `summary`,
`changed_paths`, `violations`, and `error`; it is suitable for CI or other
tooling. Exit codes are exact:

| Code | Meaning |
| ---: | --- |
| 0 | Policy passes. |
| 1 | Policy violation (`FAIL`). |
| 2 | Invocation, repository, policy, base, or Git error (`ERROR`). |

The checker includes staged, unstaged, and non-ignored untracked files. It
disables rename detection (a rename is a deletion plus an addition) and fails
closed for binary or unmeasurable files.

### Dependency-sensitive filenames

Changing any of these filenames anywhere in the tree requires
`allow_dependency_changes = true`; ordinary path rules and limits still apply.
Neckbeard does not parse their contents or infer ecosystems.

`pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `Pipfile`,
`Pipfile.lock`, `poetry.lock`, `uv.lock`, `package.json`, `package-lock.json`,
`npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.toml`,
`Cargo.lock`, `go.mod`, `go.sum`.

See [configuration](docs/configuration.md) for the complete policy reference.

## Agent skill

The canonical portable skill is [`skills/neckbeard/`](skills/neckbeard/).
Install or copy that directory using your host's documented skill mechanism:

- Claude Code: project or user `.claude/skills/neckbeard/`
- Codex: `$CODEX_HOME/skills/neckbeard/` (typically `~/.codex/skills/`)
- Gemini CLI: `.gemini/skills/neckbeard/`
- Pi: `.pi/skills/neckbeard/`
- skills.sh: import the canonical directory with its documented skills workflow

Hosts differ in discovery and invocation behavior. Installing this skill does
**not** automatically enforce Neckbeard: ensure `neckbeard` is installed and
instruct CI, contributors, or agents to run `neckbeard check`. The CLI and the
repository policy are authoritative; the skill is workflow guidance, not a
replacement for tests or review. See [agent-skill guidance](docs/agent-skill.md).

## Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md),
and [security policy](SECURITY.md). General help belongs in
[SUPPORT.md](SUPPORT.md).
