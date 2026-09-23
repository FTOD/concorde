"""The native result gate's control documents are bounded, canonical Host output."""

import unittest

from concorde.harness.native_result import MAX_CONTROL_BYTES, control_value
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies


class ControlValueTests(unittest.TestCase):
    @verifies("scenario.harness.native-result-gate")
    def test_control_dto_is_not_truncated(self):
        with self.assertRaises(SpecError):
            control_value({"answer": "x" * MAX_CONTROL_BYTES})
        self.assertEqual(control_value({"route": "stop"}), {"route": "stop"})


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
