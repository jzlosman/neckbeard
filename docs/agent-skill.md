# Agent skill

[`skills/neckbeard/SKILL.md`](../skills/neckbeard/SKILL.md) is the sole
canonical, portable Agent Skills instruction. Its frontmatter contains only a
name and trigger-focused description, so it does not depend on a specific
agent host.

## Install

Copy the entire `skills/neckbeard/` directory through the host's documented
skill installation mechanism. Common project or user locations include
`.claude/skills/` for Claude Code, `$CODEX_HOME/skills/` for Codex,
`.gemini/skills/` for Gemini CLI, and `.pi/skills/` for Pi. skills.sh users
should import the same canonical directory through skills.sh rather than fork
its instructions.

Install the `neckbeard` CLI separately and make it available on `PATH`. Skill
discovery does not guarantee automatic invocation or enforcement; configure
CI and contributor/agent workflows to run `neckbeard check` as needed.

## Expected behavior

The skill directs an agent to read the repository's `.neckbeard.toml`, run
`neckbeard check` before completion or review, and report `PASS` with normal
verification. For a `FAIL` or `ERROR`, it stops the affected work and reports
the CLI's exact evidence. It must not edit policy, select a different base,
or hide changes merely to pass.

The CLI is authoritative. The skill neither duplicates the policy nor replaces
sandboxing, access controls, tests, security review, or human review. If a
reported root cause is outside the assigned work, report that cause rather than
symptom-patching it.
