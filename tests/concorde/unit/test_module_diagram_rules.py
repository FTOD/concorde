"""Profile 4 layout and module-diagram rules: architecture/diagrams/, architecture/contracts/, architecture/modules/."""

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


LEVEL_VIEW = "specs/example/architecture/diagrams/level-view.json"
RELEASE_FLOW = "specs/example/architecture/diagrams/release-flow.json"


def rules(result) -> list[str]:
    return [item.rule_id for item in result.findings]


def finding(result, rule: str):
    return next(item for item in result.findings if item.rule_id == rule)


class ModuleDiagramRuleTests(unittest.TestCase):
    def project_copy(self, temporary: str, fixture: Path = VALID_PROJECT) -> Path:
        root = Path(temporary) / "project"
        shutil.copytree(fixture, root)
        return root

    def add_release_flow(self, root: Path, link_from: str | None) -> None:
        (root / RELEASE_FLOW).write_text(json.dumps({
            "schema_version": 1,
            "diagram_type": "sequence",
            "meta": {
                "title": "Release flow",
                "legend": {"mode": "hidden"},
                "views": [{"id": "scenario.example.release", "label": "Release", "focus": []}],
            },
        }), encoding="utf-8")
        if link_from == "design":
            design = root / "specs/example/design.md"
            design.write_text(design.read_text(encoding="utf-8") + "\n\nThe [release flow](architecture/diagrams/release-flow.json) explains publication order.\n", encoding="utf-8")
        elif link_from == "reflections":
            (root / "specs/example/reflections.md").write_text(
                "# Reflections: Example\n\nSee the [release flow](architecture/diagrams/release-flow.json).\n", encoding="utf-8"
            )

    def test_every_module_diagram_must_be_referenced_from_the_level_documents(self):
        for link_from, expected in (("design", []), ("reflections", []), (None, ["CONCORDE-VIEW-006"])):
            with self.subTest(link_from=link_from), tempfile.TemporaryDirectory() as temporary:
                root = self.project_copy(temporary)
                self.add_release_flow(root, link_from)
                result = validate_project(root)
                self.assertEqual([rule for rule in rules(result) if rule == "CONCORDE-VIEW-006"], expected)
                if expected:
                    unreferenced = finding(result, "CONCORDE-VIEW-006")
                    self.assertEqual(unreferenced.source, RELEASE_FLOW)
                    self.assertEqual(unreferenced.subject_id, "module.example")
                    self.assertEqual(result.status, "invalid")
                else:
                    self.assertEqual(result.status, "success", result.findings)

    def test_a_second_diagram_joins_context_readiness_and_scenario_visibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            self.add_release_flow(root, "design")
            design = root / "specs/example/features/001-deliver/design.md"
            design.write_text(design.read_text(encoding="utf-8").replace(
                "scenarios:\n  - scenario.example.deliver", "scenarios:\n  - scenario.example.deliver\n  - scenario.example.release"
            ), encoding="utf-8")
            self.assertNotIn("CONCORDE-SCENARIO-004", rules(validate_project(root)))
            context = bounded_context(root, "module.example")
            self.assertEqual(context.result["context"]["current_module"]["diagrams"], [LEVEL_VIEW, RELEASE_FLOW])
            self.assertEqual([item["id"] for item in context.result["context"]["scenarios"]], ["scenario.example.deliver", "scenario.example.release"])
            self.assertIn(RELEASE_FLOW, context.artifacts)
            readiness = architecture_readiness(root, "feature.example.deliver")
            self.assertEqual(readiness["affected_views"], [LEVEL_VIEW, RELEASE_FLOW])

    def test_every_maintained_diagram_must_explicitly_hide_its_legend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary, CONTEXT_PROJECT)
            module_view_path = root / LEVEL_VIEW
            module_view = json.loads(module_view_path.read_text(encoding="utf-8"))
            del module_view["meta"]["legend"]
            module_view_path.write_text(json.dumps(module_view), encoding="utf-8")

            feature_view_path = root / "specs/example/features/001-deliver/diagrams/delivery-sequence.json"
            feature_view = json.loads(feature_view_path.read_text(encoding="utf-8"))
            feature_view["meta"]["legend"] = {"mode": "auto"}
            feature_view_path.write_text(json.dumps(feature_view), encoding="utf-8")

            findings = [
                item for item in validate_project(root).findings if item.rule_id == "CONCORDE-VIEW-007"
            ]
            expected_sources = sorted([LEVEL_VIEW, feature_view_path.relative_to(root).as_posix()])
            self.assertEqual([item.source for item in findings], expected_sources)
            self.assertTrue(all('meta.legend' in item.remediation for item in findings))

    def test_structure_must_link_one_architecture_diagram_but_a_dynamic_diagram_does_not_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            module = root / "specs/example/module.md"
            module.write_text(module.read_text(encoding="utf-8").replace(
                "[level-view.json](architecture/diagrams/level-view.json)", "the level view"
            ), encoding="utf-8")
            design = root / "specs/example/design.md"
            design.write_text(design.read_text(encoding="utf-8") + "\n\nSee the [level view](architecture/diagrams/level-view.json).\n", encoding="utf-8")
            result = validate_project(root)
            self.assertIn("CONCORDE-SUMMARY-002", rules(result))
            self.assertNotIn("CONCORDE-VIEW-006", rules(result))

    def test_immediate_children_may_be_spread_over_several_level_views(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary, CONTEXT_PROJECT)
            view_path = root / LEVEL_VIEW
            view = json.loads(view_path.read_text(encoding="utf-8"))
            api = next(item for item in view["components"] if item.get("module_id") == "module.example.api")
            view["components"].remove(api)
            view["connections"] = []
            view_path.write_text(json.dumps(view), encoding="utf-8")
            self.assertIn("CONCORDE-VIEW-003", rules(validate_project(root)))
            second = root / "specs/example/architecture/diagrams/api-view.json"
            second.write_text(json.dumps({
                "schema_version": 1,
                "diagram_type": "architecture",
                "meta": {"title": "API", "legend": {"mode": "hidden"}},
                "components": [api], "connections": [],
            }), encoding="utf-8")
            module = root / "specs/example/module.md"
            module.write_text(module.read_text(encoding="utf-8").replace(
                "[level-view.json](architecture/diagrams/level-view.json)",
                "[level-view.json](architecture/diagrams/level-view.json) and [api-view.json](architecture/diagrams/api-view.json)",
            ), encoding="utf-8")
            result = validate_project(root)
            self.assertNotIn("CONCORDE-VIEW-003", rules(result))
            self.assertNotIn("CONCORDE-VIEW-005", rules(result))
            grandchild = {"id": "store", "type": "database", "module_id": "module.example.api.store"}
            second.write_text(json.dumps({
                "schema_version": 1,
                "diagram_type": "architecture",
                "meta": {"title": "API", "legend": {"mode": "hidden"}},
                "components": [api, grandchild], "connections": [],
            }), encoding="utf-8")
            deep = finding(validate_project(root), "CONCORDE-VIEW-002")
            self.assertIn("api-view.json", deep.message)

    def test_non_leaf_module_without_architecture_diagram_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            (root / LEVEL_VIEW).unlink()
            module = root / "specs/example/module.md"
            module.write_text(module.read_text(encoding="utf-8").replace(
                "The level view is [level-view.json](architecture/diagrams/level-view.json).", "No level view is maintained yet."
            ), encoding="utf-8")
            self.assertIn("CONCORDE-VIEW-001", rules(validate_project(root)))

    def test_invalid_module_diagram_json_is_a_source_finding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            (root / RELEASE_FLOW).write_text('{"diagram_type": "mindmap", "meta": {"title": "x"}}', encoding="utf-8")
            result = validate_project(root)
            self.assertEqual(rules(result), ["CONCORDE-SOURCE-001"])
            self.assertIn("release-flow.json", result.findings[0].message)

    def test_legacy_module_layout_is_reported_with_the_new_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            (root / "specs/example/architecture.json").write_text("{}", encoding="utf-8")
            (root / "specs/example/modules").mkdir()
            module = root / "specs/example/module.md"
            module.write_text(module.read_text(encoding="utf-8").replace("parent: null\n", "parent: null\nview: specs/example/architecture.json\n"), encoding="utf-8")
            design = root / "specs/example/features/001-deliver/design.md"
            design.write_text(design.read_text(encoding="utf-8").replace("evidence_status: unknown\n", "evidence_status: unknown\narchitecture_view: specs/example/architecture.json\n"), encoding="utf-8")
            result = validate_project(root)
            legacy = [item for item in result.findings if item.rule_id == "CONCORDE-LAYOUT-010"]
            self.assertEqual(
                sorted(item.source for item in legacy),
                sorted(["specs/example/architecture.json", "specs/example/modules", "specs/example/module.md", "specs/example/features/001-deliver/design.md"]),
            )
            for item in legacy:
                self.assertIn("architecture/", item.remediation)
            self.assertEqual(result.status, "invalid")

    def test_child_module_must_live_under_the_parents_architecture_modules_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.project_copy(temporary)
            shutil.move(str(root / "specs/example/architecture/modules/api"), str(root / "specs/example/api"))
            for path in (root / "specs/example/api").rglob("*.md"):
                path.write_text(path.read_text(encoding="utf-8").replace("specs/example/architecture/modules/api/", "specs/example/api/"), encoding="utf-8")
            result = validate_project(root)
            misplaced = finding(result, "CONCORDE-LAYOUT-011")
            self.assertEqual(misplaced.source, "specs/example/api/module.md")
            self.assertIn("specs/example/architecture/modules/", misplaced.remediation)
            self.assertNotIn("CONCORDE-LAYOUT-010", rules(result))


if __name__ == "__main__":
    unittest.main()
