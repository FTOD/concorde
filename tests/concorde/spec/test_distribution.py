"""Installed source closure and the Pi completion adapter, with explicit process doubles."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.distribution.package_validation import validate_package
from concorde.spec.boundaries import scope_roots
from agents import AGENTS
from concorde.harness.worker_profile import bind_agent, load_instructions
from concorde.operations.catalog import OPERATION_NAMES
from concorde.spec.repository import SpecRepository
from concorde.spec.typed_data import typed
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies

from tests.concorde.support.spec_project import PACKAGE, project


class DistributionTests(unittest.TestCase):
    def test_catalog_roles_and_exported_schemas_are_executable_package_contracts(self):
        self.assertEqual([], validate_package(PACKAGE))
        agents = tuple("concorde-" + name.replace("_", "-") for name in AGENTS)
        self.assertEqual(11, len(OPERATION_NAMES))
        self.assertEqual(7, len(agents))
        self.assertIn("concorde-context-solve", OPERATION_NAMES)
        self.assertNotIn("concorde-ask", OPERATION_NAMES)
        self.assertNotIn("concorde-planner", OPERATION_NAMES)
        for role in agents:
            binding = bind_agent(PACKAGE, role)
            self.assertEqual(role, "concorde-" + binding.agent.replace("_", "-"))
            self.assertTrue(load_instructions(PACKAGE, binding).strip())
            self.assertIsNotNone(binding.effects)

    @verifies(
        "scenario.spec.admit-inventory",
        "scenario.spec.shared-file",
        "scenario.spec.validate-success",
    )
    def test_self_architecture_lists_every_implementation_file_under_an_entity(self):
        repo = SpecRepository(PACKAGE)
        report = validate_repository(PACKAGE)
        self.assertEqual("success", report.status, [f.message for f in report.findings])
        self.assertEqual("module.concorde", repo.module("module.agents").parent)
        self.assertEqual("module.concorde", repo.module("module.operations").parent)
        self.assertTrue(all(t.kind == "module" for t in repo.modules.values()))
        self.assertEqual("module.concorde", repo.module("module.views").parent)
        self.assertIn(
            "src/concorde/views",
            scope_roots(repo.implementation_scope("module.views")),
        )
        for target in repo.modules.values():
            self.assertEqual(
                list(target.files), sorted(repo.realization_entries(target))
            )
        shared = {
            path
            for module in repo.modules.values()
            for paths in repo.shared_files(module).values()
            for path in paths
        }
        # A shared file, where the project has one, is implemented by every Module binding it.
        for path in shared:
            self.assertLess(1, len(repo.implemented_by(path)), path)
            self.assertEqual(
                sorted(repo.implemented_by(path)), list(repo.impact(paths=[path]))
            )
        test = "tests/concorde/operations/test_change_scope.py"
        self.assertEqual(
            sorted(repo.implemented_by(test)), list(repo.impact(paths=[test]))
        )
        # Every capability's request is described in the Spec of the Module that owns it.
        from concorde.operations.catalog import CATALOG

        for op in OPERATION_NAMES:
            text = "\n".join(
                repo.source_bytes(path).decode()
                for path in repo.spec_context(CATALOG[op].owner).paths
            )
            self.assertIn(op + "-request", text)

    def test_launcher_refuses_a_nonpublic_operation_name_and_accepts_a_public_operation(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            launcher = str(PACKAGE / "scripts/run-operation.py")
            internal_command = [sys.executable, launcher, "concorde-planner"]
            internal_value = {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": "concorde-planner",
                "mode": "execute",
                "configuration": None,
                "input": typed(
                    "concorde-plan-request",
                    {"target_id": "service.transfer", "task": "Explain transfer"},
                ),
            }
            result = subprocess.run(
                internal_command,
                input=json.dumps(internal_value),
                capture_output=True,
                text=True,
                cwd=root,
            )
            self.assertEqual(3, result.returncode, result.stdout + result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual("blocked", output["status"])
            self.assertEqual("unknown_operation", output["errors"][0]["code"])
            public_command = [sys.executable, launcher, "concorde-issues"]
            public_value = {
                "type_id": "concorde-operation-invocation",
                "schema_version": 3,
                "operation_id": "concorde-issues",
                "mode": "describe-policy",
                "configuration": None,
                "input": typed("concorde-issues-request", {"action": "list"}),
            }
            result = subprocess.run(
                public_command,
                input=json.dumps(public_value),
                capture_output=True,
                text=True,
                cwd=root,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("described", json.loads(result.stdout)["status"])
            result = subprocess.run(
                public_command + ["--feature-path", "specs/transfer/module.md"],
                input=json.dumps(public_value),
                capture_output=True,
                text=True,
                cwd=root,
            )
            self.assertEqual(3, result.returncode)
            self.assertEqual("blocked", json.loads(result.stdout)["status"])
