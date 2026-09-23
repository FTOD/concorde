"""Terminal-node boundaries, without model calls or task delegation."""

import unittest

from concorde.spec.typed_data import TypedDataError, typed, validate_typed
from concorde.spec.verification import verifies


class TerminalBoundaryTests(unittest.TestCase):
    @verifies("scenario.execution.model-selection-reject")
    def test_configuration_v1_is_not_reinterpreted(self):
        current = typed("concorde-operation-configuration", {"thinking": "high"})
        self.assertEqual(2, current["schema_version"])
        with self.assertRaises(TypedDataError) as error:
            validate_typed({**current, "schema_version": 1})
        self.assertEqual("unsupported_version", error.exception.code)
