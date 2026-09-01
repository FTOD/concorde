import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.validate import validate_project  # noqa: E402


class InterfaceRuleTests(unittest.TestCase):
    def copy(self, temporary: str) -> tuple[Path, Path]:
        root = Path(temporary) / "project"
        shutil.copytree(VALID_PROJECT, root)
        return root, root / "specs/example/features/001-deliver.md"

    def test_every_provided_interface_is_embedded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, design = self.copy(temporary)
            design.write_text(design.read_text(encoding="utf-8").replace("### `contract.example.workflow`", "### Workflow"), encoding="utf-8")
            self.assertIn("CONCORDE-INTERFACE-004", {item.rule_id for item in validate_project(root).findings})

    def test_interface_requires_consumer_direction_shapes_failures_and_implementers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, design = self.copy(temporary)
            body = design.read_text(encoding="utf-8")
            for field in ("Consumer", "Failures", "Implementing entities"):
                body = body.replace(f"**{field}**:", f"**Missing {field}**:")
            design.write_text(body, encoding="utf-8")
            finding = next(item for item in validate_project(root).findings if item.rule_id == "CONCORDE-INTERFACE-007")
            self.assertIn("Consumer", finding.message)
            self.assertIn("Failures", finding.message)
            self.assertIn("Implementing entities", finding.message)

    def test_zoom_and_interface_entities_resolve_against_architecture(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, design = self.copy(temporary)
            design.write_text(design.read_text(encoding="utf-8").replace("entity.example.runtime", "entity.example.missing"), encoding="utf-8")
            rules = {item.rule_id for item in validate_project(root).findings}
            self.assertIn("CONCORDE-ZOOM-002", rules)
            self.assertIn("CONCORDE-INTERFACE-009", rules)

    def test_zoom_may_not_redefine_architecture_type(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, design = self.copy(temporary)
            design.write_text(design.read_text(encoding="utf-8").replace(
                "| Entity | Role |\n|---|---|\n| `entity.example.maintainer` |",
                "| Entity | Type | Role |\n|---|---|---|\n| `entity.example.maintainer` | program |",
            ).replace("| `entity.example.runtime` | Orchestrates", "| `entity.example.runtime` | program | Orchestrates").replace("| `module.example.api` | Provides", "| `module.example.api` | module | Provides"), encoding="utf-8")
            self.assertIn("CONCORDE-ZOOM-004", {item.rule_id for item in validate_project(root).findings})

    def test_unresolved_required_interface_needs_explicit_external_provider_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, design = self.copy(temporary)
            body = design.read_text(encoding="utf-8").replace(
                "  required: []",
                "  required:\n    - contract.external.platform",
            )
            design.write_text(body, encoding="utf-8")
            self.assertIn("CONCORDE-INTERFACE-011", {item.rule_id for item in validate_project(root).findings})
            external = """

### `contract.external.platform` — External platform

**Provider**: external:fixture-platform

**Consumer**: delivery runtime

**Direction**: input

**Entry points**: platform workflow

**Inputs**: A platform request.

**Outputs**: A platform result.

**Obligations**: The consumer follows platform requirements.

**Failures**: Platform unavailability is surfaced.

**Compatibility**: The external provider versions its behavior.
"""
            design.write_text(design.read_text(encoding="utf-8").replace("\n## Usage Scenarios", external + "\n## Usage Scenarios"), encoding="utf-8")
            rules = {item.rule_id for item in validate_project(root).findings}
            self.assertNotIn("CONCORDE-INTERFACE-011", rules)
            self.assertNotIn("CONCORDE-INTERFACE-005", rules)


if __name__ == "__main__":
    unittest.main()
