import json
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class FeatureWorkspaceContractTests(unittest.TestCase):
    def test_examples_share_safe_complete_workspace_shape(self):
        examples = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-starter-workflow/contracts/examples"
        for name in ("feature-create-proposal.json", "feature-select-response.json"):
            payload = json.loads((examples / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertIn(payload["operation"], {"feature.create", "feature.select"})
            self.assertEqual(
                set(payload["workspace"]),
                {"feature_directory", "feature_spec", "implementation_dir", "plan", "tasks"},
            )
            for value in (*payload["workspace"].values(), *payload["artifacts"]):
                self.assertFalse(Path(value).is_absolute())
                self.assertNotIn("\\", value)
                self.assertNotIn("..", Path(value).parts)

    def test_schema_keeps_workspace_protocol_separate_from_architecture_v1(self):
        contracts = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-starter-workflow/contracts"
        workspace = json.loads((contracts / "feature-workspace.schema.json").read_text())
        architecture = json.loads((contracts / "architecture-service.schema.json").read_text())
        self.assertEqual(workspace["$defs"]["operation"]["enum"], ["feature.create", "feature.select"])
        self.assertEqual(architecture["$defs"]["operation"]["enum"], ["init", "context", "validate"])


if __name__ == "__main__":
    unittest.main()
