"""Task context: an Agent's typed input and result against its definition, and reference versions.

Inputs are built from real snapshots frozen for the shared-file project; the checks are the
production ``validate_agent_input`` and ``validate_agent_result`` the Agent node runs before launch
and after completion. The reference version check is the production script, pointed at temporary
reference and lock files.
"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import concorde.review.records  # noqa: F401  (registers the review stage types)
from concorde.harness.context import resolve_context
from concorde.harness.worker_profile import (
    ContractError,
    agent_definition,
    validate_agent_input,
    validate_agent_result,
)
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.shared_file_project import SharedFileFixture

TASK_INPUT = {
    "type_id": "concorde-implementation-task",
    "schema_version": 1,
    "data": {"plan": "Plan", "tasks": []},
}
CONTEXT_ID = "sha256:" + "1" * 64


def _review(mode: str, changes: list[dict]) -> dict:
    return typed(
        "concorde-review-input",
        {
            "review_mode": mode,
            "input_digest": "sha256:" + "2" * 64,
            "revision": {
                "spec_digest": "sha256:" + "3" * 64,
                "implementation_digest": None,
                "baseline": None,
                "head": None,
            },
            "changes": changes,
        },
    )


class AgentInputTests(unittest.TestCase):
    def setUp(self):
        self.fixture = SharedFileFixture(self)
        self.fixture.setUp()

    def snapshot(self, agent, **arguments):
        return resolve_context(
            self.fixture.repository(),
            "module.a",
            agent=agent,
            task="Adapt the shared value",
            **arguments,
        ).value

    def stage(self, snapshot):
        return typed(
            "concorde-agent-stage-context",
            {
                "snapshot": typed("concorde-context-snapshot", snapshot),
                "change_id": None,
                "expected_artifacts": [],
            },
        )

    def review(self, snapshot, review):
        return typed(
            "concorde-review-stage-context",
            {
                "snapshot": typed("concorde-context-snapshot", snapshot),
                "review": review,
            },
        )

    def refused(self, name, value):
        with self.assertRaises(ValueError):
            validate_agent_input(agent_definition(name), value)

    @verifies("scenario.context.input-check")
    def test_inputs_that_do_not_match_the_definition_are_refused(self):
        planner = self.snapshot("planner")
        programmer = self.snapshot("programmer", stage_inputs=(TASK_INPUT,))
        spec = self.snapshot("spec-reviewer")
        # Matching inputs are admitted.
        validate_agent_input(agent_definition("planner"), self.stage(planner))
        validate_agent_input(agent_definition("programmer"), self.stage(programmer))
        spec_source = spec["spec_resolution"]["sources"][0]["path"]
        validate_agent_input(
            agent_definition("spec_reviewer"),
            self.review(spec, _review("spec", [{"path": spec_source, "patch": "+x"}])),
        )
        with self.subTest("mismatched phase"):
            self.refused("context_assessor", self.stage(planner))
        with self.subTest("mismatched context type"):
            self.refused("spec_reviewer", self.stage(spec))
            self.refused("planner", self.review(planner, _review("spec", [])))
        with self.subTest("unadmitted stage input"):
            smuggled = copy.deepcopy(planner)
            smuggled["stage_inputs"] = [TASK_INPUT]
            self.refused("planner", self.stage(smuggled))
        with self.subTest("missing required stage input"):
            preview = self.snapshot("programmer", require_inputs=False)
            self.refused("programmer", self.stage(preview))
        with self.subTest("implementation files without implementation reads"):
            reviewer = self.snapshot("code-reviewer")
            self.assertTrue(reviewer["implementation_artifacts"])
            widened = copy.deepcopy(planner)
            widened["implementation_artifacts"] = reviewer["implementation_artifacts"]
            self.refused("planner", self.stage(widened))
        with self.subTest("Spec review carrying code changes"):
            self.refused(
                "spec_reviewer",
                self.review(
                    spec, _review("spec", [{"path": "source/a.py", "patch": "+x"}])
                ),
            )


class AgentResultTests(unittest.TestCase):
    def result(self, **fields):
        return typed(
            "concorde-agent-stage-result",
            {
                "context_id": CONTEXT_ID,
                "outcome": "completed",
                "answer": "Done",
                "blockers": [],
                "documents": [],
                "plan": "",
                "tasks": [],
                **fields,
            },
        )

    def refused(self, name, value, code):
        with self.assertRaises(ContractError) as raised:
            validate_agent_result(agent_definition(name), value)
        self.assertEqual(code, raised.exception.code)

    @verifies("scenario.context.result-check")
    def test_results_beyond_the_definition_are_refused(self):
        validate_agent_result(
            agent_definition("context_assessor"), self.result(outcome="sufficient")
        )
        validate_agent_result(agent_definition("planner"), self.result(plan="Plan"))
        # An outcome the definition does not list.
        for outcome in ("completed", "failed"):
            with self.subTest(outcome=outcome):
                self.refused(
                    "context_assessor",
                    self.result(outcome=outcome),
                    "invalid_completion",
                )
        # A filled field the definition does not permit.
        document = [{"path": "specs/a/module.md", "content": "# Rewritten\n"}]
        for name, fields in (
            ("planner", {"documents": document}),
            ("context_assessor", {"outcome": "sufficient", "documents": document}),
            ("programmer", {"plan": "A new plan"}),
            (
                "planner",
                {
                    "tasks": [
                        {
                            "id": "t",
                            "target_id": "module.a",
                            "description": "d",
                            "acceptance": "a",
                            "complete": False,
                        }
                    ]
                },
            ),
        ):
            with self.subTest(agent=name, fields=sorted(fields)):
                self.refused(name, self.result(**fields), "permission_denied")


class ReferenceVersionTests(unittest.TestCase):
    """``scripts/development/check-reference-versions.py`` against temporary checkouts."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        path = REPOSITORY_ROOT / "scripts/development/check-reference-versions.py"
        spec = importlib.util.spec_from_file_location("check_reference_versions", path)
        self.script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.script)
        self.pyproject = self.root / "reference/langgraph/libs/langgraph/pyproject.toml"
        self.lock = self.root / "uv.lock"

    def reference(self, version):
        self.pyproject.parent.mkdir(parents=True, exist_ok=True)
        self.pyproject.write_text(
            f'[project]\nname = "langgraph"\nversion = "{version}"\n'
        )

    def locked(self, version):
        self.lock.write_text(
            f'[[package]]\nname = "langgraph"\nversion = "{version}"\nsource = {{ registry = "x" }}\n'
        )

    def run_check(self, installed):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            mock.patch.object(self.script, "ROOT", self.root),
            mock.patch.object(self.script, "VENDORED_PYPROJECT", self.pyproject),
            mock.patch.object(self.script, "LOCK", self.lock),
            mock.patch.object(
                self.script.importlib.metadata, "version", return_value=installed
            ),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            try:
                status = self.script.main()
            except SystemExit as exit:
                status = exit.code
        return status, stdout.getvalue(), stderr.getvalue()

    @verifies("scenario.context.reference-versions")
    def test_a_reference_at_another_release_fails(self):
        for reference, installed, lock in (
            ("1.0.0", "1.1.0", "1.1.0"),
            ("1.1.0", "1.1.0", "1.0.0"),
            ("1.0.0", "1.1.0", None),
        ):
            with self.subTest(reference=reference, installed=installed, lock=lock):
                self.reference(reference)
                if lock is None:
                    self.lock.unlink(missing_ok=True)
                else:
                    self.locked(lock)
                status, stdout, stderr = self.run_check(installed)
                self.assertEqual(1, status)
                self.assertIn(
                    f"vendored={reference} installed={installed} locked={lock}", stdout
                )
                self.assertIn("reference/langgraph is not checked out", stderr)
                self.assertIn("checkout <tag>", stderr)

    @verifies("scenario.context.reference-versions")
    def test_agreeing_versions_pass_and_a_missing_checkout_fails(self):
        self.reference("1.1.0")
        self.locked("1.1.0")
        self.assertEqual(0, self.run_check("1.1.0")[0])
        self.lock.unlink()
        self.assertEqual(0, self.run_check("1.1.0")[0])
        self.pyproject.unlink()
        status, *_ = self.run_check("1.1.0")
        self.assertNotEqual(0, status)
        self.assertIn("init-references.py", str(status))


if __name__ == "__main__":
    unittest.main()
