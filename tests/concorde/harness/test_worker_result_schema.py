"""Profile-specific result tools reject unauthorized data before ending a worker."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from concorde.harness.pi_worker import PiWorkerRuntime, WorkerLaunch
from concorde.harness.worker_executor import result_parameters, worker_result_parameters
from concorde.harness.worker_profile import (
    RESULT_FIELDS,
    ContractError,
    load_worker_profiles,
    validate_worker_output,
    worker_profile,
)
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.harness.test_pi_worker import installed_pi
from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider
from tests.concorde.support.paths import REPOSITORY_ROOT


def stage_result():
    return {
        "context_id": "sha256:" + "0" * 64,
        "outcome": "completed",
        "answer": "A test submission, not evidence of semantic correctness.",
        "blockers": [],
        "documents": [],
        "plan": "",
        "tasks": [],
    }


def issue_decision():
    return {
        "action": "needs-decision",
        "intent": "Decide the scope",
        "rationale": "An external grant is missing",
        "duplicate_of": None,
    }


class WorkerResultSchemaTests(unittest.TestCase):
    @verifies("scenario.harness.worker-contract", "scenario.harness.execute-failure")
    def test_planner_cannot_submit_an_issue_solver_decision(self):
        profile = worker_profile("planner")
        broad = result_parameters(profile.contract.result)
        narrowed = worker_result_parameters(profile)
        valid = stage_result()
        invalid = {**valid, "issue_decision": issue_decision()}
        # Regression: this passes the shared wire type, but not this worker's authority.
        Draft202012Validator(broad).validate(invalid)
        with self.assertRaises(ContractError) as rejected:
            validate_worker_output(profile, typed(profile.contract.result, invalid))
        self.assertEqual("permission_denied", rejected.exception.code)
        self.assertNotIn("issue_decision", narrowed["properties"])
        self.assertFalse(Draft202012Validator(narrowed).is_valid(invalid))
        self.assertFalse(
            Draft202012Validator(narrowed).is_valid({**valid, "issue_decision": None})
        )
        Draft202012Validator(narrowed).validate(valid)
        validate_worker_output(profile, typed(profile.contract.result, valid))
        authored = {
            **valid,
            "plan": "An authorized implementation plan",
        }
        Draft202012Validator(narrowed).validate(authored)
        validate_worker_output(profile, typed(profile.contract.result, authored))
        for field, value in (
            ("documents", [{"path": "specs/service/module.md", "content": "# Spec\n"}]),
            (
                "tasks",
                [
                    {
                        "id": "task.x",
                        "target_id": "module.service",
                        "description": "d",
                        "acceptance": "a",
                        "complete": False,
                    }
                ],
            ),
        ):
            with self.subTest(field=field):
                self.assertFalse(
                    Draft202012Validator(narrowed).is_valid({**valid, field: value})
                )

    @verifies("scenario.harness.worker-contract")
    def test_all_profiles_narrow_only_unauthorized_fields_without_mutating_wire_types(
        self,
    ):
        empty = {
            "documents": [],
            "plan": "",
            "tasks": [],
            "routes": [],
            "topology_design": None,
        }
        for name, profile in load_worker_profiles().items():
            with self.subTest(worker=name):
                broad = result_parameters(profile.contract.result)
                before = copy.deepcopy(broad)
                narrowed = worker_result_parameters(profile)
                Draft202012Validator.check_schema(narrowed)
                self.assertFalse(narrowed["additionalProperties"])
                self.assertEqual(broad["required"], narrowed["required"])
                for field, schema in broad["properties"].items():
                    if (
                        field not in RESULT_FIELDS
                        or field in profile.contract.output_fields
                    ):
                        self.assertEqual(schema, narrowed["properties"][field])
                    elif field not in broad["required"]:
                        self.assertNotIn(field, narrowed["properties"])
                    else:
                        actual = narrowed["properties"][field]
                        self.assertEqual(empty[field], actual["const"])
                        Draft202012Validator(actual).validate(empty[field])
                self.assertEqual(before, result_parameters(profile.contract.result))
                self.assertEqual(narrowed, worker_result_parameters(profile))

    @verifies("scenario.harness.worker-contract")
    def test_issue_solver_retains_its_decision_and_no_other_authored_fields(self):
        profile = worker_profile("issue_solver")
        schema = worker_result_parameters(profile)
        valid = {**stage_result(), "issue_decision": issue_decision()}
        Draft202012Validator(schema).validate(valid)
        validate_worker_output(profile, typed(profile.contract.result, valid))
        self.assertFalse(
            Draft202012Validator(schema).is_valid({**valid, "plan": "Unauthorized"})
        )

    @unittest.skipUnless(installed_pi(), "the pi executable is not installed")
    @verifies("scenario.harness.pi-worker-launch", "scenario.harness.worker-contract")
    def test_real_pi_rejects_invalid_submission_and_accepts_correction_in_same_run(
        self,
    ):
        pi = installed_pi()
        assert pi is not None
        profile = worker_profile("context_assessor")
        valid = {**stage_result(), "outcome": "sufficient"}
        turns = [
            {
                "tool": "submit_result",
                "arguments": {**valid, "issue_decision": issue_decision()},
            },
            {"tool": "submit_result", "arguments": {**valid, "plan": "Unauthorized"}},
            {"tool": "submit_result", "arguments": valid},
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace, credentials = root / "workspace", root / "credentials"
            workspace.mkdir()
            credentials.mkdir()
            with FakeOpenAIProvider(turns) as provider:
                (credentials / "models.json").write_text(
                    json.dumps(
                        {
                            "providers": {
                                "fake": {
                                    "baseUrl": provider.base_url,
                                    "api": "openai-completions",
                                    "apiKey": "fake-test-key",
                                    "compat": {
                                        "supportsDeveloperRole": False,
                                        "supportsReasoningEffort": False,
                                    },
                                    "models": [{"id": "fake-model"}],
                                }
                            }
                        }
                    )
                )
                runtime = PiWorkerRuntime(
                    REPOSITORY_ROOT,
                    pi_executable=pi,
                    credentials_dir=credentials,
                    environment={
                        "HOME": str(root),
                        "LANG": "C.UTF-8",
                        "PATH": f"{Path(pi).parent}:/usr/bin:/bin",
                    },
                )
                launch = WorkerLaunch(
                    worker=profile.name,
                    workspace=str(workspace),
                    system_prompt="Submit the scripted test result.",
                    message="Offline submission test.",
                    result_schema=worker_result_parameters(profile),
                    tools=("submit_result",),
                    model="fake/fake-model",
                    timeout_seconds=60,
                )
                result = runtime(launch)
            self.assertEqual(valid, result.value)
            submissions = result.run.results_of("submit_result")
            self.assertEqual(
                [True, True, False], [bool(item.get("isError")) for item in submissions]
            )
            self.assertEqual(3, len(provider.requests))
            advertised = next(
                tool["function"]["parameters"]
                for tool in provider.requests[0]["tools"]
                if tool["function"]["name"] == "submit_result"
            )
            self.assertEqual(launch.result_schema, advertised)
            validate_worker_output(
                profile, typed(profile.contract.result, result.value)
            )


if __name__ == "__main__":
    unittest.main()
