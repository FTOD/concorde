from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


WORKFLOW = REPOSITORY_ROOT / ".github/workflows/publish-release.yml"


def _load(name: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, REPOSITORY_ROOT / "scripts/release" / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleasePointerContractTests(unittest.TestCase):
    def test_builder_writes_complete_deterministic_native_pointer(self):
        builder = _load("build-release.py", "concorde_release_builder_pointer")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            first = builder.build_release(output)
            pointer = json.loads((output / "release.json").read_text())
            self.assertEqual(pointer["repository"], builder.REPOSITORY)
            self.assertEqual(pointer["architecture_profile"], 7)
            self.assertEqual(pointer["workspace_protocol"], 13)
            self.assertEqual(pointer["tag"], "v" + pointer["version"])
            self.assertTrue(pointer["archive"]["url"].endswith("/" + pointer["archive"]["name"]))
            self.assertEqual(pointer["archive"]["sha256"], first[pointer["archive"]["name"]])
            self.assertFalse({"published_at", "updated_at", "catalogs", "bundle_id"} & set(pointer))
            second = builder.build_release(output)
            self.assertEqual(second, first)


class PublishWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text()

    def test_workflow_triggers_on_tags_and_dry_run_dispatch(self):
        self.assertIn('tags: ["v*"]', self.workflow)
        self.assertIn("dry_run:", self.workflow)
        self.assertIn("default: true", self.workflow)

    def test_workflow_has_release_permission_and_serialization(self):
        self.assertIn("contents: write", self.workflow)
        self.assertIn("group: release-${{ github.ref }}", self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)

    def test_workflow_tests_builds_verifies_then_publishes_native_assets(self):
        positions = [
            self.workflow.index("Run unit tests"),
            self.workflow.index("Run release contract tests"),
            self.workflow.index("Build standalone release"),
            self.workflow.index("Verify release"),
            self.workflow.index("Publish release"),
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("scripts/release/build-release.py", self.workflow)
        self.assertIn("scripts/release/verify-release.py", self.workflow)
        self.assertIn("scripts/release/publish-release.py", self.workflow)
        self.assertNotIn("build-components.py", self.workflow)
        self.assertNotIn("--clobber", self.workflow)


if __name__ == "__main__":
    unittest.main()
