import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from tests.concorde.support.paths import REPOSITORY_ROOT


WORKSPACE_FIXTURES = REPOSITORY_ROOT / "tests/concorde/fixtures/interfaces/workspace"


class DeliveryTerminologyContractTests(unittest.TestCase):
    def test_workspace_interface_is_protocol12_and_proposal8(self):
        schema = json.loads((WORKSPACE_FIXTURES / "feature-workspace.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["$defs"]["deliveryResponse"]["properties"]["schema_version"]["const"], 12)
        self.assertEqual(schema["$defs"]["deliveryProposal"]["properties"]["proposal_version"]["const"], 8)
        self.assertEqual(
            set(schema["$defs"]["deliveryProposal"]["required"]),
            {"proposal_version", "operation", "target", "source_digest", "remove"},
        )

    def test_examples_validate_and_proposal_contains_no_narrative_updates(self):
        schema = json.loads((WORKSPACE_FIXTURES / "feature-workspace.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        for name in ("deliver-eligible-response.json", "deliver-proposal.json"):
            value = json.loads((WORKSPACE_FIXTURES / name).read_text(encoding="utf-8"))
            self.assertEqual(list(validator.iter_errors(value)), [], name)
        proposal = json.loads((WORKSPACE_FIXTURES / "deliver-proposal.json").read_text(encoding="utf-8"))
        for forbidden in ("content", "updates", "files", "module_" + "design", "implementation"):
            self.assertNotIn(forbidden, proposal)

    def test_eligible_response_retains_design_architecture_and_executable_digests(self):
        value = json.loads((WORKSPACE_FIXTURES / "deliver-eligible-response.json").read_text(encoding="utf-8"))
        self.assertEqual(value["schema_version"], 12)
        self.assertEqual(value["proposal_version"], 8)
        self.assertEqual(value["changes"], [{
            "path": value["workspace"]["attempt_dir"],
            "action": "delete",
            "meaning": "Remove the complete temporal attempt; retain every durable and executable authority.",
        }])
        self.assertEqual(value["evidence_summary"]["missing"], 0)
        self.assertIn(value["workspace"]["feature_path"], value["retained_digests"])
        self.assertIn(value["workspace"]["module_architecture"], value["retained_digests"])
        self.assertIn(value["workspace"]["reflections"], value["retained_digests"])
        self.assertIn("executable_context", value["retained_digests"])

    def test_runtime_and_guidance_use_cleanup_only_delivery_language(self):
        runtime = (REPOSITORY_ROOT / "src/concorde/delivery.py").read_text(encoding="utf-8")
        command = (REPOSITORY_ROOT / "commands/concorde.deliver.md").read_text(encoding="utf-8")
        readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Delivery Proposal 8", runtime)
        self.assertIn("proposal.get(\"proposal_version\") != 8", runtime)
        self.assertIn("cleanup-only", runtime)
        self.assertIn("cleanup-only", command)
        self.assertIn("cleanup-only", readme)
        self.assertIn("remove exactly", readme)
        for body in (command, readme):
            self.assertNotIn("accepted realization", body.lower())

    def test_interface_fixtures_live_outside_specification_hierarchy(self):
        expected = {
            "architecture-service.schema.json",
            "context-response.json",
            "deliver-eligible-response.json",
            "deliver-proposal.json",
            "feature-workspace.schema.json",
            "validation-response.json",
        }
        self.assertEqual({path.name for path in WORKSPACE_FIXTURES.glob("*.json")}, expected)
        for path in WORKSPACE_FIXTURES.glob("*.json"):
            self.assertNotIn("/specs/", path.as_posix())


if __name__ == "__main__":
    unittest.main()
