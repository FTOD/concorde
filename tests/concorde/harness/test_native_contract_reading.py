"""Focused regressions for specific reviewed contradictions, not semantic-completeness proof."""

import importlib
import json
import unittest

import agents
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
            (REPOSITORY_ROOT / "specs/concorde/agents/roles.md.json").read_text()
        )["extensions"]["concorde.agents"]
        roles = {x["id"].replace("-", "_") for x in metadata if x["family"] == "domain"}
        self.assertEqual(roles, set(agents.DOMAIN_AGENTS))
        for role in roles:
            module = importlib.import_module("agents." + role)
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

    @verifies(
        "scenario.harness.native-context-public", "scenario.harness.optional-operation"
    )
    def test_related_precise_reading_and_scenarios_follow_the_actual_backend(self):
        defects = {
            "harness/requirements": [
                "nothing outside the grant is readable",
                "For the native context-assessor this is intended read policy",
            ],
            "harness/scenarios": [
                "actual admission, operation branches",
                "selects the operation's declared execution Graph",
                "no worker ever runs unconfined",
            ],
            "review/execution-reference": [
                "Studio also admits these public Operations directly"
            ],
            "review/scenarios": ["or its Studio entry"],
            "spec/module": ["retained explicit Studio adapter"],
            "spec/initialize": ["explicit Studio adapter retains"],
            "distribution/module": [
                "explicit Studio adapter uses",
                "Except for native context preparation",
            ],
            "validation/module": ["Explicit Studio execution selects"],
            "delivery/module": ["explicit Studio adapter selects"],
            "issues/module": ["executes declared transitions with| langgraph"],
            "issues/scenarios": ["WHEN the graph selects its response"],
            "planning/module": [
                "Other capabilities keep their existing graph implementations"
            ],
            "distribution/build": ["concatenates the shared common worker rules"],
            "distribution/requirements": ["seven legacy terminal worker renderings"],
        }
        for name, phrases in defects.items():
            with self.subTest(unit=name):
                text = self.text("specs/concorde/" + name + ".md")
                for phrase in phrases:
                    self.assertNotIn(phrase, text)
        # Actual declared topology and render inventory are checked independently of those strings.
        from concorde.distribution.build import build
        from concorde.operations.graph_catalog import catalog

        self.assertEqual(set(catalog()), {"terminal_agent_operation"})
        outputs = {o.path: o.content for o in build(REPOSITORY_ROOT).outputs}
        roles = {r.replace("_", "-") for r in agents.DOMAIN_AGENTS}
        self.assertEqual(len(roles), 7)
        self.assertEqual(
            {p for p in outputs if p.startswith("generated/native/")},
            {"generated/native/" + r + ".md" for r in roles},
        )
        for role in roles:
            self.assertEqual(
                outputs["generated/native/" + role + ".md"],
                outputs["generated/agents/" + role + ".md"],
            )
