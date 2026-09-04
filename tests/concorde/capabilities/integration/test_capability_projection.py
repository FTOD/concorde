from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.skill_assets import (  # noqa: E402
    SkillAssetError,
    render_capabilities,
    render_skill,
)


class CapabilityProjectionIntegrationTests(unittest.TestCase):
    def test_leaf_skills_and_operations_render_for_both_integrations(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        for integration in ("codex", "claude"):
            with self.subTest(integration=integration):
                rendered = render_capabilities(REPOSITORY_ROOT, integration, "")
                self.assertEqual(len(rendered), 18)
                self.assertTrue(
                    all('author: "concorde"' in content for content in rendered.values())
                )
                self.assertEqual(
                    sum('kind: "operation"' in content for content in rendered.values()),
                    3,
                )
                self.assertFalse(any("concorde-plan-context" in path or "concorde-plan-author" in path for path in rendered))
                self.assertTrue(all(".specify/" not in content for content in rendered.values()))

    def test_source_and_installed_prefixes_change_paths_not_skill_intent(self):
        skill = REPOSITORY_ROOT / "operations/concorde-plan/SKILL.md"
        source = render_skill(skill, "codex", "", kind="operation")
        installed = render_skill(skill, "codex", ".concorde/framework", kind="operation")
        self.assertIn(
            "python3 scripts/run-operation.py operations/concorde-plan/operation.py",
            source,
        )
        self.assertIn(
            "python3 .concorde/framework/scripts/run-operation.py "
            ".concorde/framework/operations/concorde-plan/operation.py",
            installed,
        )
        for marker in ("context", "author", "permission"):
            self.assertIn(marker, source)
            self.assertIn(marker, installed)

    def test_operation_projection_resolves_paired_installed_python(self):
        operation = REPOSITORY_ROOT / "operations/concorde-standard-dev-loop/SKILL.md"
        source = render_skill(operation, "codex", "", kind="operation")
        installed = render_skill(
            operation, "codex", ".concorde/framework", kind="operation"
        )
        self.assertIn(
            "python3 scripts/run-operation.py "
            "operations/concorde-standard-dev-loop/operation.py",
            source,
        )
        self.assertIn(
            "python3 .concorde/framework/scripts/run-operation.py "
            ".concorde/framework/operations/concorde-standard-dev-loop/operation.py",
            installed,
        )
        self.assertIn('kind: "operation"', installed)
        self.assertIn(
            'entrypoint: ".concorde/framework/operations/concorde-standard-dev-loop/operation.py"',
            installed,
        )

    def test_feature_template_is_complete_and_not_a_fragment(self):
        body = (REPOSITORY_ROOT / "templates/feature-template.md").read_text()
        for section in (
            "# Feature Design",
            "## Outcome and Scope",
            "## Usage",
            "## User Scenarios & Testing",
            "## Interfaces",
            "## Architecture Zoom",
            "## Related Features",
            "## Requirements",
            "## Success Criteria",
        ):
            self.assertIn(section, body)
        self.assertTrue(body.startswith("---\n"))
        self.assertNotIn("append", body.lower())

    def test_invalid_skill_name_heading_or_operation_pair_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid = root / "invalid/SKILL.md"
            invalid.parent.mkdir()
            invalid.write_text("---\nname: invalid\ndescription: Invalid\n---\n\n# Invalid\n")
            with self.assertRaisesRegex(SkillAssetError, "invalid Concorde capability path"):
                render_skill(invalid, "codex")
            missing_heading = root / "concorde-invalid/SKILL.md"
            missing_heading.parent.mkdir()
            missing_heading.write_text(
                "---\nname: concorde-invalid\ndescription: Invalid\n---\n\nBody.\n"
            )
            with self.assertRaisesRegex(SkillAssetError, "level-one heading"):
                render_skill(missing_heading, "codex")
            missing_heading.write_text(
                "---\nname: concorde-invalid\ndescription: Invalid\n"
                "operation: graph.py\ncapabilities: [\"concorde-plan\", \"concorde-tasks\"]\n"
                "---\n\n# Invalid\n\nRun {OPERATION}.\n"
            )
            with self.assertRaisesRegex(SkillAssetError, "operation: operation.py"):
                render_skill(missing_heading, "codex", kind="operation")


if __name__ == "__main__":
    unittest.main()
