## ADDED Requirements

### Requirement: Select a deterministic comparison base
The system SHALL compare the working tree with an explicitly selected `--base` revision when one is supplied; otherwise it SHALL use `HEAD`. When no base is supplied and the repository has no `HEAD` commit, it SHALL use Git's empty tree. An explicitly supplied invalid base SHALL be an error.

#### Scenario: Use an explicit base
- **WHEN** a caller invokes `neckbeard check --base main`
- **THEN** the checker evaluates changes against `main` rather than `HEAD`

#### Scenario: Check an unborn repository
- **WHEN** no base is supplied and the repository has no commit
- **THEN** the checker evaluates the working tree against the empty tree

### Requirement: Collect the complete visible working-tree change set
The system SHALL collect tracked staged and unstaged changes between the selected base and the working tree, plus non-ignored untracked files. It SHALL include additions, modifications, and deletions. It SHALL disable Git rename detection and represent a rename as a deletion plus an addition so both paths are evaluated.

#### Scenario: Include staged, unstaged, and untracked files
- **WHEN** one file is staged, a different tracked file has an unstaged edit, and a third file is untracked
- **THEN** all three paths appear in the evaluated change set

#### Scenario: Apply path rules to both sides of a rename
- **WHEN** a tracked file moves from `src/a.py` to `secrets/a.py` and the policy denies `secrets/**`
- **THEN** the checker reports the added `secrets/a.py` path as denied

### Requirement: Measure and enforce diff budgets
The system SHALL calculate unique changed-file count, textual additions, and textual deletions across the complete change set, then enforce every configured maximum. It SHALL count untracked text-file lines as additions. A binary or otherwise unmeasurable changed file SHALL produce a fail-closed policy violation rather than a zero line count.

#### Scenario: Fail an exceeded additions limit
- **WHEN** the evaluated change set has 11 additions and the policy sets `max_additions = 10`
- **THEN** the checker reports an additions-budget violation

#### Scenario: Include untracked text in the additions budget
- **WHEN** an untracked text file contains two lines and the policy sets `max_additions = 1`
- **THEN** the checker reports an additions-budget violation

#### Scenario: Measure a tracked Git symlink blob without dereferencing it
- **WHEN** a tracked symlink changes and its target is outside the repository
- **THEN** the checker uses Git's blob numstat for the symlink and does not read the target

#### Scenario: Reject an untracked symlink
- **WHEN** an untracked path is a symlink
- **THEN** the checker reports it as an unmeasurable file without reading its target

### Requirement: Produce deterministic change facts
The system SHALL sort changed paths in bytewise repository-relative path order and sort violations by repository-relative path bytes followed by violation code before rendering a verdict. It SHALL not mutate the Git index, configuration, or working tree while checking.

#### Scenario: Repeat a check without state changes
- **WHEN** the same working tree, base, and policy are checked twice
- **THEN** both checks produce the same changed-path ordering and metrics
