# Contributing

Thanks for contributing. Please open an issue before broad changes so scope is
clear, then keep pull requests focused.

## Local checks

Python 3.11+ and Git are required. Install the package and development tools,
then run the same checks as CI:

```sh
uv venv
uv pip install -e . -r requirements-dev.txt
ruff format
ruff check
coverage run -m unittest discover
coverage combine
coverage report
uv build
neckbeard check
```

Add focused `unittest` coverage for behavior changes. Preserve deterministic
CLI output and the documented exit codes. The final `neckbeard check` result is
scope evidence, not a replacement for tests or review.

## Pull requests

Describe the problem, the minimal change, tests run, and any policy impact.
Follow the [Code of Conduct](CODE_OF_CONDUCT.md). See [SECURITY.md](SECURITY.md)
for vulnerabilities; do not disclose them in public issues.
