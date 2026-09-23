"""Multi-Module changes (change scope) and promise-level Spec review impact."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.harness.admission import run_operation
from concorde.harness.change_worktree import read_change
from concorde.spec.impact import change_scope, changed_nodes, review_impact
from concorde.spec.repository import SpecRepository
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    ModelProcessDouble,
    block,
    entry_of,
    project,
    update_module,
    uses,
)
from tests.concorde.support.native_planning import OperationHost

LEDGER_ENTRY = "specs/ledger/module.md"
LEDGER_OBLIGATIONS = "specs/ledger/obligations.md"
READ_CONTRACT = {
    "id": "contract.ledger.read",
    "version": 2,
    "schema": {"type": "integer"},
    "semantics": "Return the stored balance.",
    "example": 42,
}


class Fixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project(self.root)

    def repository(self, **options):
        return SpecRepository(self.root, PACKAGE, **options)

    def explain(self, module_id, anchor, text):
        path = self.root / entry_of(self.root, module_id)
        path.write_text(path.read_text() + f'\n<a id="{anchor}"></a>\n\n{text}\n')

    def participate(self, module_id, role, peer, version=2, contract=READ_CONTRACT):
        anchor = "participates-" + contract["id"].replace(".", "-")
        self.explain(module_id, anchor, "Balance reads follow the read contract.")
        update_module(
            self.root,
            module_id,
            participates=[
                {
                    "contract": contract["id"],
                    "version": version,
                    "role": role,
                    "peer": peer,
                    "meaning": "#" + anchor,
                }
            ],
        )

    def define_contract(self, path=LEDGER_OBLIGATIONS, contract=READ_CONTRACT):
        with (self.root / path).open("a") as stream:
            stream.write("\n## Contracts\n\n" + block("concorde-contract", contract))

    def snapshot(self, *paths):
        """Both members of each document, as a baseline override."""
        return {
            member: (self.root / member).read_bytes()
            for path in paths
            for member in (path, path + ".json")
        }

    def replace(self, path, old, new):
        file = self.root / path
        text = file.read_text()
        self.assertIn(old, text)
        file.write_text(text.replace(old, new))


class ChangeScopeTests(Fixture):
    @verifies("scenario.planning.change-scope")
    def test_scope_spans_composition_dependencies_references_contracts_and_shared_files(
        self,
    ):
        repository = self.repository()
        # Transfer uses the ledger; Banking relates its request concept to Transfers.
        self.assertEqual(
            ("module.ledger", "scope.bank", "service.transfer"),
            change_scope(repository, "service.transfer"),
        )
        # Transfer imports the ledger's Account concept, and Banking uses the ledger: a Module that
        # selects the owner's documents may have to follow its change.
        self.assertEqual(
            ("module.ledger", "scope.bank", "service.transfer"),
            change_scope(repository, "module.ledger"),
        )
        # Banking uses Audit, so it may have to follow an Audit change.
        self.assertEqual(
            ("scope.audit", "scope.bank"), change_scope(repository, "scope.audit")
        )
        # A contract Audit defines brings every participant, though Audit uses nobody.
        record = {**READ_CONTRACT, "id": "contract.audit.record"}
        self.define_contract("specs/audit/obligations.md", record)
        self.participate("scope.audit", "provided", "scope.bank", contract=record)
        self.participate("scope.bank", "required", "scope.audit", contract=record)
        repository = self.repository()
        self.assertEqual(
            ("scope.audit", "scope.bank"), change_scope(repository, "scope.audit")
        )
        # A participant's scope brings the contract's owner.
        self.assertIn("scope.audit", change_scope(repository, "scope.bank"))
        # A file bound by two Modules puts each in the other's scope.
        metadata = self.root / (LEDGER_ENTRY + ".json")
        value = json.loads(metadata.read_text())
        store = next(
            item
            for item in value["defines"]
            if item["id"] == "realization.ledger.store"
        )
        store["entries"].append("shared.txt")
        metadata.write_text(json.dumps(value, indent=2) + "\n")
        self.assertIn(
            "module.workspace", change_scope(self.repository(), "module.ledger")
        )
        self.assertIn(
            "module.ledger", change_scope(self.repository(), "module.workspace")
        )


class ReviewImpactTests(Fixture):
    def narrow_transfer(self):
        """Transfer relies only on the ledger's Account concept."""
        update_module(
            self.root,
            "service.transfer",
            uses=[
                uses(
                    "module.ledger",
                    "#uses-module-ledger",
                    relies_on=["concept.ledger.account"],
                )
            ],
        )

    def impact(self, *paths, edit):
        baseline = self.snapshot(*paths)
        edit()
        old = self.repository(document_overrides=baseline)
        return review_impact(old, self.repository(), None)

    @verifies("scenario.review.promise-impact")
    def test_narrowed_selection_of_unchanged_nodes_needs_no_review(self):
        self.narrow_transfer()
        # Prose outside every node definition: only whole-document selectors are concerned.
        impact = self.impact(
            LEDGER_ENTRY,
            edit=lambda: self.replace(
                LEDGER_ENTRY,
                "answers one read per account identity.",
                "answers exactly one read per account identity.",
            ),
        )
        self.assertEqual(("module.ledger", "scope.bank"), impact)

    @verifies("scenario.review.promise-impact")
    def test_a_changed_relied_on_definition_concerns_the_narrowed_consumer(self):
        self.narrow_transfer()
        impact = self.impact(
            LEDGER_ENTRY,
            edit=lambda: self.replace(
                LEDGER_ENTRY,
                "The identity of exactly one stored balance.",
                "The identity of one or more stored balances.",
            ),
        )
        self.assertEqual(("module.ledger", "scope.bank", "service.transfer"), impact)

    @verifies("scenario.review.promise-impact")
    def test_an_unselected_changed_document_concerns_only_whole_selectors(self):
        self.narrow_transfer()
        baseline = self.snapshot(LEDGER_OBLIGATIONS)
        self.replace(
            LEDGER_OBLIGATIONS, "THEN it raises KeyError", "THEN it raises LookupError"
        )
        old = self.repository(document_overrides=baseline)
        new = self.repository()
        self.assertEqual(
            ("scenario.ledger.unknown",), changed_nodes(old, new, [LEDGER_OBLIGATIONS])
        )
        self.assertEqual(("module.ledger", "scope.bank"), review_impact(old, new, None))
        # An unchanged document concerns nobody, whoever selects it.
        self.assertEqual((), review_impact(old, new, ["specs/transfer/module.md"]))

    @verifies("scenario.review.promise-impact")
    def test_a_changed_module_block_concerns_modules_relating_to_the_module(self):
        # Banking relates its request concept to Transfers and selects the transfer documents whole;
        # Audit, which uses nobody, is never concerned.
        impact = self.impact(
            "specs/transfer/module.md",
            edit=lambda: update_module(
                self.root, "service.transfer", title="Money transfers"
            ),
        )
        self.assertEqual(("scope.bank", "service.transfer"), impact)


