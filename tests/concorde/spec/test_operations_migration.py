"""The Operations cutover refuses old executable data instead of silently aliasing it."""

import json
import tempfile
import unittest
from pathlib import Path

from concorde.harness.entry import validate_invocation
from concorde.harness.change_worktree import STATE_PATH, ensure_change, read_change
from concorde.spec.content_model import reading_problems
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError, typed, validate_typed
from concorde.spec.verification import verifies
from concorde.spec.wire_shapes import type_version


class OperationsMigrationTests(unittest.TestCase):
    @verifies("scenario.harness.typed-reject")
    def test_changed_wire_types_advance_versions_and_reject_old_versions(self):
        for name, current in {
            "concorde-discovery-context": 6,
            "concorde-main-stage-context": 5,
            "concorde-init-request": 2,
            "concorde-configure-request": 2,
            "concorde-configure-response": 2,
            "concorde-dev-loop-response": 3,
            "concorde-issues-response": 2,
        }.items():
            with self.subTest(name=name):
                self.assertEqual(current, type_version(name))
                with self.assertRaises(TypedDataError) as refusal:
                    validate_typed(
                        {"type_id": name, "schema_version": current - 1, "data": {}}
                    )
                self.assertEqual("unsupported_version", refusal.exception.code)
        with self.assertRaises(TypedDataError):
            validate_typed(
                {
                    "type_id": "concorde-capability-configuration",
                    "schema_version": 1,
                    "data": {},
                }
            )

    @verifies("scenario.harness.operation-state")
    def test_retired_envelope_and_identity_field_are_not_current_aliases(self):
        current = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-main",
            "mode": "execute",
            "configuration": None,
            "input": typed("concorde-main-request", {"task": "Inspect"}),
        }
        self.assertEqual(current, validate_invocation(current))
        for old in (
            {**current, "type_id": "concorde-capability-invocation"},
            {
                **{k: v for k, v in current.items() if k != "operation_id"},
                "capability_id": "concorde-main",
            },
        ):
            with self.subTest(fields=list(old)), self.assertRaises(SpecError):
                validate_invocation(old)

    @verifies("scenario.harness.change-owner")
    def test_legacy_worktree_state_cannot_resume_and_is_not_rewritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = ensure_change(root, allow_primary=True)
            self.assertEqual(2, state["schema_version"])
            path = root / STATE_PATH
            state["schema_version"] = 1
            old = json.dumps(state).encode()
            path.write_bytes(old)
            with self.assertRaises(SpecError) as refusal:
                read_change(root, required=True)
            self.assertEqual("unsupported_worktree_version", refusal.exception.code)
            self.assertEqual(old, path.read_bytes())

    @verifies("scenario.spec.reader-parts")
    def test_retired_reading_bindings_require_explicit_migration(self):
        inventory = "# Old inventory\n\n```concorde-capabilities\n[]\n```\n"
        self.assertTrue(
            reading_problems(inventory, primary=False, role="implementation")
        )
        graph = (
            "# Exact graph\n\n```mermaid\nflowchart LR\n%% flow: old\na --> b\n```\n"
        )
        self.assertTrue(reading_problems(graph, primary=False, role="implementation"))
        self.assertFalse(
            reading_problems(
                graph.replace("%% flow:", "%% graph:"),
                primary=False,
                role="implementation",
            )
        )
