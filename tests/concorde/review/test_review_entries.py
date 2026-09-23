"""Each review Operation selects only its own reviewer."""

import unittest

from concorde.operations.catalog import CATALOG
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies


class ReviewEntryTests(unittest.TestCase):
    @verifies("scenario.review.separate-entries")
    def test_each_review_entry_uses_only_its_own_reviewer(self):
        for kind in ("spec", "code"):
            with self.subTest(kind=kind):
                operation = CATALOG[f"concorde-{kind}-review"]
                self.assertEqual(
                    ((f"{kind}_reviewer", f"{kind}-review"),), operation.agents
                )
                self.assertEqual(
                    {"target_id", "task"}, set(operation.request["required"])
                )
                typed(
                    f"concorde-{kind}-review-request",
                    {"target_id": "module.example", "task": "Inspect"},
                )


if __name__ == "__main__":
    unittest.main()
