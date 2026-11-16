"""Validate bundled Athena Skills and the architect approval contract."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"


class SkillsManifestTests(unittest.TestCase):
    def test_all_manifest_skills_exist(self):
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["skills"]), len(set(manifest["skills"])))
        for directory in manifest["skills"]:
            with self.subTest(directory=directory):
                self.assertFalse(Path(directory).is_absolute())
                skill = (PLUGIN / directory / "SKILL.md").resolve()
                self.assertTrue(skill.is_relative_to(PLUGIN.resolve()))
                self.assertTrue(skill.is_file())
                text = skill.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                header = text.split("---", 2)[1]
                self.assertRegex(header, r"(?m)^name:\s*\S+")
                self.assertRegex(header, r"(?m)^description:\s*\S+")

    def test_architect_approval_is_documented(self):
        guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn("aguardar aprovação", guidance)
        self.assertIn("antes de modificar", guidance)
        for skill in ("athena-developer", "athena-operations"):
            with self.subTest(skill=skill):
                content = (PLUGIN / "skills" / skill / "SKILL.md").read_text(encoding="utf-8").lower()
                self.assertIn("aprovação", content)

    def test_skill_names_unique(self):
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        found = []
        for directory in manifest["skills"]:
            content = (PLUGIN / directory / "SKILL.md").read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*(.+)$", content.split("---", 2)[1])
            self.assertIsNotNone(match)
            found.append(match.group(1).strip())
        self.assertEqual(len(found), len(set(found)))


if __name__ == "__main__":
    unittest.main()
