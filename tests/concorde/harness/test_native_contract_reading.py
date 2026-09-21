"""Focused regressions for specific reviewed contradictions, not semantic-completeness proof."""

import importlib
import json
import unittest

import operations
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class NativeContractReadingTests(unittest.TestCase):
    def text(self, name):
        return " ".join((REPOSITORY_ROOT / name).read_text().split())

    @verifies("scenario.harness.native-context-public")
    def test_security_explanations_distinguish_native_policy_from_actual_isolation(
        self,
    ):
        for name in ("execution", "permissions", "module"):
            with self.subTest(name=name):
                text = self.text("specs/concorde/harness/" + name + ".md")
                self.assertIn("prompt-level", text)
                self.assertIn("diagnostic/test", text)
                self.assertIn("read-only", text)
                self.assertNotIn(
                    "sandbox enforces the same grant on the process itself, so a shell command cannot write outside",
                    text,
                )
                self.assertNotIn(
                    "worker sandbox around that process bounds everything else it does",
                    text,
                )

    @verifies("scenario.harness.optional-operation")
    def test_canonical_inventory_and_explanation_have_no_retired_agent_alias_claim(
        self,
    ):
        text = self.text("specs/concorde/operations/execution-reference.md")
        self.assertNotIn("Agent** executable registry is retired", text)
        self.assertNotIn("Each entry under `operations/` declares `STATE`", text)
        self.assertIn("canonical Agent definitions", text)
        self.assertIn("no `STATE`/`run`", text)
        metadata = json.loads(
            (
                REPOSITORY_ROOT / "specs/concorde/operations/composition.md.json"
            ).read_text()
        )["extensions"]["concorde.operations"]
        roles = {x["id"].replace("-", "_") for x in metadata if x["kind"] == "agent"}
        self.assertEqual(roles, set(operations.AGENTS))
        for role in roles:
            module = importlib.import_module("operations." + role)
            self.assertFalse(hasattr(module, "STATE"))
            self.assertFalse(hasattr(module, "run"))

    @verifies("scenario.harness.native-context-public")
    def test_issue_review_and_catalog_current_contracts_do_not_retain_migration_promises(
        self,
    ):
        for file in (
            "specs/concorde/review/module.md",
            "specs/concorde/harness/execution-reference.md",
        ):
            text = self.text(file)
            self.assertNotIn("Issue solving temporarily retains", text)
            self.assertNotIn("trusted nested Issue verification until", text)
        text = self.text("specs/concorde/distribution/contracts.md")
        self.assertIn("catalog schema 2", text)
        self.assertNotIn(
            "catalog schema 1 and build-manifest schema 1 are unchanged", text
        )
        self.assertNotIn(
            "Pi catalog and build-manifest schema 1 remain unchanged", text
        )
