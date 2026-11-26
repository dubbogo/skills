# SPDX-License-Identifier: Apache-2.0
"""Guard the Git whitespace check used by the push workflow."""

import subprocess
import tempfile
import unittest
from pathlib import Path


def run_git(root, *args):
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def check_pushed_whitespace(root):
    return subprocess.run(
        ["git", "diff-tree", "-m", "--check", "--root", "-r", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
    )


class WorkflowWhitespaceTests(unittest.TestCase):
    def create_repo(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        run_git(root, "init")
        run_git(root, "config", "user.email", "ci@example.invalid")
        run_git(root, "config", "user.name", "CI")
        return root

    def commit_file(self, root, name, content, message):
        (root / name).write_text(content, encoding="utf-8")
        run_git(root, "add", name)
        run_git(root, "commit", "-m", message)

    def test_root_and_normal_commits_are_checked(self):
        root = self.create_repo()
        self.commit_file(root, "root.txt", "root   \n", "root")
        result = check_pushed_whitespace(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("root.txt", result.stdout)

        self.commit_file(root, "root.txt", "root\n", "clean root")
        self.commit_file(root, "normal.txt", "normal   \n", "normal")
        result = check_pushed_whitespace(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("normal.txt", result.stdout)

    def test_merge_commits_are_checked_against_each_parent(self):
        root = self.create_repo()
        self.commit_file(root, "root.txt", "root\n", "root")
        run_git(root, "checkout", "-b", "side")
        self.commit_file(root, "side.txt", "side   \n", "side")
        run_git(root, "checkout", "-")
        run_git(root, "merge", "--no-ff", "side", "-m", "merge")

        result = check_pushed_whitespace(root)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("side.txt", result.stdout)


if __name__ == "__main__":
    unittest.main()
