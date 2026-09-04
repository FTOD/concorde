from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.managed_runtime import create_langgraph_index, runtime_install_environment


class TemplateWorkflowAcceptance(unittest.TestCase):
    def test_complete_root_templates_ship_byte_identically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = runtime_install_environment(create_langgraph_index(root.parent))
            result = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/install-concorde.py"), "--target", str(root), "--apply", "--format", "json"],
                text=True, capture_output=True, env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            manifest = json.loads((root / ".concorde/framework/concorde.json").read_text())
            for name in manifest["templates"]:
                self.assertEqual(
                    (REPOSITORY_ROOT / "templates" / name).read_bytes(),
                    (root / ".concorde/framework/templates" / name).read_bytes(),
                    name,
                )

    def test_feature_plan_tasks_formats_form_one_native_lifecycle(self):
        feature = (REPOSITORY_ROOT / "templates/feature-template.md").read_text()
        plan = (REPOSITORY_ROOT / "templates/plan-template.md").read_text()
        tasks = (REPOSITORY_ROOT / "templates/tasks-template.md").read_text()
        self.assertIn("## Interfaces", feature)
        self.assertIn("## Architecture Zoom", feature)
        self.assertIn("## User Scenarios & Testing", feature)
        self.assertIn("## Concorde Architecture Gate", plan)
        self.assertIn(".concorde/attempts/<stable-feature-id>", plan)
        self.assertIn("## Concorde Task Coverage", tasks)
        self.assertIn("Evidence Before Completion", tasks)
        for body in (feature, plan, tasks):
            self.assertNotIn(".specify/", body)
            self.assertNotIn("preset resolver", body.lower())


if __name__ == "__main__":
    unittest.main()
