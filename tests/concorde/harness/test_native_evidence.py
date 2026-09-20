"""Synthetic artifact admission tests, not native publication or model execution proof."""

import json
import tempfile
import unittest
from pathlib import Path

from concorde.harness.native_evidence import NativeChildEvidence, verify_native_children
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies


class NativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.children = []
        self.status = {
            "runId": "workflow-id",
            "mode": "workflow",
            "sessionId": "session-id",
            "state": "running",
            "steps": [],
            "workflow": {"emits": []},
        }
        self.metadata = {}
        self.add_child(0)

    def add_child(self, index):
        key = f"review-{index}"
        identifier = f"invocation-{index}"
        proposal_digest = "sha256:" + f"{index:064x}"
        command = f"trusted-runtime gate {identifier}"
        self.children.append(
            NativeChildEvidence(
                key, "concorde-spec-reviewer", identifier, proposal_digest, command
            )
        )
        self.status["steps"].append(
            {
                "workflowKey": key,
                "runId": f"run-{index}",
                "parentWorkflowRunId": "workflow-id",
                "agent": "concorde-spec-reviewer",
                "status": "completed",
            }
        )
        self.status["workflow"]["emits"].append(
            {
                "kind": "concorde.child-terminal",
                "ticket": "issued-ticket",
                "key": key,
                "runId": f"run-{index}",
                "invocation_id": identifier,
                "proposal_digest": proposal_digest,
                "metadata": str(self.root / f"metadata-{index}.json"),
            }
        )
        self.metadata[index] = {
            "runId": f"run-{index}",
            "agent": "concorde-spec-reviewer",
            "exitCode": 0,
            "acceptance": {
                "status": "verified",
                "verifyRuns": [
                    {
                        "command": command,
                        "status": "passed",
                        "exitCode": 0,
                        "structuredOutput": {
                            "invocation_id": identifier,
                            "proposal_digest": proposal_digest,
                            "state": "staged",
                            "accepted": False,
                        },
                    }
                ],
            },
        }

    def write(self):
        (self.root / "status.json").write_text(json.dumps(self.status))
        for index, metadata in self.metadata.items():
            (self.root / f"metadata-{index}.json").write_text(json.dumps(metadata))

    def verify(self):
        self.write()
        return verify_native_children(
            self.root,
            run_id="workflow-id",
            session_id="session-id",
            ticket="issued-ticket",
            children=tuple(self.children),
            runtime=NativeRuntimeBinding(
                FORMAT, "/fixture/package", "sha256:" + "0" * 64
            ),
        )

    @verifies("scenario.harness.native-terminal-evidence")
    def test_synthetic_terminal_records_need_no_workflow_receipt(self):
        self.assertEqual(len(self.verify()), 1)
        self.assertFalse((self.root / "workflow-receipt.json").exists())

    @verifies("scenario.harness.native-terminal-evidence")
    def test_scope_beyond_host_command_limit(self):
        for index in range(1, 40):
            self.add_child(index)
        self.assertEqual(len(self.verify()), 40)

    @verifies("scenario.harness.native-terminal-evidence")
    def test_gate_success_does_not_override_native_failure(self):
        self.metadata[0]["exitCode"] = 1
        with self.assertRaisesRegex(SpecError, "execution did not succeed"):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_no_caller_success_boolean_can_replace_metadata(self):
        self.status["workflow"]["emits"][0]["ok"] = True
        self.metadata[0]["exitCode"] = 1
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_incomplete_aggregate_cannot_commit(self):
        self.add_child(1)
        self.status["steps"][1]["status"] = "running"
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_unvisited_scope_is_not_coverage(self):
        self.add_child(1)
        self.status["steps"].pop()
        self.status["workflow"]["emits"].pop()
        with self.assertRaisesRegex(SpecError, "coverage is incomplete"):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_foreign_workflow_identity(self):
        self.status["runId"] = "foreign"
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_foreign_parent_identity(self):
        self.status["steps"][0]["parentWorkflowRunId"] = "foreign"
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_foreign_proposal_digest(self):
        self.metadata[0]["acceptance"]["verifyRuns"][0]["structuredOutput"][
            "proposal_digest"
        ] = "sha256:" + "f" * 64
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_other_gate_command_cannot_accept(self):
        self.metadata[0]["acceptance"]["verifyRuns"][0]["command"] = "other-command"
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_cancellation_before_commit(self):
        self.status["stopped"] = True
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_missing_metadata_fails_closed(self):
        self.write()
        (self.root / "metadata-0.json").unlink()
        with self.assertRaises(SpecError):
            verify_native_children(
                self.root,
                run_id="workflow-id",
                session_id="session-id",
                ticket="issued-ticket",
                children=tuple(self.children),
                runtime=NativeRuntimeBinding(
                    FORMAT, "/fixture/package", "sha256:" + "0" * 64
                ),
            )

    @verifies("scenario.harness.native-terminal-evidence")
    def test_duplicate_native_child_does_not_double_count(self):
        self.status["steps"].append(dict(self.status["steps"][0]))
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_nonterminal_or_skipped_children_never_supply_coverage(self):
        for state in ("pending", "running", "paused", "skipped", "failed", "stopped"):
            with self.subTest(state=state):
                self.status["steps"][0]["status"] = state
                with self.assertRaises(SpecError):
                    self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_new_artifact_version_needs_an_explicit_adapter(self):
        self.status["lifecycleArtifactVersion"] = 3
        with self.assertRaises(SpecError):
            self.verify()

    @verifies("scenario.harness.native-terminal-evidence")
    def test_malformed_native_fields_fail_closed(self):
        for value in (None, [], "verified", False):
            with self.subTest(value=value):
                self.metadata[0]["acceptance"] = value
                with self.assertRaises(SpecError):
                    self.verify()
