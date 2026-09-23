"""Failure feedback at the actual finite, optional Graph and native record boundaries."""

import asyncio
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.harness.entry import invocation_failure
from concorde.harness.execution_error import (
    exception_feedback,
    native_feedback,
    response_failure,
    safe_text,
    workflow_feedback,
)
from concorde.harness.native_driver import _remember_failure, _slot_failure
from concorde.harness.operation_node import OperationNode
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.support.stage_context import stage_context as _stage_context


class ExecutionFeedbackTests(unittest.TestCase):
    @verifies("scenario.admission.feedback-causes")
    def test_pi_proposal_command_and_display_boundaries(self):
        root = Path(__file__).resolve().parents[3]
        result = subprocess.run(
            [
                "node",
                "--experimental-strip-types",
                str(Path(__file__).with_name("execution_feedback_probe.mts")),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(
        os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
        and os.environ.get("CONCORDE_NATIVE_PI"),
        "explicit SDK/native roots required",
    )
    @verifies("scenario.admission.feedback-causes")
    def test_actual_sdk_observation_failure_reaches_native_error_reporting(self):
        from concorde.harness.native_runtime import admit_native_runtime
        from tests.concorde.support.fake_openai_provider import FakeOpenAIProvider

        root = Path(__file__).resolve().parents[3]
        native = Path(os.environ["CONCORDE_NATIVE_SUBAGENTS"])
        admit_native_runtime(native)
        with (
            tempfile.TemporaryDirectory() as scratch,
            FakeOpenAIProvider(
                [
                    {"tool": "structured_output", "arguments": {"value": {}}},
                    {
                        "tool": "structured_output",
                        "arguments": {"value": {"answer": "corrected"}},
                    },
                    {"text": "Fixture complete"},
                ]
            ) as provider,
        ):
            result = subprocess.run(
                [
                    "node",
                    str(Path(__file__).with_name("observation_failure_sdk.mjs")),
                    os.environ["CONCORDE_NATIVE_PI"],
                    str(native),
                    str(root),
                    scratch,
                    provider.base_url,
                ],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=45,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(provider.requests), 3)
            print(result.stdout)

    @verifies("scenario.admission.feedback-causes")
    def test_entry_preserves_exception_chain_for_every_public_kind(self):
        for operation in (
            "concorde-context-solve",
            "concorde-tasks",
            "concorde-implement",
            "concorde-plan",
            "concorde-spec-review",
            "concorde-code-review",
            "concorde-issues",
            "concorde-init",
            "concorde-configure",
            "concorde-validate",
            "concorde-deliver",
        ):
            with self.subTest(operation=operation):
                try:
                    try:
                        raise OSError(5, "disk read failed")
                    except OSError as cause:
                        raise SpecError(
                            "cannot read admitted input", "missing_source"
                        ) from cause
                except SpecError as error:
                    result = invocation_failure(operation, error)
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["output"])
                feedback = result["errors"][0]["feedback"]
                self.assertEqual(feedback["code"], "missing_source")
                self.assertEqual(feedback["causes"][0]["code"], 5)
                self.assertIn("disk read failed", feedback["causes"][0]["message"])

    @verifies("scenario.admission.feedback-causes")
    def test_optional_graph_sync_async_refusal_preserves_cause(self):
        context = _stage_context()
        cause = SpecError("exact plan identity refused", "stale_context")

        def refuse(_):
            raise cause

        async def async_refuse(_):
            raise cause

        for asynchronous in (False, True):
            cause = SpecError("exact plan identity refused", "stale_context")
            with (
                self.subTest(asynchronous=asynchronous),
                self.assertRaises(SpecError) as raised,
            ):
                graph = OperationNode("planner").graph(
                    async_refuse if asynchronous else refuse
                )
                if asynchronous:
                    asyncio.run(graph.ainvoke(context["data"]))
                else:
                    graph.invoke(context["data"])
            self.assertIs(raised.exception, cause)
            detail = exception_feedback(raised.exception)
            self.assertEqual(detail["layer"], "operation")
            self.assertEqual(detail["causes"][0]["code"], "stale_context")
            self.assertEqual(detail["causes"][0]["message"], str(cause))

    @verifies("scenario.admission.feedback-causes")
    def test_optional_graph_cancellation_is_not_an_ordinary_failure(self):
        async def cancel(_):
            raise asyncio.CancelledError("caller cancelled native service")

        from langgraph.errors import NodeCancelledError

        with self.assertRaises(NodeCancelledError) as raised:
            asyncio.run(
                OperationNode("planner").graph(cancel).ainvoke(_stage_context()["data"])
            )
        self.assertEqual(
            exception_feedback(raised.exception)["causes"][0]["causes"][0]["category"],
            "cancelled",
        )

    @verifies("scenario.admission.feedback-causes")
    def test_first_slot_failure_survives_invalidation_and_large_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            original = exception_feedback(
                SpecError("first cause " + "x" * 30000, "invalid_completion"),
                layer="host-submit",
                attempt="ticket",
            )
            _remember_failure(directory, original)
            _remember_failure(directory, exception_feedback(ValueError("secondary")))
            detail = exception_feedback(_slot_failure(directory))
            self.assertEqual(detail["causes"], [original])
            self.assertTrue(detail["diagnostics"]["references"])
            self.assertEqual(
                json.loads((directory / "failure.json").read_text()), original
            )
            self.assertEqual((directory / "failure.json").stat().st_mode & 0o777, 0o600)

    @verifies("scenario.admission.feedback-causes")
    def test_native_categories_unknowns_and_workflow_error_emissions(self):
        for row, category in (
            ({"timedOut": True}, "timeout"),
            ({"interrupted": True}, "cancelled"),
            ({"exitCode": 9}, "native-exit"),
            ({"metadataSaveError": "cannot publish"}, "observation"),
            ({}, "unknown"),
        ):
            self.assertEqual(native_feedback(row)["category"], category)
        with tempfile.TemporaryDirectory() as tmp:
            detail = exception_feedback(
                SpecError("staging refused", "invalid_completion")
            )
            status = {
                "state": "failed",
                "error": "child stopped",
                "workflow": {
                    "emits": [{"kind": "concorde.failure", "feedback": detail}]
                },
            }
            result = workflow_feedback(
                {"directory": tmp}, status, {"runId": "run", "asyncDir": tmp}
            )
            self.assertIn(detail, result["causes"])
            self.assertEqual(result["attempt"], "run")

    @verifies("scenario.admission.feedback-causes")
    def test_refused_workflow_service_keeps_original_errors(self):
        for layer in ("planning", "review", "issues"):
            error = response_failure(
                "parent refusal",
                {
                    "result": {
                        "invocation_id": "lower-attempt",
                        "errors": [
                            {
                                "code": "incompatible_handoff",
                                "message": "exact lower cause",
                            }
                        ],
                    }
                },
                layer=layer,
                attempt="parent-attempt",
            )
            self.assertEqual(
                error.feedback["causes"][0]["code"], "incompatible_handoff"
            )
            self.assertEqual(
                error.feedback["causes"][0]["message"], "exact lower cause"
            )
            self.assertEqual(error.feedback["causes"][0]["attempt"], "lower-attempt")

    @verifies("scenario.admission.feedback-causes")
    def test_credential_labels_are_redacted_without_clipping_causes(self):
        text = safe_text(
            'Authorization: Bearer super-secret api_key="hidden" password=private ordinary error'
        )
        for secret in ("super-secret", "hidden", "private"):
            self.assertNotIn(secret, text)
        self.assertIn("ordinary error", text)


DISPLAY_PROBE = """
import { errorDisplay } from "./pi/error-display.mjs";
import { failure } from "./pi/execution-error.mjs";
const record = failure("large cause password=private", {
  code: "relay_failed",
  layer: "relay",
  category: "transport",
  attempt: "attempt-1",
  diagnostics: "x".repeat(30000) + " api_key=hidden",
});
console.log(errorDisplay(record));
"""


class FeedbackDisplayTests(unittest.TestCase):
    """Pi's bounded display of causal feedback records larger than its limit."""

    def display(self, temporary):
        root = Path(__file__).resolve().parents[3]
        result = subprocess.run(
            ["node", "--input-type=module", "-e", DISPLAY_PROBE],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "TMPDIR": str(temporary)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    @verifies("scenario.admission.feedback-export")
    def test_a_large_record_is_exported_to_a_private_file(self):
        import hashlib

        with tempfile.TemporaryDirectory() as raw:
            display = self.display(Path(raw))
            diagnostics = display["diagnostics"]
            self.assertFalse(diagnostics["complete"])
            self.assertEqual(
                ("relay_failed", "relay", "transport", "attempt-1"),
                (
                    display["code"],
                    display["layer"],
                    display["category"],
                    display["attempt"],
                ),
            )
            path = Path(diagnostics["reference"])
            # A new private directory under the temporary root holds the whole record.
            self.assertEqual(Path(raw).resolve(), path.parent.parent.resolve())
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            saved = path.read_bytes()
            self.assertEqual(len(saved), diagnostics["bytes"])
            self.assertEqual(hashlib.sha256(saved).hexdigest(), diagnostics["sha256"])
            record = json.loads(saved)
            self.assertEqual("relay_failed", record["code"])
            self.assertIn("x" * 30000, record["diagnostics"]["text"])
            for secret in ("private", "hidden"):
                self.assertNotIn(secret, saved.decode())
                self.assertNotIn(secret, json.dumps(display))

    @verifies("scenario.admission.feedback-export")
    def test_a_failed_export_is_reported_as_incomplete(self):
        with tempfile.TemporaryDirectory() as raw:
            display = self.display(Path(raw) / "missing")
        diagnostics = display["diagnostics"]
        self.assertFalse(diagnostics["complete"])
        self.assertIsNone(diagnostics["reference"])
        self.assertTrue(diagnostics["export_error"])
        self.assertGreater(diagnostics["bytes"], 30000)
        self.assertEqual("relay_failed", display["code"])
