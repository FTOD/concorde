"""Promise-level Spec review impact: only Modules relying on a changed promise are consumers."""

import unittest

from concorde.review.impact import review_impact
from concorde.spec.impact import changed_nodes
from concorde.spec.verification import verifies
from tests.concorde.support.contract_project import (
    LEDGER_ENTRY,
    LEDGER_OBLIGATIONS,
    ContractProject,
)
from tests.concorde.support.spec_project import (
    update_module,
    uses,
)


class ReviewImpactTests(ContractProject, unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
