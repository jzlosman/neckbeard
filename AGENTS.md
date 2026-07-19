# Contributor guidance

- Keep the runtime dependency-free and compatible with Python 3.11+.
- Preserve the CLI's deterministic text/JSON and exit-code contract; add focused
  `unittest` coverage for behavior changes.
- Run `ruff format`, `ruff check`, `python -m unittest discover`, coverage, and
  `uv build` before proposing a change.
- Read `.neckbeard.toml` and run `neckbeard check` for scope evidence. Do not
  edit policy or bypass a failure solely to make a diff pass.
- Keep `skills/neckbeard/SKILL.md` host-neutral. The CLI and repository policy
  are authoritative; the skill is not a sandbox or review replacement.
- Do not commit build artifacts, virtual environments, or generated caches.
