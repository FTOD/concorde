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

from concorde.understanding.validate import validate_project  # noqa: E402
from concorde.capabilities.validation import (  # noqa: E402
    capability_source_paths,
    validate_capabilities,
)


PACKAGE_ROOTS = ["agent-assets", "docsite", "operations", "scripts", "skills", "src", "templates"]


def write_capabilities(root: Path) -> None:
    manifest = {
        "schema_version": 2,
        "name": "concorde",
        "package_roots": PACKAGE_ROOTS,
        "skills": ["concorde-alpha", "concorde-beta"],
        "operations": ["concorde-inner", "concorde-loop"],
    }
    (root / "concorde.json").write_text(json.dumps(manifest), encoding="utf-8")
    for directory in PACKAGE_ROOTS:
        (root / directory).mkdir(exist_ok=True)
    for name in manifest["skills"]:
        directory = root / "skills" / name
        directory.mkdir()
        (directory / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Leaf {name}.\nexposure: public\n"
            "effects:\n  reads:\n    - selected-feature\n  writes: []\n"
            "  network: false\n  credentials: none\n---\n\n"
            f"# {name}\n\nLeaf body.\n",
            encoding="utf-8",
        )
    inner = root / "operations/concorde-inner"
    inner.mkdir()
    (inner / "SKILL.md").write_text(
        "---\nname: concorde-inner\ndescription: Inner operation.\nexposure: public\n"
        "operation: operation.py\ncapabilities:\n  - concorde-alpha\n  - concorde-beta\n"
        "---\n\n# Inner\n\n{OPERATION}\n",
        encoding="utf-8",
    )
    (inner / "operation.py").write_text(
        "OPERATION_CAPABILITIES = ('concorde-alpha', 'concorde-beta')\n"
        "OPERATION_STAGES = (('one', ('concorde-alpha',)), ('two', ('concorde-beta',)))\n"
        "OPERATION_BINDINGS = (('one', 0, 'concorde-alpha', 'reader'), ('two', 0, 'concorde-beta', 'reader'))\n"
        "def make(build_operation, launch_factory):\n"
        "    return build_operation(None, 'concorde-inner', OPERATION_STAGES, OPERATION_BINDINGS, None, launch_factory=launch_factory)\n",
        encoding="utf-8",
    )
    operation = root / "operations/concorde-loop"
    operation.mkdir()
    (operation / "SKILL.md").write_text(
        "---\nname: concorde-loop\ndescription: Test operation.\nexposure: public\n"
        "operation: operation.py\ncapabilities:\n  - concorde-inner\n  - concorde-alpha\n"
        "---\n\n# Loop\n\n{OPERATION}\n",
        encoding="utf-8",
    )
    (operation / "operation.py").write_text(
        "OPERATION_CAPABILITIES = ('concorde-inner', 'concorde-alpha')\n"
        "OPERATION_STAGES = (('one', ('concorde-inner',)), ('two', ('concorde-alpha',)))\n"
        "OPERATION_BINDINGS = (('one', 0, 'concorde-inner', 'planner'), ('two', 0, 'concorde-alpha', 'reader'))\n"
        "def make(build_operation, launch_factory, nested_dispatcher):\n"
        "    return build_operation(None, 'concorde-loop', OPERATION_STAGES, OPERATION_BINDINGS, None, launch_factory=launch_factory, nested_dispatcher=nested_dispatcher)\n",
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
            skill.write_text(skill.read_text().replace("concorde-alpha", "concorde-missing"), encoding="utf-8")
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-OPERATION-003", rules)
            self.assertIn("CONCORDE-OPERATION-002", rules)

    def test_direct_and_indirect_operation_cycles_report_exact_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            loop_skill = root / "operations/concorde-loop/SKILL.md"
            loop_python = root / "operations/concorde-loop/operation.py"
            loop_skill.write_text(
                loop_skill.read_text().replace("  - concorde-inner\n", "  - concorde-loop\n"),
                encoding="utf-8",
            )
            loop_python.write_text(
                loop_python.read_text().replace("'concorde-inner'", "'concorde-loop'"),
                encoding="utf-8",
            )
            findings = validate_capabilities(self.package(root))
            self.assertTrue(any(
                finding.rule_id == "CONCORDE-OPERATION-CYCLE-001"
                and "concorde-loop -> concorde-loop" in finding.message
                for finding in findings
            ))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            inner_skill = root / "operations/concorde-inner/SKILL.md"
            inner_python = root / "operations/concorde-inner/operation.py"
            inner_skill.write_text(
                inner_skill.read_text().replace("  - concorde-alpha\n", "  - concorde-loop\n"),
                encoding="utf-8",
            )
            inner_python.write_text(
                inner_python.read_text().replace("'concorde-alpha'", "'concorde-loop'"),
                encoding="utf-8",
            )
            findings = validate_capabilities(self.package(root))
            self.assertTrue(any(
                finding.rule_id == "CONCORDE-OPERATION-CYCLE-001"
                and "concorde-inner -> concorde-loop -> concorde-inner" in finding.message
                for finding in findings
            ))

    def test_internal_exposure_is_valid_only_for_leaf_skills(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            operation = root / "operations/concorde-loop/SKILL.md"
            operation.write_text(
                operation.read_text().replace("exposure: public", "exposure: internal"),
                encoding="utf-8",
            )
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-CAPABILITY-EXPOSURE-001", rules)

    def test_policy_bindings_cover_each_capability_occurrence_exactly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            operation = root / "operations/concorde-loop/operation.py"
            operation.write_text(
                operation.read_text().replace(
                    "OPERATION_BINDINGS = (('one', 0, 'concorde-inner', 'planner'), ('two', 0, 'concorde-alpha', 'reader'))",
                    "OPERATION_BINDINGS = (('one', 0, 'concorde-inner', 'planner'),)",
                ),
                encoding="utf-8",
            )
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-OPERATION-POLICY-001", rules)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            leaf = root / "skills/concorde-alpha/SKILL.md"
            text = leaf.read_text(encoding="utf-8")
            start = text.index("effects:\n")
            end = text.index("---\n", start)
            leaf.write_text(text[:start] + text[end:], encoding="utf-8")
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-SKILL-EFFECTS-001", rules)

    def test_operation_builders_require_leaf_launch_and_nested_dispatch_enforcement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            inner = root / "operations/concorde-inner/operation.py"
            inner.write_text(
                inner.read_text().replace(", launch_factory=launch_factory", ""),
                encoding="utf-8",
            )
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
            self.assertIn("CONCORDE-OPERATION-002", rules)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_capabilities(root)
            outer = root / "operations/concorde-loop/operation.py"
            outer.write_text(
                outer.read_text().replace(", nested_dispatcher=nested_dispatcher", ""),
                encoding="utf-8",
            )
            rules = {finding.rule_id for finding in validate_capabilities(self.package(root))}
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
