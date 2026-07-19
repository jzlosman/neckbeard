## 1. Contract tests and minimal project foundation

- [ ] 1.1 Create the Python 3.11 package, `unittest` test harness, console entry point, and zero-runtime-dependency packaging metadata.
- [ ] 1.2 Write failing black-box CLI contract tests for `check`, `--base`, `--json`, text prefixes, deterministic JSON field order, and exit codes 0/1/2.
- [ ] 1.3 Write failing policy tests for required TOML fields, invalid policies, normalized POSIX paths, and the specified `*`, `?`, and `**` full-path glob semantics.
- [ ] 1.4 Write failing temporary-real-Git tests for explicit and default bases, unborn repositories, staged and unstaged changes, untracked non-ignored files, deletions, renames as delete-plus-add, ordering, and binary/unmeasurable failures.
- [ ] 1.5 Write failing dependency-gate tests for every documented sensitive filename, nested paths, approval, and deterministic multiple violations.

## 2. Checker implementation

- [ ] 2.1 Implement strict `.neckbeard.toml` loading and validation, including non-negative budgets and traversal-like glob rejection.
- [ ] 2.2 Implement the specified repository-relative glob matcher and allow/deny/budget evaluation, with deny taking precedence.
- [ ] 2.3 Collect complete facts from real Git without mutation: selected base (or empty tree for unborn `HEAD`), tracked staged/unstaged changes with rename detection disabled, and non-ignored untracked files.
- [ ] 2.4 Measure text additions/deletions, count untracked text lines, and emit explicit violations for binary or unmeasurable files.
- [ ] 2.5 Apply the fixed dependency-path catalog and require `allow_dependency_changes = true` while retaining all ordinary path and budget checks.
- [ ] 2.6 Implement one deterministic verdict model and its concise text and single-object JSON renderers, including ordered paths/violations and operational-error handling.
- [ ] 2.7 Make the contract tests pass and add only focused regressions discovered during implementation.

## 3. Portable skill and project materials

- [ ] 3.1 Add the sole canonical `skills/neckbeard/SKILL.md` with standard `name`/trigger-only `description`, CLI-authoritative workflow, failure stop/report behavior, and no host-specific instructions or duplicate policy.
- [ ] 3.2 Pressure-test the skill with a fresh agent in a red scenario: a failing scope check must stop work and report the exact violations without editing policy or bypassing the CLI.
- [ ] 3.3 Pressure-test the skill with a fresh agent in a green scenario: a passing scope check must be invoked and reported alongside normal verification.
- [ ] 3.4 Create an accessible hand-authored canonical SVG and generate the supplementary PNG; document that the SVG is canonical.
- [ ] 3.5 Add public README and docs covering installation, policy schema/globs, fixed dependency catalog, CLI text/JSON/CI usage, limits, and the non-sandbox boundary.
- [ ] 3.6 Add MIT LICENSE and minimal public community files (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and support guidance).

## 4. Automation, review, and release

- [ ] 4.1 Add CI for supported Python versions that installs the built package, runs tests, lint/format checks, coverage threshold, and wheel/sdist build.
- [ ] 4.2 Independently review the CLI/policy implementation against every OpenSpec requirement and resolve findings.
- [ ] 4.3 Independently review the portable skill, documentation, and release artifacts for host-neutrality, accuracy, accessibility, and scope.
- [ ] 4.4 Run final clean-worktree verification: full tests, lint/format, coverage, package build, representative text/JSON CLI checks, and both fresh-agent pressure scenarios.
- [ ] 4.5 Inspect the final diff and status, then create a local Git commit containing the validated change.
- [ ] 4.6 Only after explicit user confirmation and GitHub repository/release availability checks, create the public GitHub release with the built artifacts and release notes.
