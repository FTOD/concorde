import json
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT


class FeatureWorkspaceContractTests(unittest.TestCase):
    def test_examples_share_safe_complete_workspace_shape(self):
        examples = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples"
        for name in ("feature-accept-eligible-response.json",):
            payload = json.loads((examples / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 7)
            self.assertEqual(payload["operation"], "feature.accept")
            self.assertEqual(
                set(payload["workspace"]),
                {
                    "workspace_kind",
                    "feature_id",
                    "providing_module",
                    "parent_context",
                    "siblings",
                    "feature_directory",
                    "feature_abstract",
                    "feature_design",
                    "feature_implementation",
                    "module_summary",
                    "module_design",
                    "contracts_dir",
                    "checklists_dir",
                    "diagrams_dir",
                    "attempt_dir",
                    "attempt_state",
                    "plan",
                    "research",
                    "data_model",
                    "quickstart",
                    "tasks",
                    "validation",
                    "reflections",
                    "reflections_open",
                },
            )
            path_values = (
                value for key, value in payload["workspace"].items()
                if key not in {"workspace_kind", "feature_id", "providing_module", "parent_context", "siblings", "attempt_state", "reflections_open"}
            )
            for value in (*path_values, *payload["artifacts"]):
                self.assertFalse(Path(value).is_absolute())
                self.assertNotIn("\\", value)
                self.assertNotIn("..", Path(value).parts)
            self.assertEqual(
                payload["workspace"]["checklists_dir"],
                payload["workspace"]["attempt_dir"] + "/checklists",
            )

    def test_schema_keeps_workspace_protocol_separate_from_architecture_v1(self):
        contracts = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts"
        workspace = json.loads((contracts / "feature-workspace.schema.json").read_text())
        architecture = json.loads((contracts / "architecture-service.schema.json").read_text())
        self.assertEqual(workspace["$defs"]["operation"]["enum"], ["feature.accept"])
        self.assertEqual(workspace["$defs"]["request"]["properties"]["schema_version"]["const"], 7)
        self.assertEqual(workspace["$defs"]["response"]["properties"]["schema_version"]["const"], 7)
        self.assertIn("implementation_digest_before", response_properties := workspace["$defs"]["response"]["properties"])
        self.assertIn("module_design_digest_after", response_properties)
        response_properties = workspace["$defs"]["response"]["properties"]
        self.assertIn("proposal_path", response_properties)
        self.assertIn("task_summary", response_properties)
        self.assertIn("checklist_summary", response_properties)
        self.assertEqual(architecture["$defs"]["operation"]["enum"], ["init", "context", "validate"])

    def test_acceptance_proposal_binds_one_realization_optional_reference_and_one_removal_target(self):
        path = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples/feature-accept-proposal.json"
        proposal = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(proposal["proposal_version"], 5)
        self.assertEqual(proposal["operation"], "feature.accept")
        realization = Path(proposal["implementation"]["path"])
        removal = Path(proposal["remove"][0])
        self.assertEqual(realization.name, "implementation.md")
        self.assertEqual(removal.name, "attempt")
        self.assertEqual(realization.parent, removal.parent)
        self.assertEqual(len(proposal["remove"]), 1)
        reference = Path(proposal["module_design"]["path"])
        self.assertEqual(reference.name, "design.md")
        self.assertNotEqual(reference.parent, realization.parent)
        schema = json.loads((path.parents[1] / "feature-workspace.schema.json").read_text(encoding="utf-8"))
        acceptance = schema["$defs"]["acceptanceProposal"]
        self.assertEqual(acceptance["properties"]["proposal_version"]["const"], 5)
        self.assertIn("implementation", acceptance["required"])
        self.assertNotIn("design", acceptance["properties"])
        self.assertNotIn("module_design", acceptance["required"])

    def test_acceptance_eligibility_example_exposes_review_metadata(self):
        path = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/examples/feature-accept-eligible-response.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "eligible")
        self.assertEqual(
            payload["proposal_path"],
            payload["workspace"]["attempt_dir"] + "/accept-proposal.json",
        )
        self.assertEqual(payload["task_summary"]["incomplete"], 0)
        self.assertEqual(payload["checklist_summary"]["incomplete"], 0)
        self.assertEqual(payload["checklist_summary"]["malformed"], 0)

    def test_reflection_fields_are_additive_and_the_proposal_gained_none(self):
        contracts = REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts"
        schema = json.loads((contracts / "feature-workspace.schema.json").read_text(encoding="utf-8"))
        workspace = schema["$defs"]["workspacePaths"]
        self.assertIn("reflections", workspace["properties"])
        self.assertIn("reflections_open", workspace["properties"])
        self.assertNotIn("reflections", workspace["required"])
        self.assertNotIn("reflections_open", workspace["required"])
        self.assertIn("reflections_open", schema["$defs"]["featureSummary"]["properties"])
        self.assertIn("reflection_summary", schema["$defs"]["response"]["properties"])
        self.assertNotIn("reflections", schema["$defs"]["acceptanceProposal"]["properties"])
        payload = json.loads((contracts / "examples/feature-accept-eligible-response.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["reflection_summary"], {"entries": 2, "open": 1, "resolved": 1, "dismissed": 0})
        self.assertEqual(payload["workspace"]["reflections"], "specs/example/reflections.md")
        context = json.loads((contracts / "examples/context-response.json").read_text(encoding="utf-8"))
        self.assertEqual(context["result"]["context"]["reflections"]["path"], "specs/example/reflections.md")
        try:
            import jsonschema
        except ImportError:  # pragma: no cover - dev dependency
            self.skipTest("jsonschema unavailable")
        jsonschema.validate(payload, {**schema, "$ref": "#/$defs/response"})
        proposal = json.loads((contracts / "examples/feature-accept-proposal.json").read_text(encoding="utf-8"))
        jsonschema.validate(proposal, {**schema, "$ref": "#/$defs/acceptanceProposal"})


if __name__ == "__main__":
    unittest.main()
