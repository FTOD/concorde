"""Spec context selection, context identity and the authority it never grants (Protocol 14)."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import (
    PACKAGE,
    block,
    entry_of,
    read_json,
    source_pairs,
    sync_registry,
    update_module,
)

PROMISES = {
    "kind": "document",
    "target": "document.transfer.promises",
    "reason": "the transfer amount rules",
}


def uses(target, meaning="#uses-extra", **extra):
    return {"target": target, "meaning": meaning, **extra}


class ContextSelectionTests(unittest.TestCase):
    def setUp(self):
        from tests.concorde.support.spec_project import project

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        project(self.root)

    def repository(self):
        return SpecRepository(self.root, PACKAGE)

    def explain(self, module_id, anchor, text):
        """Add an explanation anchor to a Module's entry reading."""
        path = self.root / entry_of(self.root, module_id)
        path.write_text(path.read_text() + f'\n<a id="{anchor}"></a>\n\n{text}\n')

    def audit_uses_transfer(self, **extra):
        self.explain(
            "scope.audit", "uses-transfer", "Audit reads the transfer promises."
        )
        update_module(
            self.root,
            "scope.audit",
            uses=[uses("service.transfer", "#uses-transfer", **extra)],
        )

    @verifies("scenario.spec.reference-resolution")
    def test_selection_is_one_level_and_every_document_keeps_its_owner_and_reasons(
        self,
    ):
        self.audit_uses_transfer()
        update_module(self.root, "scope.audit", includes=[PROMISES])
        r = self.repository()
        resolved = r.spec_context("scope.audit").value
        paths = [source["path"] for source in resolved["sources"]]
        self.assertEqual(sorted(set(paths)), paths)
        # Transfer uses the ledger, but Audit's selection never follows Transfer's own relations.
        self.assertNotIn("specs/ledger/module.md", paths)
        self.assertIn("specs/transfer/obligations.md", paths)
        promise = next(
            s
            for s in resolved["sources"]
            if s["document_id"] == "document.transfer.promises"
        )
        self.assertEqual("service.transfer", promise["owner"])
        self.assertEqual(
            [
                {
                    "relation": "includes",
                    "kind": "document",
                    "id": "document.transfer.promises",
                },
                {"relation": "uses", "id": "service.transfer"},
            ],
            promise["reasons"],
        )
        entry = next(
            s for s in resolved["sources"] if s["path"] == "specs/audit/module.md"
        )
        self.assertEqual([{"relation": "owns", "id": "scope.audit"}], entry["reasons"])
        # A context record carries only Protocol relations: sharing a file adds nothing.
        self.assertEqual(3, resolved["schema_version"])
        self.assertNotIn("shares", resolved)
        scenario = r.spec_context("scenario.transfer.debit").value
        self.assertEqual("service.transfer", scenario["module_id"])
        self.assertIn(
            "specs/ledger/module.md", [s["path"] for s in scenario["sources"]]
        )
        self.assertEqual(
            r.spec_context("service.transfer").paths,
            r.spec_context("scenario.transfer.debit").paths,
        )
        self.assertEqual(
            ("scope.audit", "scope.bank", "service.transfer"),
            r.selected_by("document.transfer.promises"),
        )
        self.assertEqual(
            ["scenario.bank.settlement"],
            [s.id for s in r.scenarios(r.module("scope.bank"))],
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertIn(
            "CHK.includes.redundant",
            {f.rule_id for f in report.findings if f.severity == "warning"},
        )

    @verifies("scenario.spec.reference-resolution")
    def test_every_relation_that_selects_a_document_is_recorded(self):
        before = self.repository().spec_context("scope.bank").value
        update_module(
            self.root,
            "scope.bank",
            includes=[
                {
                    "kind": "module",
                    "target": "service.transfer",
                    "reason": "the transfer promises the settlement reports",
                }
            ],
        )
        after = self.repository().spec_context("scope.bank").value
        promise = next(
            s for s in after["sources"] if s["path"] == "specs/transfer/promises.md"
        )
        self.assertEqual(
            [
                {"relation": "includes", "kind": "module", "id": "service.transfer"},
                {"relation": "uses", "id": "service.transfer"},
            ],
            promise["reasons"],
        )
        # The redundant inclusion selects nothing new, yet it changes the context identity.
        self.assertEqual(
            [s["path"] for s in before["sources"]],
            [s["path"] for s in after["sources"]],
        )
        self.assertNotEqual(digest(before), digest(after))

    @verifies("scenario.spec.relies-on")
    def test_relies_on_selects_the_entry_and_the_defining_documents_only(self):
        self.audit_uses_transfer(relies_on=["req.transfer.pure"])
        r = self.repository()
        paths = [
            source["path"] for source in r.spec_context("scope.audit").value["sources"]
        ]
        self.assertEqual(
            source_pairs(
                [
                    "specs/audit/module.md",
                    "specs/audit/obligations.md",
                    "specs/transfer/module.md",
                    "specs/transfer/obligations.md",
                ]
            ),
            paths,
        )
        self.assertNotIn("specs/transfer/promises.md", paths)
        self.assertEqual(
            "success", validate_repository(self.root, package_root=PACKAGE).status
        )

    @verifies("scenario.spec.impact-indexes")
    def test_impact_indexes_name_whom_a_change_concerns(self):
        from tests.concorde.support.spec_project import set_realization

        self.audit_uses_transfer(relies_on=["req.transfer.pure"])
        update_module(
            self.root,
            "module.ledger",
            includes=[
                {
                    "kind": "document",
                    "target": "document.transfer.feature.obligations",
                    "reason": "the purity rule the store must respect",
                }
            ],
        )
        set_realization(
            self.root,
            "realization.ledger.store",
            entries=["app/ledger.py", "app/transfer.py"],
        )
        r = self.repository()
        scopes = {module: r.spec_scope(module) for module in r.modules}
        self.assertEqual(
            ("module.ledger", "scope.audit", "scope.bank", "service.transfer"),
            r.selected_by("document.transfer.feature.obligations"),
        )
        self.assertEqual(
            [
                {
                    "document": "specs/audit/module.md",
                    "module": "scope.audit",
                    "relation": "relies_on",
                }
            ],
            list(r.referenced_by("req.transfer.pure")),
        )
        self.assertEqual(
            ("service.transfer", "module.ledger"), r.implemented_by("app/transfer.py")
        )
        self.assertEqual(
            ("module.ledger", "scope.audit", "service.transfer"),
            r.impact(nodes=["req.transfer.pure"], paths=["app/transfer.py"]),
        )
        self.assertEqual(scopes, {module: r.spec_scope(module) for module in r.modules})
        self.assertNotIn("specs/transfer/obligations.md", r.spec_scope("scope.audit"))

    @verifies("scenario.spec.query-files", "scenario.spec.query-invalid-target")
    def test_spec_files_read_no_bodies_and_refuse_other_identities(self):
        update_module(self.root, "scope.audit", includes=[PROMISES])
        r = self.repository()
        with patch.object(r, "document", side_effect=AssertionError("body read")):
            self.assertEqual(
                tuple(
                    source_pairs(
                        [
                            "specs/audit/module.md",
                            "specs/audit/obligations.md",
                            "specs/transfer/promises.md",
                        ]
                    )
                ),
                r.spec_context("scope.audit").paths,
            )
        for identity in (
            "document.bank",
            "req.transfer.pure",
            "concept.ledger.account",
            "realization.ledger.store",
            "specs/bank/module.md",
        ):
            with (
                self.subTest(identity=identity),
                self.assertRaises(SpecError) as caught,
            ):
                r.spec_context(identity).paths
            self.assertEqual("invalid_target", caught.exception.code)

    @verifies("scenario.spec.reject-inconsistent-inventory")
    def test_unreadable_documents_never_yield_a_partial_context(self):
        update_module(self.root, "scope.audit", includes=[PROMISES])
        path = self.root / "specs/transfer/promises.md"
        raw = path.read_bytes()
        for replacement in (None, raw + b"\xff"):
            with self.subTest(replacement=replacement):
                if replacement is None:
                    path.unlink()
                else:
                    path.write_bytes(replacement)
                with self.assertRaises(SpecError):
                    self.repository().spec_context("scope.audit")
                self.assertEqual(
                    "invalid",
                    validate_repository(self.root, package_root=PACKAGE).status,
                )
                path.write_bytes(raw)
        metadata = Path(str(path) + ".json")
        value = json.loads(metadata.read_text())
        value["document"]["owner"] = "module.ledger"
        metadata.write_text(json.dumps(value))
        with self.assertRaisesRegex(SpecError, "owner"):
            self.repository()

    def test_duplicate_ownership_stops_loading(self):
        owns = read_json(self.root, "specs/bank/module.md.json")["module"]["owns"]
        update_module(
            self.root, "scope.bank", owns=[*owns, "specs/transfer/promises.md"]
        )
        with self.assertRaisesRegex(SpecError, "CHK.owns.unique"):
            self.repository()
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertIn("CHK.owns.unique", {f.rule_id for f in report.findings})

    @verifies("scenario.spec.participation")
    def test_contract_participants_need_the_definition_in_context(self):
        definition = {
            "id": "contract.ledger.read",
            "version": 2,
            "schema": {"type": "integer"},
            "semantics": "Return the stored balance.",
            "example": 42,
        }
        with (self.root / "specs/ledger/obligations.md").open("a") as stream:
            stream.write("\n## Contracts\n\n" + block("concorde-contract", definition))
        for module_id, role, peer, anchor in (
            ("module.ledger", "provided", "service.transfer", "reads-balance"),
            ("service.transfer", "required", "module.ledger", "reads-balance"),
        ):
            self.explain(
                module_id, anchor, "Balance reads follow the ledger read contract."
            )
            update_module(
                self.root,
                module_id,
                participates=[
                    {
                        "contract": "contract.ledger.read",
                        "version": 2,
                        "role": role,
                        "peer": peer,
                        "meaning": "#" + anchor,
                    }
                ],
            )
        r = self.repository()
        self.assertEqual((), r.contracts(r.module("service.transfer")))
        self.assertEqual(
            "module.ledger", r.contracts(r.module("module.ledger"))[0]["owner"]
        )
        self.assertEqual(
            ("module.ledger", "service.transfer"),
            tuple(item["module"] for item in r.referenced_by("contract.ledger.read")),
        )
        self.assertEqual(
            "success", validate_repository(self.root, package_root=PACKAGE).status
        )
        # Narrowing to a promise defined next to the contract keeps its definition in context.
        self.explain(
            "service.transfer", "uses-ledger-narrowly", "Only balance reads matter."
        )
        for relies_on, reconciled in (
            (["scenario.ledger.read"], []),
            (["concept.ledger.account"], ["service.transfer"]),
        ):
            with self.subTest(relies_on=relies_on):
                update_module(
                    self.root,
                    "service.transfer",
                    uses=[
                        uses(
                            "module.ledger",
                            "#uses-ledger-narrowly",
                            relies_on=relies_on,
                        )
                    ],
                )
                findings = validate_repository(self.root, package_root=PACKAGE).findings
                self.assertEqual(
                    reconciled,
                    [
                        f.subject_id
                        for f in findings
                        if f.rule_id == "CHK.context.reconciled"
                    ],
                )

    def test_ownership_transfer_changes_every_selecting_context(self):
        update_module(self.root, "module.ledger", includes=[PROMISES])
        old = self.repository()
        old.context_identities()
        transfer = read_json(self.root, "specs/transfer/module.md.json")["module"][
            "owns"
        ]
        audit = read_json(self.root, "specs/audit/module.md.json")["module"]["owns"]
        update_module(
            self.root,
            "service.transfer",
            owns=[path for path in transfer if not path.endswith("promises.md")],
        )
        update_module(
            self.root, "scope.audit", owns=[*audit, "specs/transfer/promises.md"]
        )
        path = self.root / "specs/transfer/promises.md.json"
        path.write_bytes(
            path.read_bytes().replace(b'"service.transfer"', b'"scope.audit"')
        )
        sync_registry(self.root)
        self.assertEqual(
            ("module.ledger", "scope.audit", "scope.bank", "service.transfer"),
            old.affected_contexts(self.repository()),
        )


if __name__ == "__main__":
    unittest.main()