class MultiModuleChangeTests(Fixture):
    """A contract version increment edits its provider and a consumer the provider does not use."""

    def setUp(self):
        super().setUp()
        self.define_contract()
        self.participate("module.ledger", "provided", "service.transfer")
        self.participate("service.transfer", "required", "module.ledger")
        for args in (
            ("init",),
            ("add", "."),
            (
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "Fixture baseline",
            ),
        ):
            subprocess.run(
                ("git", *args), cwd=self.root, capture_output=True, check=True
            )
        self.task = {
            "target_id": "module.ledger",
            "task": "Move the ledger read contract to version 3",
        }

    def call(self, operation, data=None):
        def callback(stage, snapshot, data, cwd):
            if stage == "tasks" and snapshot["target_id"] == "module.ledger":
                data["tasks"] = [
                    {
                        "id": "task.ledger.read-v3",
                        "target_id": "module.ledger",
                        "description": "Serve balance reads under version 3.",
                        "acceptance": "A known account returns its balance.",
                        "complete": False,
                    },
                    {
                        "id": "task.transfer.read-v3",
                        "target_id": "service.transfer",
                        "description": "Read balances under version 3.",
                        "acceptance": "Valid transfer subtracts; invalid amount raises ValueError.",
                        "complete": False,
                    },
                ]

        self.model = ModelProcessDouble(callback)
        host = OperationHost(
            self.root,
            PACKAGE,
            executor=self.model.executor,
            allow_primary_worktree=True,
        )
        return run_operation(
            operation,
            CONFIGURATION,
            typed(operation + "-request", data or self.task),
            host_context=host,
        )

    def bump_contract(self):
        self.replace(LEDGER_OBLIGATIONS, '"version": 2', '"version": 3')
        for module_id in ("module.ledger", "service.transfer"):
            path = self.root / (entry_of(self.root, module_id) + ".json")
            value = json.loads(path.read_text())
            participates = value["module"]["participates"]
            update_module(
                self.root,
                module_id,
                participates=[{**item, "version": 3} for item in participates],
            )

    @verifies(
        "scenario.planning.change-scope",
        "scenario.implementation.caller-components",
        "scenario.validation.multi-module",
        "scenario.review.multi-module",
    )
    def test_contract_increment_spans_provider_and_consumer_in_one_candidate(self):
        # The provider does not use its consumer.
        self.assertNotIn(
            "service.transfer",
            {
                item["target"]
                for item in self.repository().declarations["module.ledger"].uses
            },
        )
        self.bump_contract()
        for operation in ("plan", "tasks"):
            result = self.call("concorde-" + operation)
            self.assertEqual("succeeded", result["status"], result)
        change = read_change(self.root, required=True)
        self.assertEqual(
            ["module.ledger", "service.transfer"],
            [task["target_id"] for task in change["targets"]["module.ledger"]["tasks"]],
        )
        # The consumer's work is its own single-Module implementation in the same candidate.
        result = self.call("concorde-implement")
        self.assertEqual("unsupported", result["output"]["data"]["outcome"], result)
        self.assertEqual([], self.model.calls)
        from concorde.implementation.implement import component_intent

        component = {
            "target_id": "service.transfer",
            "task": component_intent(change["targets"]["module.ledger"]["tasks"][1:]),
        }
        for operation in ("plan", "tasks", "implement", "validate"):
            result = self.call("concorde-" + operation, component)
            self.assertEqual("succeeded", result["status"], result)
            if operation == "implement":
                self.assertEqual(
                    ["service.transfer"],
                    [call["snapshot"]["target_id"] for call in self.model.calls],
                )
        result = self.call("concorde-implement")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(
            ["module.ledger"],
            [call["snapshot"]["target_id"] for call in self.model.calls],
        )
        # The change's Module's reviews cover every Module the candidate edits: the consumer's
        # changed entry and code, and Banking, which selects the changed ledger documents whole.
        from concorde.harness.invocation import Invocation
        from concorde.review.review import code_review_peers, spec_consumers

        owner = Invocation(
            "concorde-spec-review",
            CONFIGURATION,
            self.task,
            OperationHost(self.root, PACKAGE, allow_primary_worktree=True),
        )
        self.assertEqual({"scope.bank", "service.transfer"}, spec_consumers(owner))
        self.assertEqual(
            ["service.transfer"], [module.id for module in code_review_peers(owner)]
        )
        # Validating the change's Module covers every Module the candidate edits.
        result = self.call("concorde-validate")
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual("ready", result["output"]["data"]["outcome"])
        self.assertEqual(
            {"service.transfer"},
            {item["target_id"] for item in result["output"]["data"]["checks"]},
        )
        state = read_change(self.root, required=True)["targets"]["module.ledger"]
        self.assertEqual(
            ["module.ledger", "service.transfer"],
            sorted(item["target_id"] for item in state["implementation_impacts"]),
        )
        # A later edit of the consumer's code makes the owner's evidence stale.
        code = self.root / "app/transfer.py"
        code.write_text(code.read_text() + "\n# changed after validation\n")
        from concorde.spec.repository import SpecError
        from concorde.validation.validate import verify_completion

        with self.assertRaises(SpecError):
            verify_completion(
                Invocation(
                    "concorde-validate",
                    CONFIGURATION,
                    self.task,
                    OperationHost(self.root, PACKAGE, allow_primary_worktree=True),
                )
            )

    @verifies("scenario.planning.change-scope")
    def test_a_task_outside_the_change_scope_is_refused(self):
        def outside(stage, snapshot, data, cwd):
            if stage == "tasks":
                data["tasks"][0]["target_id"] = "scope.audit"

        for operation in ("plan", "tasks"):
            self.model = ModelProcessDouble(outside)
            host = OperationHost(
                self.root,
                PACKAGE,
                executor=self.model.executor,
                allow_primary_worktree=True,
            )
            result = run_operation(
                "concorde-" + operation,
                CONFIGURATION,
                typed("concorde-" + operation + "-request", self.task),
                host_context=host,
            )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("permission_denied", result["errors"][0]["code"], result)


if __name__ == "__main__":
    unittest.main()
