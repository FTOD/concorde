import json
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class FeatureWorkspaceContractTests(unittest.TestCase):
    def test_examples_share_safe_complete_workspace_shape(self):
        examples = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-starter-workflow/contracts/examples"
        for name in ("feature-create-proposal.json", "feature-select-response.json"):
            payload = json.loads((examples / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 2)
            self.assertIn(payload["operation"], {"feature.create", "feature.select"})
            self.assertEqual(
                set(payload["workspace"]),
                {
                    "feature_directory",
                    "feature_spec",
                    "feature_design",
                    "contracts_dir",
                    "checklists_dir",
                    "diagrams_dir",
                    "implementation_dir",
                    "implementation_state",
                    "plan",
                    "research",
                    "data_model",
                    "quickstart",
                    "tasks",
                    "validation",
                },
            )
            path_values = (
                value
                for key, value in payload["workspace"].items()
                if key != "implementation_state"
            )
            for value in (*path_values, *payload["artifacts"]):
                self.assertFalse(Path(value).is_absolute())
                self.assertNotIn("\\", value)
                self.assertNotIn("..", Path(value).parts)

    def test_schema_keeps_workspace_protocol_separate_from_architecture_v1(self):
        contracts = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-starter-workflow/contracts"
        workspace = json.loads((contracts / "feature-workspace.schema.json").read_text())
        architecture = json.loads((contracts / "architecture-service.schema.json").read_text())
        self.assertEqual(workspace["$defs"]["operation"]["enum"], ["feature.create", "feature.select", "feature.harden"])
        self.assertEqual(workspace["$defs"]["request"]["properties"]["schema_version"]["const"], 2)
        self.assertEqual(workspace["$defs"]["response"]["properties"]["schema_version"]["const"], 2)
        self.assertEqual(architecture["$defs"]["operation"]["enum"], ["init", "context", "validate"])

    def test_hardening_proposal_binds_one_design_and_one_removal_target(self):
        path = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-starter-workflow/contracts/examples/feature-harden-proposal.json"
        proposal = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["proposal_version"], 1)
        self.assertEqual(proposal["operation"], "feature.harden")
        design = Path(proposal["design"]["path"])
        removal = Path(proposal["remove"][0])
        self.assertEqual(design.name, "design.md")
        self.assertEqual(removal.name, "implementation")
        self.assertEqual(design.parent, removal.parent)


if __name__ == "__main__":
    unittest.main()
