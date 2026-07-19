# budget-verdict-output Specification

## Purpose
TBD - created by archiving change bootstrap-neckbeard. Update Purpose after archive.
## Requirements
### Requirement: Emit concise human-readable verdicts
The system SHALL emit a concise default text verdict to standard output. A compliant check SHALL begin with `PASS`; a policy-violation check SHALL begin with `FAIL`; and an invocation, policy, repository, or Git error SHALL begin with `ERROR`. Violations and errors SHALL include a stable code and affected path when one exists.

#### Scenario: Render a passing text verdict
- **WHEN** evaluation finds no policy violations
- **THEN** standard output begins with `PASS` and the process exits with status 0

#### Scenario: Render a failed text verdict
- **WHEN** evaluation finds a denied changed path
- **THEN** standard output begins with `FAIL`, identifies the stable violation code and path, and the process exits with status 1

### Requirement: Emit stable structured JSON verdicts
When invoked with `--json`, the system SHALL emit one JSON object to standard output with top-level fields in this order: `version`, `verdict`, `exit_code`, `base`, `summary`, `changed_paths`, `violations`, and `error`. `version` SHALL be 1. `verdict` SHALL be `pass`, `violation`, or `error`. `summary` SHALL contain integer `changed_files`, `additions`, and `deletions`. Each violation SHALL contain `code`, `path`, and `message`. `error` SHALL be null or contain `code` and `message`. Arrays SHALL be deterministically ordered.

#### Scenario: Render a passing JSON verdict
- **WHEN** JSON mode evaluates a compliant diff
- **THEN** it emits `verdict` as `pass`, `exit_code` as 0, an empty `violations` array, and `error` as null

#### Scenario: Render ordered JSON violations
- **WHEN** JSON mode evaluates dependency and denied-path violations for different paths
- **THEN** it emits a `violation` verdict with violations ordered by normalized path bytes and then violation code

#### Scenario: Render a JSON policy error
- **WHEN** JSON mode encounters an invalid policy
- **THEN** it emits an `error` verdict with exit code 2 and a structured error object

### Requirement: Use fixed exit-status classes
The system SHALL exit 0 only for a compliant evaluation, 1 only for one or more policy violations, and 2 for unsupported invocation, invalid policy, repository, or Git errors. It SHALL not convert an operational error into a policy violation.

#### Scenario: Distinguish invalid invocation from a policy violation
- **WHEN** the CLI is invoked with an unsupported option
- **THEN** it reports an error verdict and exits with status 2

