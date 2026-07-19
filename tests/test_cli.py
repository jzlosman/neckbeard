import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
SENSITIVE = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
)


def isolated_git_environment():
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return environment


class NeckbeardCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test User")
        self.write_policy()
        self.commit("policy")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True, text=True, capture_output=True, env=isolated_git_environment())

    def write(self, path, content, binary=False):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if binary:
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")

    def write_policy(self, **scope):
        values = {"allow_dependency_changes": False, **scope}
        lines = ["[scope]"]
        for key, value in values.items():
            if isinstance(value, bool):
                rendered = str(value).lower()
            elif isinstance(value, list):
                rendered = "[" + ", ".join(json.dumps(item) for item in value) + "]"
            else:
                rendered = json.dumps(value)
            lines.append(f"{key} = {rendered}")
        self.write(".neckbeard.toml", "\n".join(lines) + "\n")

    def set_policy(self, **scope):
        self.write_policy(**scope)
        self.git("add", ".neckbeard.toml")
        self.git("commit", "-qm", "policy update")

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-qm", message)

    def check(self, *args):
        environment = isolated_git_environment() | {"PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "neckbeard", "check", *args], cwd=self.repo, text=True, capture_output=True, env=environment)

    def result(self, *args):
        completed = self.check("--json", *args)
        self.assertTrue(completed.stdout, completed.stderr)
        return completed, json.loads(completed.stdout)

    def test_pass_text_json_and_version_contract(self):
        completed = self.check()
        self.assertEqual(0, completed.returncode)
        self.assertTrue(completed.stdout.startswith("PASS"))
        completed, payload = self.result()
        self.assertEqual(0, completed.returncode)
        self.assertEqual(["version", "verdict", "exit_code", "base", "summary", "changed_paths", "violations", "error"], list(payload))
        self.assertEqual("pass", payload["verdict"])
        self.assertEqual([], payload["violations"])
        self.assertIsNone(payload["error"])

    def test_repository_root_preserves_a_trailing_newline_in_its_name(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repository\n"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=isolated_git_environment())
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, env=isolated_git_environment())
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, env=isolated_git_environment())
            (repo / ".neckbeard.toml").write_text("[scope]\nallow_dependency_changes = false\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, env=isolated_git_environment())
            subprocess.run(["git", "commit", "-qm", "policy"], cwd=repo, check=True, env=isolated_git_environment())
            environment = isolated_git_environment() | {"PYTHONPATH": str(ROOT / "src")}
            completed = subprocess.run(
                [sys.executable, "-m", "neckbeard", "check", "--json"], cwd=repo, text=True, capture_output=True, env=environment
            )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertEqual("pass", json.loads(completed.stdout)["verdict"])

    def test_committed_policy_symlink_is_rejected_without_following_its_target(self):
        with tempfile.TemporaryDirectory() as external:
            target = Path(external) / "policy.toml"
            target.write_text("[scope]\nallow_dependency_changes = false\n", encoding="utf-8")
            (self.repo / ".neckbeard.toml").unlink()
            (self.repo / ".neckbeard.toml").symlink_to(target)
            self.git("add", ".neckbeard.toml")
            self.git("commit", "-qm", "symlinked policy")
            completed, payload = self.result()
        self.assertEqual(2, completed.returncode)
        self.assertEqual("policy-error", payload["error"]["code"])
        self.assertIn("regular Git blob", payload["error"]["message"])

    def test_missing_committed_policy_is_rejected(self):
        self.git("rm", ".neckbeard.toml")
        self.git("commit", "-qm", "remove policy")
        completed, payload = self.result()
        self.assertEqual(2, completed.returncode)
        self.assertEqual("policy-error", payload["error"]["code"])
        self.assertIn("missing .neckbeard.toml in base commit", payload["error"]["message"])

    def test_base_policy_ignores_an_unstaged_permissive_replacement(self):
        self.set_policy(allow=["src/**"])
        self.write_policy(allow=["**"])
        self.write("outside.txt", "changed\n")
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        self.assertIn(("outside.txt", "path-not-allowed"), {(v["path"], v["code"]) for v in payload["violations"]})

    def test_explicit_base_selects_its_committed_policy(self):
        self.set_policy(allow=["src/**"])
        base = self.git("rev-parse", "HEAD").stdout.strip()
        self.set_policy(allow=["**"])
        self.write("outside.txt", "changed\n")
        completed, payload = self.result("--base", base)
        self.assertEqual(1, completed.returncode)
        self.assertIn(("outside.txt", "path-not-allowed"), {(v["path"], v["code"]) for v in payload["violations"]})

    def test_cli_ignores_an_inherited_conflicting_git_dir(self):
        self.set_policy(deny=["main.txt"])
        self.write("main.txt", "changed\n")
        rival = self.repo.parent / f"rival-{self.repo.name}"
        rival.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=rival, check=True, env=isolated_git_environment())
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=rival, check=True, env=isolated_git_environment())
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=rival, check=True, env=isolated_git_environment())
        (rival / ".neckbeard.toml").write_text("[scope]\nallow_dependency_changes = false\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=rival, check=True, env=isolated_git_environment())
        subprocess.run(["git", "commit", "-qm", "policy"], cwd=rival, check=True, env=isolated_git_environment())
        subprocess.run(["git", "config", "core.worktree", str(rival)], cwd=rival, check=True, env=isolated_git_environment())
        with patch.dict(os.environ, {"GIT_DIR": str(rival / ".git")}):
            completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        self.assertIn(("main.txt", "path-denied"), {(v["path"], v["code"]) for v in payload["violations"]})

    def test_invalid_base_and_invalid_policy_are_errors(self):
        completed = self.check("--base", "does-not-exist")
        self.assertEqual(2, completed.returncode)
        self.assertTrue(completed.stdout.startswith("ERROR"))
        completed, payload = self.result("--base", "does-not-exist")
        self.assertEqual(2, completed.returncode)
        self.assertEqual("error", payload["verdict"])
        completed = self.check("--base", "")
        self.assertEqual(2, completed.returncode)
        self.assertTrue(completed.stdout.startswith("ERROR base-error:"), completed.stdout)
        completed, payload = self.result("--base", "")
        self.assertEqual(2, completed.returncode)
        self.assertEqual("base-error", payload["error"]["code"])
        self.write(".neckbeard.toml", '[scope]\nallow_dependency_changes = "false"\n')
        self.git("add", ".neckbeard.toml")
        self.git("commit", "-qm", "invalid policy")
        completed, payload = self.result()
        self.assertEqual(2, completed.returncode)
        self.assertEqual("error", payload["verdict"])
        self.assertIsNotNone(payload["error"])

    def test_policy_validation_rejects_bad_types_budgets_and_patterns(self):
        invalid = [
            "",
            "[scope",
            "[scope]\n",
            "[scope]\nallow_dependency_changes = false\nmax_files = -1\n",
            '[scope]\nallow_dependency_changes = false\nallow = "src/**"\n',
            '[scope]\nallow_dependency_changes = false\ndeny = ["/src/**"]\n',
            '[scope]\nallow_dependency_changes = false\ndeny = ["src\\\\**"]\n',
            '[scope]\nallow_dependency_changes = false\ndeny = ["src/../secret"]\n',
        ]
        for policy in invalid:
            with self.subTest(policy=policy):
                self.write(".neckbeard.toml", policy)
                self.git("add", ".neckbeard.toml")
                self.git("commit", "-qm", "invalid policy")
                completed = self.check("--json")
                self.assertEqual(2, completed.returncode)

    def test_globs_allow_deny_full_path_and_dotfiles(self):
        self.set_policy(allow=["src/*.py", ".hidden"], deny=["src/generated/**"])
        self.write("src/top.py", "x\n")
        self.write("src/nested/no.py", "x\n")
        self.write("src/generated/client.py", "x\n")
        self.write(".hidden", "x\n")
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        codes = {(item["path"], item["code"]) for item in payload["violations"]}
        self.assertIn(("src/nested/no.py", "path-not-allowed"), codes)
        self.assertIn(("src/generated/client.py", "path-denied"), codes)
        self.set_policy(allow=["src/**"])
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        self.assertIn(".hidden", [item["path"] for item in payload["violations"]])

    def test_double_star_slash_matches_zero_or_more_directories(self):
        self.set_policy(allow=["src/**/top.py", "**/name"])
        for path in ("src/top.py", "src/nested/top.py", "name", "nested/name"):
            self.write(path, "x\n")
        completed, payload = self.result()
        self.assertEqual(0, completed.returncode)
        self.assertEqual([], payload["violations"])

    def test_question_glob_and_file_addition_budgets(self):
        self.set_policy(allow=["src/?.py"], max_files=1, max_additions=1)
        self.write("src/a.py", "one\n")
        self.write("src/ab.py", "one\n")
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        codes = {(item["path"], item["code"]) for item in payload["violations"]}
        self.assertIn(("src/ab.py", "path-not-allowed"), codes)
        self.assertIn(("", "max-files"), codes)
        self.assertIn(("", "max-additions"), codes)

    def test_explicit_base_differs_from_default_head(self):
        self.write("history.txt", "one\n")
        self.commit("history")
        explicit_base = self.git("rev-parse", "HEAD").stdout.strip()
        self.write("history.txt", "two\n")
        self.commit("new head")
        self.write("working.txt", "work\n")
        completed, default = self.result()
        self.assertEqual(0, completed.returncode)
        self.assertEqual(["working.txt"], default["changed_paths"])
        completed, explicit = self.result("--base", explicit_base)
        self.assertEqual(0, completed.returncode)
        self.assertEqual(explicit_base, explicit["base"])
        self.assertEqual(["history.txt", "working.txt"], explicit["changed_paths"])

    def test_staged_unstaged_untracked_and_ignored_files_are_all_measured(self):
        self.write("tracked.txt", "old\n")
        self.write("staged.txt", "before\n")
        self.write(".gitignore", "ignored.txt\n")
        self.commit("tracked")
        self.write("tracked.txt", "new\n")
        self.write("staged.txt", "after\n")
        self.git("add", "staged.txt")
        self.write("untracked.txt", "one\ntwo\n")
        self.write("ignored.txt", "ignore me\n")
        completed, payload = self.result()
        self.assertEqual(0, completed.returncode)
        self.assertEqual(["staged.txt", "tracked.txt", "untracked.txt"], payload["changed_paths"])
        self.assertEqual({"changed_files": 3, "additions": 4, "deletions": 2}, payload["summary"])

    def test_budgets_deletion_and_rename_are_complete(self):
        self.write("src/a.py", "old\n")
        self.write("delete.txt", "bye\n")
        self.commit("files")
        self.set_policy(allow=["**"], deny=["secrets/**"], max_deletions=1)
        (self.repo / "secrets").mkdir()
        self.git("mv", "src/a.py", "secrets/a.py")
        (self.repo / "delete.txt").unlink()
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        self.assertEqual(["delete.txt", "secrets/a.py", "src/a.py"], payload["changed_paths"])
        codes = {(item["path"], item["code"]) for item in payload["violations"]}
        self.assertIn(("secrets/a.py", "path-denied"), codes)
        self.assertIn(("", "max-deletions"), codes)

    def test_unborn_head_defaults_to_empty_tree(self):
        self.temp.cleanup()
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.write_policy()
        self.write("new.txt", "new\n")
        completed, payload = self.result()
        self.assertEqual(0, completed.returncode)
        self.assertEqual(EMPTY_TREE, payload["base"])
        self.assertIn("new.txt", payload["changed_paths"])

    def test_unborn_policy_symlink_is_rejected_without_following_its_target(self):
        self.temp.cleanup()
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        target = self.repo.parent / "outside-policy.toml"
        target.write_text("[scope]\nallow_dependency_changes = false\n", encoding="utf-8")
        (self.repo / ".neckbeard.toml").symlink_to(target)
        completed, payload = self.result()
        self.assertEqual(2, completed.returncode)
        self.assertEqual("policy-error", payload["error"]["code"])
        self.assertIn("symlink", payload["error"]["message"])

    def test_unborn_policy_must_be_a_regular_file(self):
        self.temp.cleanup()
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        (self.repo / ".neckbeard.toml").mkdir()
        completed, payload = self.result()
        self.assertEqual(2, completed.returncode)
        self.assertEqual("policy-error", payload["error"]["code"])
        self.assertIn("regular file", payload["error"]["message"])

    def test_binary_files_fail_closed(self):
        self.write("blob.bin", b"a\x00b", binary=True)
        completed = self.check()
        self.assertEqual(1, completed.returncode)
        self.assertTrue(completed.stdout.startswith("FAIL"))
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        self.assertIn(("blob.bin", "unmeasurable-file"), {(v["path"], v["code"]) for v in payload["violations"]})

    def test_untracked_symlink_is_unmeasurable_without_counting_its_target(self):
        outside = self.repo.parent / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        (self.repo / "link.txt").symlink_to(outside)
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        self.assertEqual({"changed_files": 1, "additions": 0, "deletions": 0}, payload["summary"])
        self.assertIn(("link.txt", "unmeasurable-file"), {(v["path"], v["code"]) for v in payload["violations"]})

    def test_tracked_symlink_uses_git_blob_metrics_without_reading_its_target(self):
        first = self.repo.parent / "first-target"
        second = self.repo.parent / "second-target"
        first.write_bytes(b"first\0target")
        second.write_bytes(b"second\0target")
        (self.repo / "link.txt").symlink_to(first)
        self.commit("tracked symlink")
        (self.repo / "link.txt").unlink()
        (self.repo / "link.txt").symlink_to(second)
        completed, payload = self.result()
        self.assertEqual(0, completed.returncode)
        self.assertEqual({"changed_files": 1, "additions": 1, "deletions": 1}, payload["summary"])
        self.assertEqual([], payload["violations"])

    def test_every_sensitive_filename_nested_requires_approval_in_byte_order(self):
        for name in SENSITIVE:
            self.write(f"nested/{name}", "x\n")
        completed, payload = self.result()
        self.assertEqual(1, completed.returncode)
        violations = [item for item in payload["violations"] if item["code"] == "dependency-change"]
        self.assertEqual(sorted(f"nested/{name}" for name in SENSITIVE), [item["path"] for item in violations])
        self.set_policy(allow_dependency_changes=True)
        completed, payload = self.result()
        self.assertEqual(0, completed.returncode)
        self.assertFalse(payload["violations"])


if __name__ == "__main__":
    unittest.main()
