## ADDED Requirements

### Requirement: Classify a documented finite set of sensitive dependency paths
The system SHALL classify a changed path as dependency-sensitive only when its final path component is one of: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `Pipfile`, `Pipfile.lock`, `poetry.lock`, `uv.lock`, `package.json`, `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.toml`, `Cargo.lock`, `go.mod`, or `go.sum`. It SHALL use the path only and SHALL NOT parse manifest, lockfile, or dependency contents.

#### Scenario: Classify a nested listed lockfile
- **WHEN** the evaluated diff changes `services/api/poetry.lock`
- **THEN** the checker marks that path as dependency-sensitive without reading its contents

#### Scenario: Ignore dependency-like prose
- **WHEN** the evaluated diff changes `docs/dependencies.md` and no listed sensitive path
- **THEN** the checker does not mark that file as dependency-sensitive

### Requirement: Require explicit policy approval for sensitive changes
The system SHALL produce a dependency-change violation for every dependency-sensitive changed path unless `[scope] allow_dependency_changes` is exactly `true`. Normal path rules and file/line budgets SHALL still apply to approved dependency-sensitive paths.

#### Scenario: Reject an unapproved sensitive change
- **WHEN** the evaluated diff changes `package.json` and `allow_dependency_changes = false`
- **THEN** the checker reports a dependency-change violation naming `package.json`

#### Scenario: Permit an explicitly approved sensitive change
- **WHEN** the evaluated diff changes `go.sum` and `allow_dependency_changes = true`
- **THEN** the checker produces no dependency-change violation for `go.sum`

#### Scenario: Report multiple unapproved sensitive paths deterministically
- **WHEN** the evaluated diff changes `yarn.lock` and `package.json` and `allow_dependency_changes = false`
- **THEN** the checker reports both dependency-change violations in deterministic path order
