"""Deterministic Host entry paths do not import or execute LangGraph."""

import builtins
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution.project_defaults import install_project_defaults
from concorde.harness.admission import run_operation
from concorde.harness.host import OperationHost
from concorde.issues.store import dispose_issue, read_issue
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.issues.test_store import report
from tests.concorde.spec.support import CONFIGURATION, PACKAGE, project


class HostToolTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        project(self.root)

    def call(self, name, payload, root=None):
        original = builtins.__import__

        def without_graph(module, *args, **kwargs):
            if module == "langgraph" or module.startswith("langgraph."):
                raise AssertionError("Host tool imported LangGraph: " + module)
            return original(module, *args, **kwargs)

        with patch("builtins.__import__", without_graph):
            result = run_operation(
                name,
                CONFIGURATION,
                typed(name + "-request", payload),
                host_context=OperationHost(
                    root or self.root,
                    PACKAGE,
                    allow_primary_worktree=True,
                ),
            )
        self.assertNotIn(
            "execution_failed", [e["code"] for e in result["errors"]], result
        )
        return result

    @verifies(
        "scenario.spec.propose-initialization", "scenario.harness.host-tools-direct"
    )
    def test_initialization_proposal_without_graph(self):
        root = self.root / "new-project"
        root.mkdir()
        install_project_defaults(root, PACKAGE)
        result = self.call(
            "concorde-init",
            {"action": "propose", "name": "Example", "configuration": CONFIGURATION},
            root,
        )
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual(result["output"]["data"]["status"], "proposed")

    @verifies("scenario.distribution.configure-apply")
    def test_configuration_without_graph(self):
        result = self.call("concorde-configure", {"configuration": CONFIGURATION})
        self.assertEqual(result["status"], "succeeded", result)

    @verifies(
        "scenario.issues.inspect",
        "scenario.issues.store-report",
        "scenario.issues.store-disposition",
    )
    def test_issue_bookkeeping_without_graph(self):
        result = self.call(
            "concorde-issues",
            {
                "action": "report",
                "target_id": "service.transfer",
                "report": report(owner_target_id="service.transfer", evidence=[]),
            },
        )
        self.assertEqual(result["status"], "succeeded", result)
        identifier = result["output"]["data"]["issues"][0]["id"]
        for action in ("list", "show"):
            result = self.call(
                "concorde-issues",
                {
                    "action": action,
                    **({"issue_id": identifier} if action == "show" else {}),
                },
            )
            self.assertEqual(result["status"], "succeeded", result)
        _, revision = read_issue(self.root, identifier)
        dispose_issue(
            self.root,
            identifier,
            revision,
            reason="not-actionable",
            note="Fixture disposition",
            evidence=["Fixture contract"],
            actor="developer",
        )
        result = self.call(
            "concorde-issues",
            {
                "action": "reopen",
                "issue_id": identifier,
                "note": "Explicit fixture request",
            },
        )
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual(result["output"]["data"]["issues"][0]["status"], "open")

    @verifies("scenario.validation.blocked")
    def test_validation_gates_without_graph(self):
        result = self.call(
            "concorde-validate",
            {
                "target_id": "service.transfer",
                "task": "Validate current inputs",
                "run_checks": False,
            },
        )
        self.assertIn(result["status"], {"succeeded", "blocked"}, result)

    @verifies("scenario.delivery.session-rejected")
    def test_delivery_rejection_without_graph(self):
        result = self.call("concorde-deliver", {"change_id": "change.not-present"})
        self.assertEqual(result["status"], "blocked", result)
