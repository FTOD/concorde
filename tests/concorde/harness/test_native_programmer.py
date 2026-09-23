"""Opt-in native programmer integration with scripted reasoning, real tools and publication."""

import os
import unittest

from concorde.spec.verification import verifies
from tests.concorde.support.native_probe import run_native_probe


@unittest.skipUnless(
    os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
    and os.environ.get("CONCORDE_NATIVE_PI"),
    "explicit native roots required",
)
class NativeProgrammerTests(unittest.TestCase):
    @verifies("scenario.implementation.native-programmer")
    def test_native_programmer_real_candidate_tools(self):
        cases = os.environ.get(
            "CONCORDE_NATIVE_IMPLEMENT_CASES",
            "success feedback tampered-feedback incomplete foreign-task malformed native-failure cancel stale-spec stale-plan stale-tasks stale-feedback missing-components missing-tasks stale-before",
        ).split()
        run_native_probe(self, "native_programmer_probe.mjs", cases)
