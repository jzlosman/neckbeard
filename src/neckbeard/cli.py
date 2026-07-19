"""Command-line implementation for Neckbeard."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tomllib
from typing import Any

from . import __version__

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
SENSITIVE_NAMES = frozenset({
    "pyproject.toml", "requirements.txt", "requirements-dev.txt", "Pipfile",
    "Pipfile.lock", "poetry.lock", "uv.lock", "package.json",
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml",
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
})


class NeckbeardError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise NeckbeardError("invocation-error", message)


@dataclass(frozen=True)
class Policy:
    allow_dependency_changes: bool
    allow: tuple[str, ...]
    deny: tuple[str, ...]
    max_files: int | None
    max_additions: int | None
    max_deletions: int | None


def path_key(path: str) -> bytes:
    return path.encode("utf-8", "surrogateescape")


def git(root: Path | None, *args: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise NeckbeardError("git-error", str(error)) from error


def repository_root() -> Path:
    result = git(None, "rev-parse", "--show-toplevel")
    if result.returncode:
        raise NeckbeardError("repository-error", "not inside a Git working tree")
    return Path(os.fsdecode(result.stdout.removesuffix(b"\n")))


def validate_patterns(value: Any, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise NeckbeardError("policy-error", f"scope.{field} must be an array of strings")
    patterns: list[str] = []
    for pattern in value:
        if not isinstance(pattern, str):
            raise NeckbeardError("policy-error", f"scope.{field} entries must be strings")
        if pattern.startswith("/") or "\\" in pattern or any(part in {".", ".."} for part in pattern.split("/")):
            raise NeckbeardError("policy-error", f"invalid scope.{field} pattern: {pattern!r}")
        patterns.append(pattern)
    return tuple(patterns)


def load_policy(root: Path) -> Policy:
    filename = root / ".neckbeard.toml"
    try:
        if filename.is_symlink():
            raise NeckbeardError("policy-error", ".neckbeard.toml must not be a symlink")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(filename, flags), "rb") as policy_file:
            data = tomllib.load(policy_file)
    except FileNotFoundError as error:
        raise NeckbeardError("policy-error", "missing .neckbeard.toml") from error
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise NeckbeardError("policy-error", f"invalid .neckbeard.toml: {error}") from error
    scope = data.get("scope")
    if not isinstance(scope, dict):
        raise NeckbeardError("policy-error", "missing [scope] table")
    approved = scope.get("allow_dependency_changes")
    if type(approved) is not bool:
        raise NeckbeardError("policy-error", "scope.allow_dependency_changes must be a boolean")

    limits: dict[str, int | None] = {}
    for name in ("max_files", "max_additions", "max_deletions"):
        value = scope.get(name)
        if value is None:
            limits[name] = None
        elif type(value) is int and value >= 0:
            limits[name] = value
        else:
            raise NeckbeardError("policy-error", f"scope.{name} must be a non-negative integer")
    return Policy(approved, validate_patterns(scope.get("allow"), "allow"),
                  validate_patterns(scope.get("deny"), "deny"), limits["max_files"],
                  limits["max_additions"], limits["max_deletions"])


def glob_matches(pattern: str, path: str) -> bool:
    pieces: list[str] = ["^"]
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if pattern.startswith("**/", index):
            pieces.append("(?:.*/)?")
            index += 3
        elif character == "*" and index + 1 < len(pattern) and pattern[index + 1] == "*":
            pieces.append(".*")
            index += 2
        elif character == "*":
            pieces.append("[^/]*")
            index += 1
        elif character == "?":
            pieces.append("[^/]")
            index += 1
        else:
            pieces.append(re.escape(character))
            index += 1
    pieces.append("$")
    return re.fullmatch("".join(pieces), path) is not None


def select_base(root: Path, requested: str | None) -> str:
    candidate = "HEAD" if requested is None else requested
    result = git(root, "rev-parse", "--verify", f"{candidate}^{{commit}}")
    if result.returncode == 0:
        return os.fsdecode(result.stdout).strip()
    if requested is None:
        # HEAD is the only default allowed to fall back, and only when unborn.
        head = git(root, "rev-parse", "--verify", "HEAD")
        if head.returncode:
            return EMPTY_TREE
    raise NeckbeardError("base-error", f"invalid base revision: {candidate}")


def text_lines(data: bytes) -> int | None:
    if b"\0" in data:
        return None
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def collect_changes(root: Path, base: str) -> tuple[dict[str, list[int]], set[str]]:
    result = git(root, "diff", "--no-ext-diff", "--no-renames", "--numstat", "-z", base, "--")
    if result.returncode:
        raise NeckbeardError("git-error", os.fsdecode(result.stderr).strip() or "could not read Git diff")
    metrics: dict[str, list[int]] = {}
    unmeasurable: set[str] = set()
    for item in result.stdout.split(b"\0"):
        if not item:
            continue
        try:
            added, deleted, raw_path = item.split(b"\t", 2)
        except ValueError as error:
            raise NeckbeardError("git-error", "unexpected Git numstat output") from error
        path = os.fsdecode(raw_path)
        current = metrics.setdefault(path, [0, 0])
        if added == b"-" or deleted == b"-":
            unmeasurable.add(path)
        else:
            current[0] += int(added)
            current[1] += int(deleted)

    result = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if result.returncode:
        raise NeckbeardError("git-error", os.fsdecode(result.stderr).strip() or "could not list untracked files")
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        path = os.fsdecode(raw_path)
        metrics.setdefault(path, [0, 0])
        file_path = root / Path(path)
        try:
            lines = None if file_path.is_symlink() else text_lines(file_path.read_bytes())
        except OSError:
            lines = None
        if lines is None:
            unmeasurable.add(path)
        else:
            metrics[path][0] += lines
    return metrics, unmeasurable


def violation(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def evaluate(root: Path, policy: Policy, base: str) -> dict[str, Any]:
    changes, unmeasurable = collect_changes(root, base)
    paths = sorted(changes, key=path_key)
    additions = sum(changes[path][0] for path in paths)
    deletions = sum(changes[path][1] for path in paths)
    violations: list[dict[str, str]] = []
    for path in paths:
        if any(glob_matches(pattern, path) for pattern in policy.deny):
            violations.append(violation("path-denied", path, "path matches deny rule"))
        elif policy.allow and not any(glob_matches(pattern, path) for pattern in policy.allow):
            violations.append(violation("path-not-allowed", path, "path does not match allow rule"))
        if PurePosixPath(path).name in SENSITIVE_NAMES and not policy.allow_dependency_changes:
            violations.append(violation("dependency-change", path, "dependency-sensitive path requires approval"))
        if path in unmeasurable:
            violations.append(violation("unmeasurable-file", path, "binary or unmeasurable file cannot be counted"))
    if policy.max_files is not None and len(paths) > policy.max_files:
        violations.append(violation("max-files", "", f"changed files {len(paths)} exceed {policy.max_files}"))
    if policy.max_additions is not None and additions > policy.max_additions:
        violations.append(violation("max-additions", "", f"additions {additions} exceed {policy.max_additions}"))
    if policy.max_deletions is not None and deletions > policy.max_deletions:
        violations.append(violation("max-deletions", "", f"deletions {deletions} exceed {policy.max_deletions}"))
    violations.sort(key=lambda item: (path_key(item["path"]), item["code"]))
    return {
        "version": 1,
        "verdict": "violation" if violations else "pass",
        "exit_code": 1 if violations else 0,
        "base": base,
        "summary": {"changed_files": len(paths), "additions": additions, "deletions": deletions},
        "changed_paths": paths,
        "violations": violations,
        "error": None,
    }


def error_verdict(error: NeckbeardError) -> dict[str, Any]:
    return {
        "version": 1, "verdict": "error", "exit_code": 2, "base": None,
        "summary": {"changed_files": 0, "additions": 0, "deletions": 0},
        "changed_paths": [], "violations": [],
        "error": {"code": error.code, "message": error.message},
    }


def render(payload: dict[str, Any], as_json: bool) -> str:
    if as_json:
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    if payload["verdict"] == "pass":
        summary = payload["summary"]
        return f"PASS base={payload['base']} files={summary['changed_files']} additions={summary['additions']} deletions={summary['deletions']}"
    if payload["verdict"] == "violation":
        details = "; ".join(f"{item['code']} {item['path']}".rstrip() for item in payload["violations"])
        return f"FAIL {details}"
    error = payload["error"]
    return f"ERROR {error['code']}: {error['message']}"


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = UsageParser(prog="neckbeard")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check")
    check.add_argument("--base")
    check.add_argument("--json", action="store_true", dest="as_json")
    try:
        args = parser.parse_args(args_list)
        root = repository_root()
        policy = load_policy(root)
        payload = evaluate(root, policy, select_base(root, args.base))
        as_json = args.as_json
    except NeckbeardError as error:
        payload = error_verdict(error)
        as_json = "--json" in args_list
    print(render(payload, as_json))
    return payload["exit_code"]
