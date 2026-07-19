## ADDED Requirements

### Requirement: Ship one canonical host-neutral Agent Skill
The project SHALL ship exactly one canonical Agent Skills directory at `skills/neckbeard/` containing `SKILL.md`. Its front matter SHALL use only the standard `name` and `description` fields. The description SHALL state when the skill applies without summarizing its workflow, and the skill SHALL contain no host-specific tool names, model SDK instructions, network bootstrap commands, or duplicate policy rules.

#### Scenario: Inspect the canonical skill metadata
- **WHEN** a maintainer reads `skills/neckbeard/SKILL.md`
- **THEN** it finds standard `name: neckbeard` and a trigger-focused `description` with no host-specific front-matter fields

### Requirement: Direct agents to the repository-owned enforcement point
The skill SHALL instruct an agent to read the repository's `.neckbeard.toml` before making a scoped change, invoke `neckbeard check` against the appropriate base before reporting completion, and report exact violations when the command fails. It SHALL state that the CLI is authoritative and that the skill is not a sandbox or a substitute for tests and review.

#### Scenario: A scope check fails
- **WHEN** an agent following the skill receives a policy-violation verdict from `neckbeard check`
- **THEN** the skill directs the agent to stop and report the violations rather than edit policy, bypass the command, or claim completion

#### Scenario: A scope check passes
- **WHEN** an agent following the skill receives a passing verdict from `neckbeard check`
- **THEN** the skill directs the agent to report the command and result alongside normal project verification
