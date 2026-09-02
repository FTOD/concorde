import json
import unittest

from jsonschema import Draft202012Validator

from tests.concorde.support.paths import REPOSITORY_ROOT


FIXTURES = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/workspace"


class FeatureWorkspaceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((FIXTURES / "feature-workspace.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_delivery_examples_conform_to_protocol12_schema(self):
        for name in ("deliver-eligible-response.json", "deliver-proposal.json"):
            with self.subTest(name=name):
                value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
                self.assertEqual(list(self.validator.iter_errors(value)), [])

    def test_workspace_contains_only_feature_architecture_temporal_process_and_executable_context(self):
        required = set(self.schema["$defs"]["workspace"]["required"])
        self.assertLessEqual({
            "feature_id", "providing_module", "feature_path",
            "module_architecture", "module_ancestry", "related_features", "executable_context",
            "attempt_dir", "attempt_state", "checklists_dir", "plan", "tasks", "validation",
            "reflections", "reflections_open",
        }, required)
        for removed in (
            "workspace_" + "kind",
            "feature_" + "abstract",
            "feature_" + "implementation",
            "module_" + "summary",
            "module_" + "design",
            "contracts_" + "dir",
            "diagrams_" + "dir",
            "parent_" + "context",
            "siblings",
            "feature_" + "directory",
            "feature_" + "design",
        ):
            self.assertNotIn(removed, required)

    def test_workspace_protocol_and_delivery_proposal_versions_are_independent(self):
        response = self.schema["$defs"]["deliveryResponse"]["properties"]
        proposal = self.schema["$defs"]["deliveryProposal"]["properties"]
        self.assertEqual(response["schema_version"]["const"], 12)
        self.assertEqual(proposal["proposal_version"]["const"], 8)
        self.assertEqual(proposal["operation"]["const"], "deliver")

    def test_cleanup_proposal_rejects_content_or_update_surfaces(self):
        proposal = self.schema["$defs"]["deliveryProposal"]
        self.assertFalse(proposal["additionalProperties"])
        self.assertEqual(set(proposal["properties"]), {
            "proposal_version", "operation", "target", "source_digest", "remove",
        })
        self.assertEqual(proposal["properties"]["remove"]["minItems"], 1)
        self.assertEqual(proposal["properties"]["remove"]["maxItems"], 1)

    def test_workspace_adapter_emits_protocol12_and_two_pass_feature_id_preflight(self):
        adapter = (REPOSITORY_ROOT / "scripts/workspace.py").read_text(encoding="utf-8")
        self.assertIn('"schema_version": 12', adapter)
        self.assertIn('parser.add_argument("--feature-id")', adapter)
        self.assertIn("allow_missing_feature=arguments.phase == \"specify\"", adapter)
        self.assertIn("phase_target(paths, arguments.phase)", adapter)

    def test_architecture_service_examples_use_profile7_paths(self):
        schema = json.loads((FIXTURES / "architecture-service.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for name in ("context-response.json", "validation-response.json"):
            value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
            self.assertEqual(list(validator.iter_errors(value)), [], name)
        context = json.loads((FIXTURES / "context-response.json").read_text(encoding="utf-8"))["result"]["context"]
        self.assertTrue(context["current_module"]["architecture"].endswith("/architecture.md"))
        self.assertIn("entities", context["current_module"])
        self.assertIn("relationships", context["current_module"])
        self.assertIn("interactions", context["current_module"])


if __name__ == "__main__":
    unittest.main()
