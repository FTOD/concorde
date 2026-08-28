import json
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class FeatureWorkspaceContractTests(unittest.TestCase):
    def test_examples_share_safe_complete_workspace_shape(self):
        examples = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples"
        for name in ("feature-harden-eligible-response.json",):
            payload = json.loads((examples / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 5)
            self.assertEqual(payload["operation"], "feature.harden")
            self.assertEqual(
                set(payload["workspace"]),
                {
                    "workspace_kind",
                    "feature_id",
                    "providing_module",
                    "parent_context",
                    "siblings",
                    "feature_directory",
                    "feature_tldr",
                    "feature_spec",
                    "feature_design",
                    "module_summary",
                    "module_design",
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
                value for key, value in payload["workspace"].items()
                if key not in {"workspace_kind", "feature_id", "providing_module", "parent_context", "siblings", "implementation_state"}
            )
            for value in (*path_values, *payload["artifacts"]):
                self.assertFalse(Path(value).is_absolute())
                self.assertNotIn("\\", value)
                self.assertNotIn("..", Path(value).parts)
            self.assertEqual(
                payload["workspace"]["checklists_dir"],
                payload["workspace"]["implementation_dir"] + "/checklists",
            )

    def test_schema_keeps_workspace_protocol_separate_from_architecture_v1(self):
        contracts = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts"
        workspace = json.loads((contracts / "feature-workspace.schema.json").read_text())
        architecture = json.loads((contracts / "architecture-service.schema.json").read_text())
        self.assertEqual(workspace["$defs"]["operation"]["enum"], ["feature.harden"])
        self.assertEqual(workspace["$defs"]["request"]["properties"]["schema_version"]["const"], 5)
        self.assertEqual(workspace["$defs"]["response"]["properties"]["schema_version"]["const"], 5)
        self.assertIn("design_digest_before", response_properties := workspace["$defs"]["response"]["properties"])
        self.assertIn("module_design_digest_after", response_properties)
        response_properties = workspace["$defs"]["response"]["properties"]
        self.assertIn("proposal_path", response_properties)
        self.assertIn("task_summary", response_properties)
        self.assertIn("checklist_summary", response_properties)
        self.assertEqual(architecture["$defs"]["operation"]["enum"], ["init", "context", "validate"])

    def test_hardening_proposal_binds_one_realization_optional_reference_and_one_removal_target(self):
        path = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples/feature-harden-proposal.json"
        proposal = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["proposal_version"], 3)
        self.assertEqual(proposal["operation"], "feature.harden")
        realization = Path(proposal["design"]["path"])
        removal = Path(proposal["remove"][0])
        self.assertEqual(realization.name, "design.md")
        self.assertEqual(removal.name, "implementation")
        self.assertEqual(realization.parent, removal.parent)
        self.assertEqual(len(proposal["remove"]), 1)
        reference = Path(proposal["module_design"]["path"])
        self.assertEqual(reference.name, "design.md")
        self.assertNotEqual(reference.parent, realization.parent)
        schema = json.loads((path.parents[1] / "feature-workspace.schema.json").read_text(encoding="utf-8"))
        hardening = schema["$defs"]["hardeningProposal"]
        self.assertEqual(hardening["properties"]["proposal_version"]["const"], 3)
        self.assertIn("design", hardening["required"])
        self.assertNotIn("implementation", hardening["properties"])
        self.assertNotIn("module_design", hardening["required"])

    def test_hardening_eligibility_example_exposes_review_metadata(self):
        path = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples/feature-harden-eligible-response.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "eligible")
        self.assertEqual(
            payload["proposal_path"],
            payload["workspace"]["implementation_dir"] + "/harden-proposal.json",
        )
        self.assertEqual(payload["task_summary"]["incomplete"], 0)
        self.assertEqual(payload["checklist_summary"]["incomplete"], 0)
        self.assertEqual(payload["checklist_summary"]["malformed"], 0)


if __name__ == "__main__":
    unittest.main()
