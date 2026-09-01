import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.validate import validate_project  # noqa: E402


class EntityRuleTests(unittest.TestCase):
    def copy(self, temporary: str) -> tuple[Path, Path]:
        root = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, root)
        return root, root / "specs/example/architecture.md"

    def rules(self, root: Path) -> set[str]:
        return {finding.rule_id for finding in validate_project(root).findings}

    def test_duplicate_entity_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, architecture = self.copy(temporary)
            body = architecture.read_text(encoding="utf-8")
            architecture.write_text(body.replace(
                "| `entity.example.runtime` | program |",
                "| `entity.example.runtime` | program |",
            ).replace(
                "## Relationships",
                "| `entity.example.runtime` | service | Duplicate runtime. | `concept:duplicate` |\n\n## Relationships",
            ), encoding="utf-8")
            self.assertIn("CONCORDE-ENTITY-003", self.rules(root))

    def test_undeclared_type_bad_locator_and_unknown_endpoint_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, architecture = self.copy(temporary)
            body = architecture.read_text(encoding="utf-8")
            body = body.replace("| program | The workflow orchestrator", "| spaceship | The workflow orchestrator")
            body = body.replace("`concept:example.runtime`", "`src/missing.py#runtime`")
            body = body.replace("`entity.example.runtime` | calls | `module.example.api`", "`entity.example.missing` | calls | `module.example.api`")
            architecture.write_text(body, encoding="utf-8")
            rules = self.rules(root)
            self.assertTrue({"CONCORDE-ENTITY-005", "CONCORDE-ENTITY-007", "CONCORDE-RELATIONSHIP-003"}.issubset(rules))

    def test_parent_must_expose_child_as_bounded_module_entity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, architecture = self.copy(temporary)
            lines = architecture.read_text(encoding="utf-8").splitlines()
            architecture.write_text("\n".join(line for line in lines if not line.startswith("| `module.example.api` | module |")) + "\n", encoding="utf-8")
            self.assertIn("CONCORDE-ENTITY-008", self.rules(root))

    def test_interaction_requires_typed_trigger_steps_and_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, architecture = self.copy(temporary)
            architecture.write_text(architecture.read_text(encoding="utf-8").replace(
                "`entity.example.maintainer` requests delivery.",
                "",
            ), encoding="utf-8")
            self.assertIn("CONCORDE-INTERACTION-005", self.rules(root))


if __name__ == "__main__":
    unittest.main()
