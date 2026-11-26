# SPDX-License-Identifier: Apache-2.0
"""Exercise the actual package builder and the zip files consumed by users."""

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.package import build_packages


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "example-skill"
        self.skill.mkdir()
        (self.root / "LICENSE").write_text("Apache License\n", encoding="utf-8")
        (self.skill / "LICENSE").write_bytes((self.root / "LICENSE").read_bytes())
        (self.skill / "NOTICE").write_text("Example contributors\n", encoding="utf-8")
        (self.skill / "SKILL.md").write_text(
            "---\nname: example-skill\ndescription: Example skill\nlicense: Apache-2.0\n---\n"
            "\nRead [reference](references/example.md).\n",
            encoding="utf-8",
        )
        (self.skill / "references").mkdir()
        (self.skill / "references/example.md").write_text("# Example\n中文参考\n", encoding="utf-8")

    def test_archive_preserves_resources_and_has_verifiable_checksum(self):
        output = self.root / "dist"
        archives = build_packages(self.root, output)
        self.assertEqual(["example-skill.zip"], [path.name for path in archives])
        with zipfile.ZipFile(archives[0]) as archive:
            self.assertEqual(
                (self.skill / "references/example.md").read_bytes(),
                archive.read("example-skill/references/example.md"),
            )
            self.assertEqual(
                (self.root / "LICENSE").read_bytes(), archive.read("example-skill/LICENSE")
            )
            self.assertIn("example-skill/NOTICE", archive.namelist())
            self.assertFalse(
                any(name.startswith("/") or ".." in Path(name).parts for name in archive.namelist())
            )
        checksum, name = (output / "SHA256SUMS").read_text(encoding="utf-8").strip().split()
        self.assertEqual(archives[0].name, name)
        self.assertEqual(hashlib.sha256(archives[0].read_bytes()).hexdigest(), checksum)

    def test_broken_reference_prevents_distribution(self):
        (self.skill / "references/example.md").unlink()
        output = self.root / "dist"
        with self.assertRaises(ValueError):
            build_packages(self.root, output)
        self.assertFalse(list(output.glob("*.zip")))


if __name__ == "__main__":
    unittest.main()
