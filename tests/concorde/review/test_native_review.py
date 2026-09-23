"""Opt-in native review-scope integration with scripted reasoning, real tools and publication."""

import os
import unittest

from concorde.spec.verification import verifies
from tests.concorde.support.native_probe import run_native_probe


@unittest.skipUnless(
    os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
    and os.environ.get("CONCORDE_NATIVE_PI"),
    "explicit native roots required",
)
class NativeReviewTests(unittest.TestCase):
    @verifies("scenario.review.native-scope")
    def test_native_review_scope(self):
        cases = os.environ.get(
            "CONCORDE_NATIVE_REVIEW_CASES",
            "clean managed code-clean code-shared code-parent advisory blocking incomplete wrong-context wrong-mode wrong-receipt coverage stale native-failure missing budget shared many",
        ).split()
        run_native_probe(self, "native_review_probe.mjs", cases)


if __name__ == "__main__":
    unittest.main()
