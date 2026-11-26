# SPDX-License-Identifier: Apache-2.0
"""Check the validator against broken distributable skill packages."""

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.validate import validate


class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "sample-skill"
        self.skill.mkdir()
        self.write_skill("Read [details](references/details.md).\n")
        (self.skill / "references").mkdir()
        (self.skill / "references/details.md").write_text("# Details\n", encoding="utf-8")
        (self.skill / "LICENSE").write_text("Apache License\nVersion 2.0\n", encoding="utf-8")
        (self.root / "LICENSE").write_bytes((self.skill / "LICENSE").read_bytes())
        (self.skill / "NOTICE").write_text("Sample contributors\n", encoding="utf-8")

    def write_skill(self, body):
        (self.skill / "SKILL.md").write_text(
            "---\nname: sample-skill\ndescription: Use when testing a package.\n"
            "license: Apache-2.0\n---\n\n# Sample\n\n" + body,
            encoding="utf-8",
        )

    def test_self_contained_package_is_valid(self):
        self.assertEqual([], validate(self.root))

    def test_missing_reference_is_reported(self):
        (self.skill / "references/details.md").unlink()
        self.assertTrue(any("details.md" in error for error in validate(self.root)))

    def test_sibling_dependency_is_not_portable(self):
        (self.root / "shared.md").write_text("# Shared\n", encoding="utf-8")
        self.write_skill("Read [shared](../shared.md).\n")
        self.assertTrue(any("escapes skill" in error for error in validate(self.root)))

    def test_frontmatter_must_match_install_directory(self):
        entry = self.skill / "SKILL.md"
        entry.write_text(
            entry.read_text(encoding="utf-8").replace("name: sample-skill", "name: another-skill"),
            encoding="utf-8",
        )
        self.assertTrue(any("directory" in error for error in validate(self.root)))

    def test_unclosed_fence_is_reported(self):
        self.write_skill("```text\nunclosed\n")
        self.assertTrue(any("fence" in error for error in validate(self.root)))

    def test_example_links_in_code_are_not_resolved(self):
        self.write_skill(
            '```markdown\n[output](future-report.md)\n```\nCall `attributes["execute"](revision)` or show `[example](future.md)`.\n'
        )
        self.assertEqual([], validate(self.root))

    def test_standalone_package_needs_license(self):
        (self.skill / "LICENSE").unlink()
        self.assertTrue(any("LICENSE" in error for error in validate(self.root)))

    def test_duplicate_explicit_anchor_is_reported(self):
        self.write_skill('<a id="r-pc45"></a>\n\nFirst\n\n<a id="r-pc45"></a>\n\nSecond\n')
        self.assertTrue(any("duplicate anchor" in error for error in validate(self.root)))

    def test_wrong_rule_anchor_is_reported(self):
        self.write_skill("Read [rule](references/details.md#r-pc45-02).\n")
        self.assertTrue(any("missing explicit anchor" in error for error in validate(self.root)))

    def test_supported_markdown_links_cannot_hide_missing_files(self):
        for body in (
            'Read [details](references/missing.md "optional title").\n',
            "Read [details][ref].\n\n[ref]: references/missing.md\n",
            "Read [details](<references/missing file.md>).\n",
        ):
            with self.subTest(body=body):
                self.write_skill(body)
                self.assertTrue(any("missing" in error for error in validate(self.root)))

    def test_machine_paths_are_not_portable_links(self):
        for target in ("file:///C:/notes.md", "C:/notes.md", "/tmp/notes.md"):
            with self.subTest(target=target):
                self.write_skill(f"Read [notes]({target}).\n")
                self.assertTrue(any("portable" in error for error in validate(self.root)))

    def test_license_drift_is_reported(self):
        (self.skill / "LICENSE").write_text("Truncated license\n", encoding="utf-8")
        self.assertTrue(any("LICENSE differs" in error for error in validate(self.root)))

    def test_invalid_skill_contract_fields_are_reported(self):
        valid = (self.skill / "SKILL.md").read_text(encoding="utf-8")
        for original, replacement in (
            ("license: Apache-2.0", "license: Apache-2.0\nunsupported: true"),
            ("Use when testing a package.", "Use <unfinished> instructions."),
            ("# Sample", "# Sample\n\n[TODO: replace the generated scaffold]"),
        ):
            with self.subTest(replacement=replacement):
                (self.skill / "SKILL.md").write_text(
                    valid.replace(original, replacement), encoding="utf-8"
                )
                self.assertTrue(validate(self.root))

    def test_malformed_ui_metadata_is_reported_without_crashing(self):
        ui = self.skill / "agents/openai.yaml"
        ui.parent.mkdir()
        for config in (
            [],
            {"interface": {"default_prompt": ["$sample-skill"], "short_description": "x" * 30}},
            {"interface": {"default_prompt": "$sample-skill", "short_description": ["x"] * 30}},
        ):
            with self.subTest(config=config):
                ui.write_text(yaml.safe_dump(config), encoding="utf-8")
                self.assertTrue(validate(self.root))

    def test_skill_directory_without_entrypoint_is_reported(self):
        (self.skill / "SKILL.md").unlink()
        another = self.root / "another-skill"
        another.mkdir()
        (another / "SKILL.md").write_text(
            "---\nname: another-skill\ndescription: Example\nlicense: Apache-2.0\n---\n",
            encoding="utf-8",
        )
        for name in ("LICENSE", "NOTICE"):
            (another / name).write_bytes((self.skill / name).read_bytes())
        self.assertTrue(
            any("sample-skill" in error and "SKILL.md" in error for error in validate(self.root))
        )


if __name__ == "__main__":
    unittest.main()
