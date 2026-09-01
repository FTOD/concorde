"""Profile 7 architecture-owned diagram declaration and presentation rules."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.context import bounded_context  # noqa: E402
from concorde.readiness import architecture_readiness  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


LEVEL_VIEW = "specs/example/diagrams/level-view.json"


class ModuleDiagramRuleTests(unittest.TestCase):
    def copy(self, temporary: str, fixture: Path = VALID_PROJECT) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(fixture, root)
        return root

    def test_diagrams_are_declared_and_linked_only_from_architecture(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(temporary)
            architecture = root / "specs/example/architecture.md"
            architecture.write_text(architecture.read_text(encoding="utf-8").replace("[level-view.json](diagrams/level-view.json)", "the level view"), encoding="utf-8")
            result = validate_project(root)
            self.assertIn("CONCORDE-VIEW-006", {item.rule_id for item in result.findings})
            architecture.write_text(architecture.read_text(encoding="utf-8") + "\n[view](diagrams/level-view.json)\n", encoding="utf-8")
            self.assertNotIn("CONCORDE-VIEW-006", {item.rule_id for item in validate_project(root).findings})

    def test_undeclared_diagram_and_kind_disagreement_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(temporary)
            extra = root / "specs/example/diagrams/release.json"
            extra.write_text(json.dumps({"schema_version": 1, "diagram_type": "sequence", "meta": {"title": "Release", "legend": {"mode": "hidden"}}, "participants": [], "messages": []}), encoding="utf-8")
            architecture = root / "specs/example/architecture.md"
            architecture.write_text(architecture.read_text(encoding="utf-8") + "\n[release](diagrams/release.json)\n", encoding="utf-8")
            self.assertIn("CONCORDE-VIEW-009", {item.rule_id for item in validate_project(root).findings})
            text = architecture.read_text(encoding="utf-8").replace(
                "    output: generated/architecture/example.html",
                "    output: generated/architecture/example.html\n  - source: diagrams/release.json\n    kind: architecture\n    output: generated/architecture/release.html",
            )
            architecture.write_text(text, encoding="utf-8")
            rules = {item.rule_id for item in validate_project(root).findings}
            self.assertIn("CONCORDE-VIEW-008", rules)
            self.assertNotIn("CONCORDE-VIEW-009", rules)

    def test_every_architecture_owned_diagram_hides_renderer_legend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(temporary, CONTEXT_PROJECT)
            path = root / LEVEL_VIEW
            value = json.loads(path.read_text(encoding="utf-8"))
            value["meta"]["legend"] = {"mode": "auto"}
            path.write_text(json.dumps(value), encoding="utf-8")
            finding = next(item for item in validate_project(root).findings if item.rule_id == "CONCORDE-VIEW-007")
            self.assertEqual(finding.source, LEVEL_VIEW)

    def test_context_and_readiness_project_architecture_owned_diagrams(self):
        context = bounded_context(CONTEXT_PROJECT, "module.example").result["context"]
        self.assertEqual(context["current_module"]["diagrams"], ["specs/example/diagrams/delivery-sequence.json", LEVEL_VIEW])
        readiness = architecture_readiness(CONTEXT_PROJECT, "feature.example.deliver")
        self.assertEqual(readiness["affected_diagrams"], ["specs/example/diagrams/delivery-sequence.json", LEVEL_VIEW])

    def test_feature_owned_diagrams_are_forbidden_residue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copy(temporary)
            directory = root / "specs/example/features/001-deliver/diagrams"
            directory.mkdir(parents=True)
            (directory / "feature.json").write_text("{}", encoding="utf-8")
            result = validate_project(root)
            finding = next(item for item in result.findings if item.rule_id == "CONCORDE-LAYOUT-006")
            self.assertTrue(finding.source.endswith("/001-deliver"))


if __name__ == "__main__":
    unittest.main()
