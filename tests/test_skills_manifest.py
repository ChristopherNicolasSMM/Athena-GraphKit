"""Validate the Athena portable plugin's declared skills and governance."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"

class SkillsManifestTests(unittest.TestCase):
    def test_portable_manifest_and_four_skills(self):
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(
            manifest.get("$schema"),
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        names = set()
        skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 4)
        for skill in skills:
            with self.subTest(path=skill):
                content = skill.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"))
                header = content.split("---", 2)[1]
                name = re.search(r"(?m)^name:\s*(\S+)", header)
                self.assertIsNotNone(name)
                self.assertEqual(name.group(1), skill.parent.name)
                self.assertRegex(header, r"(?m)^description:\s*\S")
                self.assertNotIn(name.group(1), names)
                names.add(name.group(1))
        self.assertEqual(names, {
            "athena-graphkit", "athena-user",
            "athena-developer", "athena-operations",
        })
        interface = manifest["extensions"]["com.openai"]["interface"]
        for key in ("logo", "composerIcon"):
            self.assertTrue((PLUGIN / interface[key]).is_file())
        self.assertFalse((PLUGIN / "mcp.json").exists())

    def test_architect_approval_documented(self):
        guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn("aguardar aprovação", guidance)
        self.assertIn("antes de modificar", guidance)
        self.assertIn("desenvolvimento", guidance)
        for skill in ("athena-developer", "athena-operations"):
            content = (PLUGIN / "skills" / skill / "SKILL.md").read_text(encoding="utf-8").lower()
            self.assertIn("aprovação", content)

if __name__ == "__main__":
    unittest.main()
