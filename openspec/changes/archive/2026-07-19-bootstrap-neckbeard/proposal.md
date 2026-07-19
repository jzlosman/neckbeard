## Why

Coding agents need a repository-enforced boundary on how much they change. Ponytail recommends minimal solutions; Neckbeard independently measures a Git diff and fails work that exceeds the repository's declared budget.

## What Changes

- Introduce Neckbeard: an MIT-licensed Python CLI with zero runtime dependencies and a portable Agent Skills package.
- Read repository-owned policy for allowed and denied path globs, maximum changed files, additions, and deletions.
- Detect dependency manifest and lockfile changes and require explicit policy approval for them.
- Evaluate a target Git diff and emit a human-readable verdict or JSON suitable for CI.
- Keep scope to mechanical diff-budget enforcement; exclude sandboxing, code-quality review, TDD workflows, and skill security scanning.

## Capabilities

### New Capabilities
- `diff-budget-policy`: Define repository-owned path rules, change limits, and dependency/lockfile approval rules.
- `git-diff-budget-check`: Calculate changed files, additions, deletions, and path-rule violations from a Git diff.
- `dependency-change-gate`: Identify dependency and lockfile changes and reject those not explicitly approved by policy.
- `budget-verdict-output`: Provide consistent human-readable and JSON pass/fail results for local agents and CI.
- `portable-agent-skill`: Provide one host-neutral Agent Skills workflow that invokes the mechanical checker without duplicating policy or bypassing failures.

### Modified Capabilities
- None.

## Impact

- Adds a standalone Python CLI and portable skills package; no runtime dependency tree is introduced.
- Repositories opt in by committing a Neckbeard policy and invoking the CLI in agent instructions or CI.
- Policy violations block or flag oversized or disallowed diffs without judging code correctness or replacing Ponytail guidance.
