"""The pure part of the pi model picker, ``pi_models.ts``, run by Node against a listing.

The dialogs around it live in ``pi_extension.ts`` and need a pi session; these tests cover what the
picker offers for the output of a ``configure_workers`` run, which command each choice becomes,
and how a refusal is shown.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SOURCE = REPOSITORY_ROOT / "src/concorde/main_session/pi_models.ts"


def chosen(model, reasoning, source="pi.default"):
    return {
        "model": model,
        "reasoning": reasoning,
        "model_source": source,
        "reasoning_source": "pi.default",
    }


LISTING = {
    "backend": "pi",
    "config": "/p/.concorde/worker-models.json",
    "candidates": {
        "reasoning_levels": ["off", "low", "high"],
        "models": [
            {
                "id": "anthropic/claude-sonnet-5",
                "reasoning": True,
                "levels": ["off", "low", "high"],
                "context": "1M",
            },
            {
                "id": "local/plain-7",
                "reasoning": False,
                "levels": ["off"],
                "context": "200K",
            },
        ],
    },
    "configured": {
        "default": {"model": "anthropic/claude-sonnet-5", "reasoning": "low"},
        "operations": {
            "spec_review": {"roles": {"checker": {"model": "local/plain-7"}}}
        },
    },
    "effective": {
        "understand": {"worker": chosen("anthropic/claude-sonnet-5", "low")},
        "spec_review": {
            "reviewer": chosen("anthropic/claude-sonnet-5", "low"),
            "checker": chosen(
                "local/plain-7", "low", "pi.operations.spec_review.roles.checker"
            ),
        },
    },
}
REFUSAL = {
    "error": {
        "actor": "Operation configure_workers r-1 (no task, /p)",
        "code": "configuration_refused",
        "detail": "'x' is not a pi model this machine lists",
        "unhandled": {
            "reason": "input",
            "explanation": "only listed models are admitted",
        },
        "options": ["choose a model from the candidates configure_workers lists"],
        "causes": [
            {
                "actor": "Workers (worker model configuration)",
                "code": "unknown_model",
                "detail": "two models",
                "unhandled": {"reason": "input", "explanation": "inner"},
                "options": [],
                "causes": [],
            }
        ],
    }
}
PROBE = """
import * as picker from %(source)s;
const listing = %(listing)s;
const scopes = picker.scopeRows(listing);
const checker = scopes.find((row) => row.label.startsWith("spec_review checker")).scope;
const understand = scopes.find((row) => row.label.startsWith("understand")).scope;
console.log(JSON.stringify({
  scopes,
  defaultModels: picker.modelRows(listing, { operation: null, role: null }),
  checkerModels: picker.modelRows(listing, checker),
  understandModels: picker.modelRows(listing, understand),
  levelsPlain: picker.levelRows(listing, "local/plain-7"),
  levelsCurrent: picker.levelRows(listing, picker.currentModel(listing, understand)),
  listing: picker.listingCommand(null),
  setDefault: picker.commandFor({ operation: null, role: null }, "set", "local/plain-7", "off", null),
  setChecker: picker.commandFor(checker, "keep", null, "high", "t1"),
  unsetChecker: picker.commandFor(checker, "unset", null, null, null),
  nothing: picker.commandFor(understand, "keep", null, picker.KEEP, null),
  refusal: picker.refusalText({ code: 1, value: %(refusal)s, text: "" }),
  bare: picker.refusalText({ code: 1, value: null, text: "Traceback: boom" }),
}));
"""


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_models.ts")
class ModelPickerTests(unittest.TestCase):
    def probe(self) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            probe = Path(directory) / "probe.mts"
            probe.write_text(
                PROBE
                % {
                    "source": json.dumps(SOURCE.as_uri()),
                    "listing": json.dumps(LISTING),
                    "refusal": json.dumps(REFUSAL),
                }
            )
            done = subprocess.run(
                ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, done.returncode, done.stderr)
        return json.loads(done.stdout)

    @verifies("scenario.main-session.pi-model-picker")
    def test_the_picker_offers_the_listing_and_applies_each_choice(self):
        out = self.probe()
        labels = [row["label"] for row in out["scopes"]]
        self.assertEqual(
            [
                "Every worker (default): anthropic/claude-sonnet-5, low",
                "understand: anthropic/claude-sonnet-5, low",
                "spec_review reviewer: anthropic/claude-sonnet-5, low",
                "spec_review checker: local/plain-7, low (own setting)",
                "Done",
            ],
            labels,
        )
        self.assertEqual(
            {"operation": "understand", "role": None}, out["scopes"][1]["scope"]
        )
        self.assertIsNone(out["scopes"][-1]["scope"])
        self.assertEqual(
            ["keep", "set", "set"], [row["action"] for row in out["defaultModels"]]
        )
        self.assertEqual(
            ["keep", "unset", "set", "set"],
            [row["action"] for row in out["checkerModels"]],
        )
        self.assertEqual(
            ["keep", "set", "set"], [row["action"] for row in out["understandModels"]]
        )
        self.assertIn(
            "local/plain-7 (200K context, no reasoning)",
            [row["label"] for row in out["checkerModels"]],
        )
        self.assertEqual(["Keep the current value", "off"], out["levelsPlain"])
        self.assertEqual(
            ["Keep the current value", "off", "low", "high"], out["levelsCurrent"]
        )
        base = ["run", "configure_workers", "--backend", "pi"]
        self.assertEqual(base, out["listing"])
        self.assertEqual(
            base + ["--model", "local/plain-7", "--reasoning", "off"], out["setDefault"]
        )
        self.assertEqual(
            base
            + ["--task", "t1", "--operation", "spec_review", "--role", "checker"]
            + ["--reasoning", "high"],
            out["setChecker"],
        )
        self.assertEqual(
            base + ["--operation", "spec_review", "--role", "checker", "--unset"],
            out["unsetChecker"],
        )
        self.assertIsNone(out["nothing"])
        self.assertIn(
            "configure_workers r-1 (no task, /p): configuration_refused", out["refusal"]
        )
        self.assertIn("not handled: only listed models are admitted", out["refusal"])
        self.assertIn(
            "\n  Workers (worker model configuration): unknown_model: two models",
            out["refusal"],
        )
        self.assertEqual("Traceback: boom", out["bare"])


if __name__ == "__main__":
    unittest.main()
