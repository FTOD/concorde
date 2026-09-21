"""Finite native context admission shares currentness and assessment predicates."""

import builtins
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.native_context import execute
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.spec.repository import digest
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import PACKAGE, project


class NativeContextTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        project(self.root)
        before = Path.cwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.root)
        self.envelope = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-context-solve",
            "mode": "execute",
            "configuration": None,
            "input": typed(
                "concorde-context-solve-request",
                {"target_id": "service.transfer", "task": "Assess transfer"},
            ),
        }
        self.patch = patch(
            "concorde.harness.native_context.admit_native_runtime",
            return_value=NativeRuntimeBinding(
                FORMAT, str(self.root), "sha256:" + "0" * 64
            ),
        )
        self.patch.start()
        self.addCleanup(self.patch.stop)
        original = builtins.__import__

        def guard(name, *a, **kw):
            if name == "langgraph" or name.startswith("langgraph."):
                raise AssertionError("native context imported Graph")
            return original(name, *a, **kw)

        guard_patch = patch("builtins.__import__", guard)
        guard_patch.start()
        self.addCleanup(guard_patch.stop)

    def prepare(self):
        return execute(
            PACKAGE,
            "prepare",
            {
                "invocation": self.envelope,
                "native_root": str(self.root),
                "session_id": "unit",
            },
        )

    def command(self, prepared, action, payload):
        return execute(
            PACKAGE, action, payload, prepared["descriptor"], prepared["digest"]
        )

    def proposal(self, prepared):
        descriptor = json.loads(Path(prepared["descriptor"]).read_text())
        return {
            "invocation_id": prepared["ticket"],
            "result": typed(
                "concorde-agent-stage-result",
                {
                    "context_id": descriptor["snapshot"]["context_id"],
                    "outcome": "sufficient",
                    "answer": "Sufficient",
                    "blockers": [],
                    "documents": [],
                    "plan": "",
                    "tasks": [],
                },
            ),
        }

    @verifies("scenario.harness.native-context-public")
    def test_prepared_not_accepted_and_no_model_service(self):
        prepared = self.prepare()
        self.assertEqual(prepared["state"], "prepared", prepared)
        self.assertFalse(prepared["accepted"])
        self.assertEqual(prepared["call"]["agentScope"], "project")
        descriptor = json.loads(Path(prepared["descriptor"]).read_text())
        self.assertEqual(prepared["digest"], digest(descriptor))
        self.assertEqual(
            descriptor["launch"],
            {k: v for k, v in prepared["call"].items() if k != "gate"},
        )
        self.assertTrue(descriptor["assets"])
        value = self.command(prepared, "submit", self.proposal(prepared))
        self.assertFalse(value["accepted"])
        staged = self.command(prepared, "stage", {})
        self.assertEqual(staged["state"], "staged", staged)
        self.assertFalse(staged["accepted"])
        self.assertFalse(
            (Path(prepared["descriptor"]).parent / "terminal.json").exists()
        )

    @verifies("scenario.harness.native-context-public")
    def test_duplicate_or_foreign_submission_invalidates(self):
        for foreign in (False, True):
            with self.subTest(foreign=foreign):
                prepared = self.prepare()
                value = self.proposal(prepared)
                if foreign:
                    value["invocation_id"] = "foreign"
                else:
                    self.assertEqual(
                        self.command(prepared, "submit", value)["state"], "proposed"
                    )
                self.assertEqual(
                    self.command(prepared, "submit", value)["state"], "rejected"
                )
                self.assertEqual(
                    self.command(prepared, "stage", {})["state"], "rejected"
                )

    @verifies("scenario.harness.native-context-public")
    def test_configuration_registry_and_spec_changes_reject_currentness(self):
        for relative in (
            ".concorde/config.json",
            ".concorde/specs.json",
            "specs/transfer/module.md",
        ):
            with self.subTest(relative=relative):
                prepared = self.prepare()
                file = self.root / relative
                original = file.read_bytes()
                if relative.endswith("config.json"):
                    value = json.loads(original)
                    value["operation_configuration"]["data"]["model"] = (
                        "fixture/changed"
                    )
                    file.write_text(json.dumps(value))
                elif relative.endswith("specs.json"):
                    value = json.loads(original)
                    value["targets"].reverse()
                    file.write_text(json.dumps(value))
                else:
                    file.write_bytes(original + b"\nChanged contract\n")
                try:
                    self.assertEqual(
                        self.command(prepared, "check", {})["state"], "rejected"
                    )
                finally:
                    file.write_bytes(original)

    @verifies("scenario.harness.native-context-public")
    def test_policy_description_has_no_capsule_or_child(self):
        self.envelope["mode"] = "describe-policy"
        value = self.prepare()
        self.assertEqual(value["state"], "described")
        self.assertNotIn("descriptor", value)
        self.assertEqual(value["policy"]["enforcement"], "prompt-level")
