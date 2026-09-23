"""Terminal-node boundaries, without model calls or task delegation."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.admission import run_operation
from concorde.harness.entry import validate_invocation
from concorde.harness.host import OperationHost
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError, typed, validate_typed
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class TerminalBoundaryTests(unittest.TestCase):
    def test_worker_marked_process_cannot_invoke_operations(self):
        with patch.dict(os.environ, {"CONCORDE_WORKER_POLICY": "/host/policy.json"}):
            with self.assertRaises(SpecError) as error:
                validate_invocation({})
            self.assertEqual("permission_denied", error.exception.code)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                result = run_operation(
                    "concorde-validate",
                    None,
                    {},
                    host_context=OperationHost(root, REPOSITORY_ROOT),
                )
                self.assertEqual("blocked", result["status"])
                self.assertEqual("permission_denied", result["errors"][0]["code"])
                self.assertEqual([], list(root.iterdir()))

    @verifies("scenario.execution.model-selection-reject")
    def test_configuration_v1_is_not_reinterpreted(self):
        current = typed("concorde-operation-configuration", {"thinking": "high"})
        self.assertEqual(2, current["schema_version"])
        with self.assertRaises(TypedDataError) as error:
            validate_typed({**current, "schema_version": 1})
        self.assertEqual("unsupported_version", error.exception.code)
