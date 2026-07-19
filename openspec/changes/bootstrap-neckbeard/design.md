## Context

Neckbeard is a local, agent-agnostic Git diff scope fence. It complements Ponytail: Ponytail recommends the smallest correct solution, while Neckbeard evaluates whether the final working-tree change remained inside a repository-owned mechanical budget. The check must work without a model SDK, a network connection, or a platform-specific agent adapter.

The project ships two coordinated pieces: a Python 3.11+ CLI with no runtime dependencies, and one portable Agent Skills directory at `skills/neckbeard/`. The CLI is authoritative; the skill only teaches an agent when to invoke it and how to respond to a failure.

## Goals / Non-Goals

**Goals:**
- Produce the same verdict for the same Git worktree, base revision, and committed policy.
- Enforce repository-relative allow/deny globs plus changed-file, addition, deletion, and dependency-file budgets.
- Include staged, unstaged, and non-ignored untracked changes so the fence cannot be bypassed by leaving work untracked.
- Provide concise human output and a stable JSON contract suitable for CI.
- Keep the core runnable with Python and Git only; test it against real temporary Git repositories.

**Non-Goals:**
- Sandboxing agents; preventing reads, commands, temporary edits, or external side effects.
- Assessing correctness, quality, security, test quality, or whether a change is semantically minimal.
- Parsing package manifests or lockfiles, auto-detecting a repository's ecosystem, fetching remote refs, or sending telemetry.
- Shipping per-agent prompt forks, model adapters, or a policy language beyond simple path/budget rules.

## Decisions

### Python standard library CLI

Neckbeard SHALL require Python 3.11+ and Git. Python 3.11 supplies `tomllib`, allowing a readable committed TOML policy without a parser dependency. Git is invoked with argument arrays rather than a shell. A Git SDK, dependency framework, and runtime package tree are rejected because they add surface area to a mechanical checker.

### Repository-owned `.neckbeard.toml`

The checker discovers the Git top-level directory and loads exactly `<root>/.neckbeard.toml`. The `[scope]` table holds optional `allow`, `deny`, `max_files`, `max_additions`, and `max_deletions` values plus required `allow_dependency_changes`. Missing, malformed, or semantically invalid policy is an error, not an implicit permissive fallback. This preserves identical local and CI behavior.

A non-empty allow list constrains changed paths; a path matching any deny glob is always rejected. Limits are non-negative and optional. The scope checker normalizes paths to repository-relative POSIX form and rejects traversal-like policy entries instead of trying to repair them. Its glob grammar is intentionally small: `*` matches zero or more non-slash characters, `?` matches exactly one non-slash character, `**` matches zero or more characters including slashes, and every other character is literal. Patterns are full-path matches; leading slashes, backslashes, and `.`/`..` path segments are invalid. Dotfiles are ordinary path characters.

### Deterministic Git facts

`neckbeard check` compares the working tree with `--base REV`, defaulting to `HEAD`. Only a missing default `HEAD` falls back to Git's empty tree; an explicitly invalid base is an error. The checker includes tracked staged and unstaged changes plus non-ignored untracked files, does not stage or alter anything, disables rename detection, and treats a rename as a deletion plus an addition. This avoids heuristic rename thresholds and ensures both paths are checked.

Git numstat provides tracked line counts. Neckbeard derives additions for untracked text files locally; a binary or otherwise unmeasurable file is a fail-closed policy violation rather than silently counting as zero.

### Fixed sensitive dependency-path catalog

V1 checks a documented finite list of common manifest and lockfile paths by filename only. It never parses their contents. Any changed sensitive path requires `allow_dependency_changes = true`; policy path rules and normal budgets still apply. A later format can add configurable catalog extensions only with a new spec.

### One verdict model, two renderers

The internal verdict contains stable base, metrics, changed paths, violations, and an optional error. Changed paths are ordered bytewise by normalized path; violations are ordered by normalized path bytes and then code. The default renderer starts with `PASS`, `FAIL`, or `ERROR`; `--json` emits one deterministic JSON object on stdout. Exit 0 means compliant, 1 means policy violation, and 2 means invocation, policy, repository, or Git error. This makes CI consume the same facts a human sees.

### Canonical portable skill and release posture

`skills/neckbeard/SKILL.md` is the only canonical instruction source, following the Agent Skills standard and avoiding host-specific fields. README installation guidance may mention Claude Code, Codex, Gemini CLI, Pi, and skills.sh, but no adapter is authoritative. The repository follows the proven `skills/`, `src/`, `tests/`, `docs/`, `assets/`, and GitHub Actions layout used by multi-agent skill projects such as Vercel Skills and Superpowers.

Tests use `unittest` plus temporary real Git repositories. GitHub Actions runs supported Python versions, tests the installed package, checks formatting/linting, builds a wheel/sdist, and enforces a coverage threshold. Generated PNG artwork is supplementary; an accessible hand-authored SVG is canonical.

## Risks / Trade-offs

- **[Scope checks are post-change, not prevention]** → Documentation MUST state that the CLI is not a sandbox and teams need isolated workspaces/permissions for stronger controls.
- **[Line counts and binary files differ]** → Treat unmeasurable files as explicit violations in v1; do not undercount them.
- **[A finite dependency catalog omits ecosystems]** → Document the catalog and require a deliberate future spec change before expanding it.
- **[Strict budgets can reject legitimate broad work]** → Require maintainers to deliberately widen committed policy or split the work; do not add hidden auto-exceptions.
- **[Platform skill discovery varies]** → Keep the standard `skills/neckbeard/` package canonical and describe installation rather than claiming interception by every host.
