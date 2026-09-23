"""The Operation catalog: its declarations, the loader, dispatch by kind and child requests."""

from __future__ import annotations

import ast
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agents

from concorde.harness.host import AdmittedRequest, OperationHost
from concorde.operations.catalog import (
    CATALOG,
    OPERATION_NAMES,
    PUBLIC_OPERATIONS,
    CatalogError,
    load_catalog,
    mirror,
)
from concorde.operations.dispatch import dispatch, run_child
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import data_schema, type_version, typed
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


def _fixture_root(directory: Path) -> Path:
    """A copy of the declaration packages the loader reads."""
    for name in ("operations", "agents"):
        shutil.copytree(
            REPOSITORY_ROOT / name,
            directory / name,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    return directory


class CatalogTests(unittest.TestCase):
    def test_the_catalog_holds_every_operation_and_no_agent(self):
        self.assertEqual(11, len(CATALOG))
        self.assertEqual(OPERATION_NAMES, PUBLIC_OPERATIONS)
        agent_names = {"concorde-" + n.replace("_", "-") for n in agents.AGENTS}
        self.assertFalse(agent_names & set(CATALOG))
        for name, operation in CATALOG.items():
            with self.subTest(operation=name):
                self.assertEqual("concorde-" + operation.id, name)
                self.assertEqual(operation.deterministic, operation.kind == "host")
                self.assertEqual(
                    operation.declaration["model_backed"], not operation.deterministic
                )
                self.assertEqual(operation.request, data_schema(f"{name}-request"))
                self.assertEqual(operation.response, data_schema(f"{name}-response"))
                self.assertEqual(
                    operation.request_version, type_version(f"{name}-request")
                )
                self.assertEqual(
                    operation.response_version, type_version(f"{name}-response")
                )

    def test_the_spec_mirror_equals_the_loaded_declarations(self):
        document = json.loads(
            (REPOSITORY_ROOT / "specs/concorde/operations/catalog.md.json").read_text()
        )
        self.assertEqual(document["extensions"]["concorde.operations"], mirror())

    def test_only_issue_solving_composes_other_operations(self):
        composing = {name: item.uses for name, item in CATALOG.items() if item.uses}
        self.assertEqual(
            {
                "concorde-issues": (
                    "concorde-spec-review",
                    "concorde-code-review",
                    "concorde-validate",
                )
            },
            composing,
        )

    @verifies("scenario.operations.invalid-declaration")
    def test_an_invalid_declaration_refuses_the_whole_catalog(self):
        cases = (
            ('KIND = "agent-call"', 'KIND = "graph"', "KIND"),
            (
                'AGENTS = (("task_author", "tasks"),)',
                'AGENTS = (("ghost_author", "tasks"),)',
                "AGENTS",
            ),
            (
                'AGENTS = (("task_author", "tasks"),)',
                'AGENTS = (("task_author", "dreaming"),)',
                "AGENTS",
            ),
            (
                'ENTRY_POINT = "concorde.planning.hooks:task_author"',
                'ENTRY_POINT = "concorde.planning.hooks:planner"',
                "ENTRY_POINT",
            ),
            ("USES = ()", 'USES = ("concorde-tasks",)', "USES"),
        )
        for before, after, field in cases:
            with (
                self.subTest(field=field, value=after),
                tempfile.TemporaryDirectory() as raw,
            ):
                root = _fixture_root(Path(raw))
                declaration = root / "operations/tasks.py"
                text = declaration.read_text()
                self.assertIn(before, text)
                declaration.write_text(text.replace(before, after))
                with self.assertRaises(CatalogError) as refused:
                    load_catalog(root)
                self.assertEqual("tasks", refused.exception.declaration)
                self.assertEqual(field, refused.exception.field)

    @verifies("scenario.operations.invalid-declaration")
    def test_an_unlisted_declaration_file_refuses_the_catalog(self):
        with tempfile.TemporaryDirectory() as raw:
            root = _fixture_root(Path(raw))
            (root / "operations/stray.py").write_text('"""Unlisted."""\n')
            with self.assertRaises(CatalogError) as refused:
                load_catalog(root)
            self.assertEqual("stray", refused.exception.declaration)

    def test_dispatch_and_the_loader_import_no_provider(self):
        providers = {
            "planning",
            "implementation",
            "review",
            "validation",
            "delivery",
            "issue_solving",
            "issues",
            "distribution",
            "session",
        }
        for relative in (
            "src/concorde/operations/dispatch.py",
            "src/concorde/operations/catalog.py",
        ):
            tree = ast.parse((REPOSITORY_ROOT / relative).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    package = (node.module or "").split(".")
                    with self.subTest(file=relative, module=node.module):
                        self.assertFalse(providers & set(package))


class DispatchTests(unittest.TestCase):
    def request(self, operation, **host):
        return AdmittedRequest(
            operation=operation,
            declaration=CATALOG[operation].declaration,
            configuration=None,
            data={"target_id": "module.example", "task": "Check"},
            mutates=True,
            host=OperationHost(REPOSITORY_ROOT, REPOSITORY_ROOT, **host),
        )

    @verifies("scenario.operations.host-dispatch")
    def test_a_host_service_runs_its_declared_entry_point(self):
        request = self.request("concorde-validate")
        output = typed(
            "concorde-validate-response",
            {
                "target_id": "module.example",
                "focus_id": None,
                "change_id": None,
                "context_id": None,
                "outcome": "ready",
                "answer": "",
                "artifacts": [],
                "blockers": [],
                "checks": [],
                "completed_operations": [],
            },
        )
        with patch("concorde.validation.validate.run", return_value=output) as entry:
            self.assertIs(output, dispatch(request))
        entry.assert_called_once_with(request)

    @verifies("scenario.operations.native-without-pi")
    def test_an_agent_call_without_the_native_driver_runs_no_hook(self):
        for name in ("concorde-tasks", "concorde-implement", "concorde-plan"):
            with (
                self.subTest(operation=name),
                patch("concorde.harness.invocation.Invocation") as bound,
            ):
                with self.assertRaises(SpecError) as refused:
                    dispatch(self.request(name))
                self.assertEqual("native_required", refused.exception.code)
                bound.assert_not_called()

    def test_an_agent_call_goes_to_the_native_driver(self):
        seen = []

        class Driver:
            def agent_call(self, request, agent):
                seen.append(("agent-call", request.operation, agent))

            def workflow(self, request, entry):
                seen.append(("workflow", request.operation, entry))

        for name in ("concorde-tasks", "concorde-plan"):
            dispatch(self.request(name, native_driver=Driver()))
        self.assertEqual(
            [
                ("agent-call", "concorde-tasks", "task_author"),
                ("workflow", "concorde-plan", "concorde.planning.hooks:plan_workflow"),
            ],
            seen,
        )


class ChildRequestTests(unittest.TestCase):
    host = OperationHost(REPOSITORY_ROOT, REPOSITORY_ROOT)
    payload = typed(
        "concorde-validate-request", {"target_id": "module.example", "task": "Check"}
    )

    @verifies("scenario.operations.child-undeclared")
    def test_an_undeclared_child_is_refused_before_admission(self):
        with patch("concorde.operations.dispatch.admit") as admit:
            for parent, child, code in (
                ("concorde-issues", "concorde-deliver", "undeclared_operation"),
                ("concorde-plan", "concorde-validate", "undeclared_operation"),
                ("concorde-issues", "concorde-issues", "undeclared_operation"),
                ("concorde-issues", "concorde-planner", "unknown_operation"),
                ("concorde-ghost", "concorde-validate", "unknown_operation"),
            ):
                with self.subTest(parent=parent, child=child):
                    with self.assertRaises(SpecError) as refused:
                        run_child(parent, child, {}, self.payload, self.host)
                    self.assertEqual(code, refused.exception.code)
            admit.assert_not_called()

    @verifies("scenario.operations.child-declared")
    def test_a_declared_child_passes_admission_as_its_own_request(self):
        envelope = {"status": "succeeded"}
        with patch(
            "concorde.operations.dispatch.admit", return_value=envelope
        ) as admit:
            result = run_child(
                "concorde-issues", "concorde-validate", {}, self.payload, self.host
            )
        self.assertIs(envelope, result)
        self.assertEqual(("concorde-validate", {}, self.payload), admit.call_args.args)
        self.assertIsNotNone(admit.call_args.kwargs["host_context"].services)


if __name__ == "__main__":
    unittest.main()
