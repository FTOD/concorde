"""Deterministic Host entry paths do not import or execute LangGraph."""

import builtins
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution.project_defaults import install_project_defaults
from concorde.operations.dispatch import run_operation
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

    def call(self, name, payload, root=None, configuration=CONFIGURATION):
        original = builtins.__import__

        def without_graph(module, *args, **kwargs):
            if module == "langgraph" or module.startswith("langgraph."):
                raise AssertionError("Host tool imported LangGraph: " + module)
            return original(module, *args, **kwargs)

        with patch("builtins.__import__", without_graph):
            result = run_operation(
                name,
                configuration,
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
        "scenario.spec.propose-initialization",
        "scenario.admission.deterministic-no-model",
    )
    def test_initialization_proposal_without_graph(self):
        root = self.root / "new-project"
        root.mkdir()
        install_project_defaults(root, PACKAGE)
        result = self.call(
            "concorde-init",
            {"action": "propose", "name": "Example", "configuration": CONFIGURATION},
            root,
            configuration=None,
        )
        self.assertEqual(result["status"], "succeeded", result)
        self.assertEqual(result["output"]["data"]["status"], "proposed")

    @verifies("scenario.admission.configure-apply")
    def test_configuration_without_graph(self):
        result = self.call("concorde-configure", {"configuration": CONFIGURATION})
        self.assertEqual(result["status"], "succeeded", result)

    @verifies(
        "scenario.issue-solving.inspect",
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

    @verifies("scenario.validation.failed-check")
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


def selection_hook(project_root, package_root, data):
    """A fixture target selection hook: records its call and binds a fixed target."""
    HOOK_CALLS.append((project_root, dict(data)))
    return {**data, "target_id": "service.transfer", "task": "Bound by hook"}, False


HOOK_CALLS: list = []


class DeclarationAdmissionTests(unittest.TestCase):
    """Admission decides from the declarations and dispatcher it is handed, nothing else."""

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        project(self.root)
        self.dispatched = []
        HOOK_CALLS.clear()

    def declaration(self, **changes):
        from concorde.operations.catalog import declarations

        return {**declarations()["concorde-validate"], **changes}

    def admit(self, declaration, *, name="concorde-validate", data=None):
        from concorde.harness.admission import run_operation as admit
        from concorde.harness.host import AdmissionServices

        def dispatcher(request):
            self.dispatched.append(request)
            return typed(
                "concorde-validate-response",
                {
                    "target_id": request.data["target_id"],
                    "focus_id": None,
                    "change_id": None,
                    "context_id": None,
                    "outcome": "completed",
                    "answer": request.data["task"],
                    "artifacts": [],
                    "blockers": [],
                    "checks": [],
                    "completed_operations": [],
                },
            )

        services = AdmissionServices(
            catalog={name: declaration} if declaration else {}, dispatcher=dispatcher
        )
        return admit(
            name,
            CONFIGURATION,
            typed(
                "concorde-validate-request",
                data or {"target_id": "service.transfer", "task": "Check"},
            ),
            host_context=OperationHost(
                self.root, PACKAGE, mode="describe-policy", services=services
            ),
        )

    @verifies("scenario.admission.unknown-capability")
    def test_a_capability_the_catalog_does_not_offer_is_refused(self):
        for declaration in (None, self.declaration(public=False)):
            with self.subTest(declaration=declaration):
                result = self.admit(declaration)
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual("unknown_operation", result["errors"][0]["code"])
        self.assertEqual([], self.dispatched)

    @verifies("scenario.admission.invalid-declaration")
    def test_a_declaration_violating_its_contract_is_refused_before_any_effect(self):
        for declaration in (
            self.declaration(entry_point="concorde.validation.validate:missing"),
            self.declaration(entry_point="not-a-reference"),
            self.declaration(workspace="elsewhere"),
            self.declaration(mutation={"policy": "always", "actions": ["apply"]}),
            self.declaration(workspace="none"),
            self.declaration(target={"selection": "provider-hook", "hook": None}),
            {**self.declaration(), "kind": "host"},
        ):
            with self.subTest(declaration=declaration):
                result = self.admit(declaration)
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual("invalid_input", result["errors"][0]["code"])
        self.assertEqual([], self.dispatched)
        self.assertFalse((self.root / ".concorde/status").exists())

    @verifies("scenario.admission.provider-hook", "scenario.admission.execute-request")
    def test_a_provider_hook_selects_the_target_before_the_workspace(self):
        declaration = self.declaration(
            target={
                "selection": "provider-hook",
                "hook": "tests.concorde.harness.test_host_tools:selection_hook",
            }
        )
        result = self.admit(declaration, data={"target_id": "x.y", "task": "Check"})
        self.assertEqual("described", result["status"], result)
        self.assertEqual(
            [(self.root.resolve(), {"target_id": "x.y", "task": "Check"})], HOOK_CALLS
        )
        [request] = self.dispatched
        self.assertEqual("Bound by hook", request.data["task"])
        self.assertFalse(request.mutates)
        self.assertEqual("Bound by hook", result["output"]["data"]["answer"])

    @verifies("scenario.admission.request-configuration")
    def test_initialization_takes_its_configuration_from_its_request(self):
        root = self.root / "fresh"
        root.mkdir()
        install_project_defaults(root, PACKAGE)
        subprocess.run(["git", "-C", str(root), "init", "-q", "-b", "main"], check=True)
        for key, value in (
            ("user.email", "fixture@example.invalid"),
            ("user.name", "Fixture"),
        ):
            subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "fresh"], check=True
        )
        self.assertFalse((root / ".concorde/config.json").exists())

        def init(data):
            return run_operation(
                "concorde-init",
                None,
                typed("concorde-init-request", data),
                host_context=OperationHost(root, PACKAGE),
            )

        proposed = init(
            {"action": "propose", "name": "Fresh", "configuration": CONFIGURATION}
        )
        self.assertEqual("succeeded", proposed["status"], proposed)
        self.assertFalse((root / ".concorde/config.json").exists())
        applied = init(
            {
                "action": "apply",
                "proposal": proposed["output"]["data"]["proposal"],
                "run_in_primary": True,
            }
        )
        self.assertEqual("succeeded", applied["status"], applied)
        self.assertEqual("applied", applied["output"]["data"]["status"])
        stored = json.loads((root / ".concorde/config.json").read_text())
        self.assertEqual(CONFIGURATION, stored["operation_configuration"])
        # An envelope configuration is refused: the request carries it.
        refused = run_operation(
            "concorde-init",
            CONFIGURATION,
            typed(
                "concorde-init-request",
                {"action": "propose", "name": "Fresh", "configuration": CONFIGURATION},
            ),
            host_context=OperationHost(root, PACKAGE),
        )
        self.assertEqual("blocked", refused["status"], refused)
        self.assertEqual(
            ("invalid_input", "/configuration"),
            (refused["errors"][0]["code"], refused["errors"][0]["field"]),
        )
