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
            "concorde-context-snapshot": 6,
            "concorde-agent-stage-context": 4,
            "concorde-agent-stage-result": 3,
            "concorde-spec-review-request": 2,
            "concorde-code-review-request": 2,
            "concorde-tasks-request": 2,
            "concorde-init-request": 2,
            "concorde-configure-request": 2,
            "concorde-configure-response": 2,
            "concorde-plan-response": 3,
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

    @verifies("scenario.harness.typed-reject")
    def test_current_shapes_do_not_restore_implicit_targets_or_author_decisions(self):
        for name in ("spec-review", "code-review", "tasks"):
            with self.subTest(name=name), self.assertRaises(TypedDataError):
                typed(f"concorde-{name}-request", {"task": "Explicit target required"})
        result = {
            "context_id": "sha256:" + "0" * 64,
            "outcome": "completed",
            "answer": "Return intent to caller",
            "blockers": [],
            "documents": [],
            "plan": "",
            "tasks": [],
            "issue_decision": {
                "action": "spec-repair",
                "intent": "Clarify contract",
                "rationale": "Missing promise",
                "duplicate_of": None,
            },
        }
        self.assertEqual(
            3, typed("concorde-agent-stage-result", result)["schema_version"]
        )
        result["issue_decision"]["specify"] = True
        with self.assertRaises(TypedDataError) as refusal:
            typed("concorde-agent-stage-result", result)
        self.assertEqual("invalid_field", refusal.exception.code)

    @verifies("scenario.harness.typed-reject")
    def test_removed_wire_types_are_unknown_not_version_aliases(self):
        from concorde.spec.typed_data import DATA_SCHEMAS, json_schema

        removed = (
            "main-request",
            "main-response",
            "dev-loop-request",
            "dev-loop-response",
            "specify-loop-request",
            "specify-loop-response",
            "specify-request",
            "specify-response",
            "discovery-context",
            "main-stage-context",
            "main-stage-result",
            "topology-design",
            "topology-proposal",
            "topology-application",
            "topology-author-context",
            "topology-author-result",
        )
        for suffix in removed:
            name = "concorde-" + suffix
            with self.subTest(name=name):
                self.assertNotIn(name, DATA_SCHEMAS)
                with self.assertRaises(KeyError):
                    json_schema(name)
                for version in (1, 2, 3, 4, 5, 6):
                    with self.assertRaises(TypedDataError) as refusal:
                        validate_typed(
                            {"type_id": name, "schema_version": version, "data": {}}
                        )
                    self.assertEqual("unknown_type", refusal.exception.code)

    @verifies("scenario.harness.operation-state")
    def test_retired_envelope_and_identity_field_are_not_current_aliases(self):
        current = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-context-solve",
            "mode": "execute",
            "configuration": None,
            "input": typed(
                "concorde-context-solve-request",
                {"target_id": "module.project", "task": "Inspect"},
            ),
        }
        self.assertEqual(current, validate_invocation(current))
        for old in (
            {**current, "type_id": "concorde-capability-invocation"},
            {
                **{k: v for k, v in current.items() if k != "operation_id"},
                "capability_id": "concorde-context-solve",
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
