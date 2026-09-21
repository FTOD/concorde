"""Native post-run acceptance is separate from model proposal and run success."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from concorde.harness.native_result import (
    MAX_CONTROL_BYTES,
    MAX_PROPOSAL_BYTES,
    NativeResultGate,
    control_value,
)
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies


class NativeResultTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "proposal.json"
        self.recheck = Mock()
        self.verify_execution = Mock()
        self.validate = Mock()
        self.persist = Mock(
            return_value={"outcome": "completed", "reference": "host-ref"}
        )
        self.gate = NativeResultGate(
            "issued-invocation",
            self.path,
            ticket="issued-ticket",
            recheck=self.recheck,
            validate=self.validate,
            persist=self.persist,
            verify_execution=self.verify_execution,
        )
        self.value = {"context_id": "bound-context", "outcome": "completed"}

    def submit(self):
        return self.gate.submit("issued-invocation", self.value)

    @verifies("scenario.harness.native-result-gate")
    def test_submission_is_not_completion(self):
        receipt = self.submit()
        self.assertFalse(receipt["accepted"])
        self.assertTrue(receipt["proposal_digest"].startswith("sha256:"))
        self.persist.assert_not_called()
        result = self.gate.finalize("issued-invocation")
        self.assertEqual(result["outcome"], "completed")
        self.recheck.assert_called_once_with()
        self.persist.assert_called_once_with(self.value)
        self.assertEqual(self.validate.call_count, 2)

    @verifies("scenario.harness.native-result-gate")
    def test_duplicate_gate_is_read_only_and_rechecks_current_inputs(self):
        self.submit()
        first = self.gate.finalize("issued-invocation")
        second = self.gate.finalize("issued-invocation")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.persist.assert_called_once()
        self.assertEqual(self.recheck.call_count, 2)

    @verifies("scenario.harness.native-result-gate")
    def test_second_submission_cannot_replace_first(self):
        self.submit()
        before = self.path.read_bytes()
        with self.assertRaises(SpecError):
            self.submit()
        self.assertEqual(self.path.read_bytes(), before)
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_foreign_submission_and_gate_are_rejected(self):
        with self.assertRaises(SpecError):
            self.gate.submit("foreign", self.value)
        self.assertFalse(self.path.exists())
        self.submit()
        with self.assertRaises(SpecError):
            self.gate.finalize("foreign")
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_missing_proposal_is_not_success(self):
        with self.assertRaises(SpecError):
            self.gate.finalize("issued-invocation")
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_invalid_proposal_can_be_corrected_before_acceptance(self):
        self.validate.side_effect = SpecError("invalid result", "invalid_completion")
        with self.assertRaises(SpecError):
            self.submit()
        self.assertFalse(self.path.exists())
        self.persist.assert_not_called()
        self.validate.side_effect = None
        self.submit()
        self.gate.finalize("issued-invocation")
        self.persist.assert_called_once()

    @verifies("scenario.harness.native-result-gate")
    def test_oversize_proposal_is_rejected_without_writing(self):
        with self.assertRaises(SpecError):
            self.gate.submit("issued-invocation", {"answer": "x" * MAX_PROPOSAL_BYTES})
        self.assertFalse(self.path.exists())
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_changed_proposal_bytes_stop_acceptance(self):
        self.submit()
        self.path.write_text('{"outcome":"completed"}')
        with self.assertRaisesRegex(SpecError, "changed"):
            self.gate.finalize("issued-invocation")
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_alias_is_not_an_admitted_proposal(self):
        self.submit()
        original = self.path.with_suffix(".original")
        self.path.rename(original)
        self.path.symlink_to(original)
        with self.assertRaisesRegex(SpecError, "aliased"):
            self.gate.finalize("issued-invocation")
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_stale_context_stops_without_persistence(self):
        self.submit()
        self.recheck.side_effect = SpecError("context changed", "stale_context")
        with self.assertRaisesRegex(SpecError, "context changed"):
            self.gate.finalize("issued-invocation")
        self.recheck.side_effect = None
        with self.assertRaisesRegex(SpecError, "fresh admission"):
            self.gate.finalize("issued-invocation")
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_uncertain_persistence_does_not_replay(self):
        self.submit()
        self.persist.side_effect = OSError("acknowledgement lost")
        with self.assertRaises(OSError):
            self.gate.finalize("issued-invocation")
        with self.assertRaises(SpecError):
            self.gate.finalize("issued-invocation")
        self.persist.assert_called_once()

    @verifies("scenario.harness.native-result-gate")
    def test_failed_child_cannot_be_accepted_even_with_submission(self):
        self.submit()
        self.gate.stop("child cancelled")
        with self.assertRaisesRegex(SpecError, "cancelled"):
            self.gate.finalize("issued-invocation")
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_control_dto_is_not_truncated(self):
        with self.assertRaises(SpecError):
            control_value({"answer": "x" * MAX_CONTROL_BYTES})
        self.assertEqual(control_value({"route": "stop"}), {"route": "stop"})

    @verifies("scenario.harness.native-result-gate")
    def test_successful_gate_does_not_commit_failed_native_child(self):
        self.submit()
        staged = self.gate.stage("issued-invocation")
        self.assertEqual(staged["state"], "staged")
        self.assertFalse(staged["accepted"])
        self.persist.assert_not_called()
        self.verify_execution.side_effect = SpecError(
            "native child failed", "execution_failed"
        )
        with self.assertRaisesRegex(SpecError, "native child failed"):
            self.gate.finalize("issued-invocation")
        self.persist.assert_not_called()

    @verifies("scenario.harness.native-result-gate")
    def test_cancel_after_durable_commit_does_not_claim_rollback(self):
        self.submit()
        accepted = self.gate.finalize("issued-invocation")
        self.gate.stop("enclosing execution cancelled after commit")
        self.verify_execution.side_effect = SpecError(
            "native workflow now cancelled", "execution_cancelled"
        )
        with self.assertRaisesRegex(SpecError, "now cancelled"):
            self.gate.finalize("issued-invocation")
        self.assertEqual(self.gate.committed_result, accepted)
        self.assertIsNot(self.gate.committed_result, accepted)
        with self.assertRaises(SpecError):
            self.gate.finalize("issued-invocation")
        self.persist.assert_called_once()


class StagingControlTests(unittest.TestCase):
    @verifies("scenario.harness.native-result-gate")
    def test_closed_bounded_host_control_not_model_prose(self):
        from concorde.harness.native_result import staging_control
        from concorde.spec.typed_data import canonical

        value = {
            "schema_version": 1,
            "ticket": "ticket",
            "invocation_id": "invocation",
            "proposal_digest": "sha256:" + "0" * 64,
            "state": "staged",
            "accepted": False,
        }
        expected = {
            key: value[key] for key in ("ticket", "invocation_id", "proposal_digest")
        }
        encoded = canonical(value)
        self.assertEqual(staging_control(encoded + "\n", **expected), value)
        malformed = [
            None,
            "",
            encoded[:-1],
            "progress\n" + encoded,
            encoded + "\n{}",
            "x" * (MAX_CONTROL_BYTES + 1),
            encoded[:-1] + ',"state":"staged"}',
            canonical({**value, "extra": True}),
            canonical({**value, "ticket": "foreign"}),
            canonical({**value, "schema_version": True}),
            canonical({**value, "accepted": "false"}),
            canonical({**value, "proposal_digest": "sha256:" + "f" * 64}),
        ]
        for text in malformed:
            with self.subTest(
                text=text if text is None or len(text) < 300 else "oversize"
            ):
                with self.assertRaises(SpecError):
                    staging_control(text, **expected)
