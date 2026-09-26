"""The error chain: links, their schema, exceptions as links and the rendering for a human."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde import errors
from concorde.spec.schema import ContractError, admit, validate


def check_link(detail: str = "check.a failed with exit code 1") -> dict:
    return errors.link(
        "check",
        "check.a",
        "check_failed",
        detail,
        reason="capability",
        explanation="a check only measures",
    )


class ErrorChainTests(unittest.TestCase):
    def chain(self) -> dict:
        harness = errors.link(
            "workers",
            "Workers run w-1",
            "checks_failed",
            "1 check still fails after 2 rounds",
            reason="exhausted",
            explanation="the rounds are used up",
            attempts=["round 1", "round 2"],
            causes=[check_link(), None],
        )
        return errors.link(
            "operation",
            "Operation implement r-1",
            "checks_failed",
            "the worker run ended failed",
            reason="decision",
            explanation="more rounds are the main agent's decision",
            options=["run again"],
            recommendation="run again",
            causes=[harness],
        )

    def test_a_chain_conforms_to_the_contract(self):
        chain = self.chain()
        validate(chain, errors.ERROR_SCHEMA)
        self.assertEqual(
            ["checks_failed", "checks_failed", "check_failed"], errors.codes(chain)
        )
        self.assertEqual(["check.a"], [item["actor"] for item in errors.origins(chain)])
        self.assertEqual(
            1, len(chain["causes"][0]["causes"]), "None causes are dropped"
        )

    def test_the_schemas_are_admitted_by_the_contract_subset(self):
        admit(errors.ERROR_SCHEMA)
        admit(errors.WORKER_ERROR_SCHEMA)

    def test_a_link_without_a_detail_or_reason_is_refused(self):
        with self.assertRaises(ValueError):
            errors.link(
                "boss", "x", "code", "detail", reason="decision", explanation="x"
            )
        with self.assertRaises(ValueError):
            errors.link(
                "check", "x", "code", "detail", reason="because", explanation="x"
            )
        bad = check_link()
        bad["detail"] = ""
        with self.assertRaises(ContractError):
            validate(bad, errors.ERROR_SCHEMA)
        bad = check_link()
        del bad["unhandled"]
        with self.assertRaises(ContractError):
            validate(bad, errors.ERROR_SCHEMA)

    def test_an_exception_becomes_a_link_with_its_output_and_traceback(self):
        try:
            subprocess.run(
                ["sh", "-c", "echo 'no such ref' >&2; exit 3"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as error:
            with tempfile.TemporaryDirectory() as directory:
                trace = Path(directory) / "trace.txt"
                link = errors.from_exception("git rev-parse", error, trace=trace)
                self.assertIn("CalledProcessError", trace.read_text())
        self.assertEqual("component", link["level"])
        self.assertIn("exit status 3", link["detail"])
        self.assertIn("no such ref", link["detail"])
        kinds = [item["kind"] for item in link["evidence"]]
        self.assertEqual(["traceback", "raised-at"], kinds)
        validate(link, errors.ERROR_SCHEMA)

    def test_the_rendering_shows_every_level_and_reason(self):
        text = errors.render(self.chain())
        for fragment in (
            "**operation** Operation implement r-1: `checks_failed`",
            "Not handled here (decision): more rounds are the main agent's decision",
            "Caused by:",
            "  - **workers** Workers run w-1",
            "Tried: round 1",
            "    - **check** check.a: `check_failed`",
            "Recommendation: run again",
        ):
            self.assertIn(fragment, text)
        multiline = check_link("check.a failed; its log ends with:\nE boom\nE bang")
        self.assertIn("  | E boom\n  | E bang", errors.render(multiline))


if __name__ == "__main__":
    unittest.main()
