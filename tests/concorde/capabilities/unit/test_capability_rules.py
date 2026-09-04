from __future__ import annotations

import json
import sys
import unittest

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.skill_assets import PATH_ROLES  # noqa: E402


class CapabilityLayoutRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())

    def test_manifest_owns_one_global_skill_namespace(self):
        skills = self.manifest["skills"]
        operations = self.manifest["operations"]
        self.assertEqual(self.manifest["schema_version"], 2)
        self.assertEqual(self.manifest["skill_namespace"], "concorde")
        self.assertEqual(len(skills), 17)
        self.assertEqual(
            operations,
            ["concorde-standard-dev-loop", "concorde-reflections-triage", "concorde-plan"],
        )
        self.assertFalse(set(skills) & set(operations))

    def test_each_leaf_is_one_markdown_capability_without_python(self):
        observed = sorted(path.name for path in (REPOSITORY_ROOT / "skills").iterdir())
        self.assertEqual(observed, sorted(self.manifest["skills"]))
        for name in observed:
            with self.subTest(skill=name):
                directory = REPOSITORY_ROOT / "skills" / name
                self.assertEqual(
                    [path.name for path in directory.iterdir()],
                    ["SKILL.md"],
                )
                body = (directory / "SKILL.md").read_text()
                self.assertTrue(body.startswith(f"---\nname: {name}\n"))
                self.assertIn("\ndescription:", body.split("---", 2)[1])
                self.assertRegex(body, r"(?m)^# ")

    def test_each_operation_is_exactly_one_python_markdown_pair(self):
        observed = sorted(
            path.name for path in (REPOSITORY_ROOT / "operations").iterdir() if path.is_dir()
        )
        self.assertEqual(observed, sorted(self.manifest["operations"]))
        for name in observed:
            with self.subTest(operation=name):
                directory = REPOSITORY_ROOT / "operations" / name
                self.assertEqual(
                    sorted(
                        path.name
                        for path in directory.iterdir()
                        if path.name != "__pycache__" and path.suffix not in {".pyc", ".pyo"}
                    ),
                    ["SKILL.md", "operation.py"],
                )
                skill = (directory / "SKILL.md").read_text()
                self.assertIn("operation: operation.py", skill)
                self.assertIn("capabilities:\n", skill)
                self.assertNotIn("skills:\n", skill)
                self.assertIn("{OPERATION}", skill)
                python = (directory / "operation.py").read_text()
                self.assertIn("OPERATION_CAPABILITIES", python)
                self.assertIn("OPERATION_BINDINGS", python)
                self.assertNotIn("OPERATION_SKILLS", python)

    def test_permission_capability_vocabulary_is_closed_and_role_based(self):
        self.assertTrue(
            {
                "selected-feature",
                "module-architecture",
                "required-feature-specs",
                "owned-implementation",
                "task-authorized",
                "attempt",
                "reflections",
                "reflection-worktrees",
            }.issubset(PATH_ROLES)
        )
        self.assertFalse(any("/" in role or ".." in role for role in PATH_ROLES))

    def test_removed_flat_capability_roots_are_absent(self):
        self.assertFalse((REPOSITORY_ROOT / "commands").exists())
        self.assertFalse((REPOSITORY_ROOT / "examples").exists())
        self.assertFalse((REPOSITORY_ROOT / "src/concorde/command_assets.py").exists())
        self.assertFalse((REPOSITORY_ROOT / "src/concorde/workflows.py").exists())
        self.assertTrue((REPOSITORY_ROOT / "src/concorde/capabilities/skill_assets.py").is_file())
        self.assertTrue((REPOSITORY_ROOT / "src/concorde/capabilities/operation_runtime.py").is_file())


if __name__ == "__main__":
    unittest.main()
