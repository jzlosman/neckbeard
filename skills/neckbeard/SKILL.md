---
name: neckbeard
description: Use when work in a Git repository may be constrained by a Neckbeard diff-scope policy, before reporting completion or asking for review.
---

# Neckbeard

Neckbeard is a mechanical Git diff-scope check. The repository's
`.neckbeard.toml` is the policy; do not copy, reinterpret, edit, or weaken its
rules to make a check pass. The `neckbeard` CLI is authoritative.

## Workflow

1. From the repository (or any subdirectory), read the selected base commit's
   `.neckbeard.toml` to understand the declared scope. In an unborn repository,
   the root regular-file policy is the empty-tree fallback.
2. Before completion or review, run:

   ```sh
   neckbeard check
   ```

   Use `neckbeard check --json` when structured evidence is needed. Use
   `--base REV` only when the task or review explicitly names the comparison
   revision.
3. Report the command's normal verification result together with its
   Neckbeard result, including `PASS` and its summary when it passes.

## Failure handling

- On `FAIL` (exit 1), stop the affected work. Report the exact violations from
  the CLI output: each code and path, plus the chosen base when JSON is used.
  Do not edit `.neckbeard.toml`, suppress files, change the base, stage around
  the check, or otherwise bypass the policy merely to obtain a pass.
- On `ERROR` (exit 2), stop and report the exact error code and message. Fix
  only a legitimate operational cause when that work is in scope; do not turn
  an invalid or missing policy into a permissive one.
- Trace the reported violation to its root cause. If correcting that cause is
  outside the assigned scope, report the root cause and evidence rather than
  symptom-patching or making unrelated edits.

Neckbeard is not a sandbox, security boundary, code review, or replacement for
normal tests and review. It measures the current Git diff after changes exist;
use appropriate permissions, isolation, verification, and human review as
well.
