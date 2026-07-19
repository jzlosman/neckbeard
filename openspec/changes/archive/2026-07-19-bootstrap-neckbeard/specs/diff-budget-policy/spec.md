## ADDED Requirements

### Requirement: Load a repository-owned scope policy
After resolving the comparison base, the system SHALL load `.neckbeard.toml` from that base commit's Git tree, not `<repository-root>/.neckbeard.toml` in the mutable working tree. The base entry SHALL be a regular Git blob with mode `100644` or `100755`; a missing, symlinked, or otherwise nonregular entry is a policy error. Only the default unborn-`HEAD` empty-tree fallback SHALL load `<repository-root>/.neckbeard.toml`; that fallback file SHALL be a regular non-symlink and be opened without following links. The policy SHALL contain a `[scope]` table with a required boolean `allow_dependency_changes` value and MAY contain `allow`, `deny`, `max_files`, `max_additions`, and `max_deletions`. `allow` and `deny` values SHALL be arrays of repository-relative glob strings, and numeric limits SHALL be non-negative integers. An omitted numeric limit SHALL impose no limit.

#### Scenario: Ignore a mutable policy replacement
- **WHEN** a base commit policy allows only `src/**` and its working-tree `.neckbeard.toml` is replaced without committing it to allow every path
- **THEN** a changed path outside `src/**` is rejected using the base policy

#### Scenario: Reject a nonregular base policy
- **WHEN** the selected base commit stores `.neckbeard.toml` as a symlink or another nonregular tree entry
- **THEN** the checker exits with a policy error without reading the working-tree policy

#### Scenario: Load path rules and budgets
- **WHEN** the selected base policy declares an allow glob, a deny glob, `max_files`, `max_additions`, `max_deletions`, and `allow_dependency_changes = false`
- **THEN** the checker evaluates the diff against those declared values

#### Scenario: Omit a numeric budget
- **WHEN** `.neckbeard.toml` omits `max_deletions`
- **THEN** the checker applies no deletion limit

### Requirement: Apply normalized path rules deterministically
The system SHALL compare normalized repository-relative POSIX paths against every configured full-path glob. In a glob, `*` SHALL match zero or more non-slash characters, `?` SHALL match exactly one non-slash character, and `**` SHALL match zero or more characters including slashes; every other character SHALL be literal. Wildcards SHALL match dotfiles. Leading slashes, backslashes, and `.` or `..` path segments in a configured glob SHALL be invalid policy. A path matching any `deny` glob SHALL be rejected even when it also matches an `allow` glob. A non-empty `allow` list SHALL reject a path that matches none of its entries. An omitted or empty allow list SHALL not constrain paths beyond deny rules and other budgets.

#### Scenario: Deny overrides allow
- **WHEN** the policy allows `src/**` and denies `src/generated/**`, and the changed path is `src/generated/client.py`
- **THEN** the checker reports that path as denied

#### Scenario: A single star does not cross a path separator
- **WHEN** the policy allows `src/*.py` and the changed path is `src/nested/client.py`
- **THEN** the checker reports that path as outside the allow list

#### Scenario: A double star crosses path separators
- **WHEN** the policy allows `src/**` and the changed path is `src/nested/client.py`
- **THEN** the checker permits that path

#### Scenario: A non-empty allow list rejects an unmatched path
- **WHEN** the policy allows only `src/**` and a changed path is `docs/readme.md`
- **THEN** the checker reports that path as outside the allow list

### Requirement: Reject invalid policy distinctly
The system SHALL reject missing `.neckbeard.toml`, a missing `[scope]` table, malformed TOML, missing or non-boolean `allow_dependency_changes`, negative limits, non-array path-rule values, non-string glob entries, and traversal-like path entries as policy errors. It SHALL not evaluate a diff after a policy error.

#### Scenario: Reject a negative budget
- **WHEN** `.neckbeard.toml` sets `max_files = -1`
- **THEN** the command returns exit status 2 without a diff verdict

#### Scenario: Reject a malformed allow value
- **WHEN** `.neckbeard.toml` sets `allow = "src/**"`
- **THEN** the command returns exit status 2 without a diff verdict
