from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.validate import validate_project  # noqa: E402
from concorde.validation.capabilities import (  # noqa: E402
    capability_source_paths,
    validate_capabilities,
)


PACKAGE_ROOTS = ["agent-assets", "operations", "scripts", "skills", "src", "templates"]


def write_capabilities(root: Path) -> None:
    manifest = {
        "schema_version": 2,
        "name": "concorde",
        "package_roots": PACKAGE_ROOTS,
        "skills": ["concorde-alpha", "concorde-beta"],
        "operations": ["concorde-loop"],
    }
    (root / "concorde.json").write_text(json.dumps(manifest), encoding="utf-8")
    for directory in PACKAGE_ROOTS:
        (root / directory).mkdir(exist_ok=True)
    for name in manifest["skills"]:
        directory = root / "skills" / name
        directory.mkdir()
        (directory / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Leaf {name}.\n---\n\n# {name}\n\nLeaf body.\n",
            encoding="utf-8",
        )
    operation = root / "operations/concorde-loop"
    operation.mkdir()
    (operation / "SKILL.md").write_text(
        "---\nname: concorde-loop\ndescription: Test operation.\noperation: operation.py\n"
        "skills:\n  - concorde-alpha\n  - concorde-beta\n---\n\n# Loop\n\n{OPERATION}\n",
        encoding="utf-8",
    )
    (operation / "operation.py").write_text(
        "OPERATION_SKILLS = ('concorde-alpha', 'concorde-beta')\n"
        "OPERATION_STAGES = (('one', ('concorde-alpha',)), ('two', ('concorde-beta',)))\n"
        "def make(build_operation):\n    return build_operation\n",
        encoding="utf-8",
    )


class CapabilityValidationTests(unittest.TestCase):
    def package(self, root: Path):
        return SimpleNamespace(project_root=root)

    def test_valid_structural_capabilities_are_non_mutating_and_digest_sources_are_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(validate_capabilities(self.package(root)), [])
            self.assertEqual(
                before,
                {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()},
            )
            paths = capability_source_paths(root)
            self.assertIn("concorde.json", paths)
            self.assertIn("skills/concorde-alpha/SKILL.md", paths)
            self.assertIn("operations/concorde-loop/operation.py", paths)

    def test_missing_or_extra_operation_pair_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            (root / "operations/concorde-loop/operation.py").unlink()
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-OPERATION-001", rules)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            (root / "operations/concorde-loop/extra.txt").write_text("extra", encoding="utf-8")
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-OPERATION-001", rules)

    def test_unknown_skills_and_python_markdown_stage_disagreement_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            skill = root / "operations/concorde-loop/SKILL.md"
            skill.write_text(skill.read_text().replace("concorde-beta", "concorde-missing"), encoding="utf-8")
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-OPERATION-003", rules)
            self.assertIn("CONCORDE-OPERATION-002", rules)

    def test_leaf_python_script_langgraph_and_legacy_roots_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            (root / "skills/concorde-alpha/graph.py").write_text("pass\n", encoding="utf-8")
            (root / "scripts/bad.py").write_text("from langgraph.graph import StateGraph\n", encoding="utf-8")
            (root / "commands").mkdir()
            (root / "examples").mkdir()
            rules = [finding.rule_id for finding in validate_capabilities(self.package(root))]
            self.assertIn("CONCORDE-SKILL-001", rules)
            self.assertIn("CONCORDE-SCRIPT-001", rules)
            self.assertEqual(rules.count("CONCORDE-CAPABILITY-LEGACY"), 2)

    def test_consumer_project_needs_no_package_capability_roots(self):
        self.assertEqual(validate_capabilities(self.package(VALID_PROJECT)), [])
        self.assertEqual(capability_source_paths(VALID_PROJECT), ())

    def test_capability_bytes_participate_in_self_validation_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            write_capabilities(root)
            first = validate_project(root)
            self.assertEqual(first.status, "success", first.findings)
            skill = root / "skills/concorde-alpha/SKILL.md"
            skill.write_text(skill.read_text() + "\nChanged capability bytes.\n", encoding="utf-8")
            second = validate_project(root)
            self.assertEqual(second.status, "success", second.findings)
            self.assertNotEqual(first.result["source_digest"], second.result["source_digest"])
            self.assertIn("skills/concorde-alpha/SKILL.md", second.artifacts)


if __name__ == "__main__":
    unittest.main()
