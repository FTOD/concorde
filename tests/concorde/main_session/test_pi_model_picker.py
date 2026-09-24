"""The pure part of the pi model picker, ``pi_models.ts``, run by Node against a listing.

The dialogs around it live in ``pi_extension.ts`` and need a pi session; these tests cover what the
picker offers for a ``concorde workers models`` listing, which command each choice becomes, and how
a refusal is shown.
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
LISTING = {
    "backend": "pi",
    "config": "/p/.concorde/worker-models.json",
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
    "configured": {
        "default": {"model": "anthropic/claude-sonnet-5", "reasoning": "low"},
        "task_types": {"implement": {"model": "local/plain-7"}},
    },
    "effective": {
        "understand": {
            "model": "anthropic/claude-sonnet-5",
            "reasoning": "low",
            "model_source": "pi.default",
            "reasoning_source": "pi.default",
        },
        "implement": {
            "model": "local/plain-7",
            "reasoning": "low",
            "model_source": "pi.task_types.implement",
            "reasoning_source": "pi.default",
        },
    },
}
REFUSAL = {
    "error": {
        "actor": "Workers (concorde workers set)",
        "code": "unknown_model",
        "detail": "'x' is not a pi model this machine lists",
        "unhandled": {
            "reason": "input",
            "explanation": "only listed models are admitted",
        },
        "options": ["choose a model from concorde workers models"],
        "causes": [
            {
                "actor": "pi",
                "code": "listing",
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
console.log(JSON.stringify({
  scopes: picker.scopeRows(listing),
  defaultModels: picker.modelRows(listing, "default"),
  implementModels: picker.modelRows(listing, "implement"),
  levelsPlain: picker.levelRows(listing, "local/plain-7"),
  levelsCurrent: picker.levelRows(listing, picker.currentModel(listing, "understand")),
  setDefault: picker.commandFor("default", "set", "local/plain-7", "off", null),
  setTask: picker.commandFor("implement", "keep", null, "high", "t1"),
  unset: picker.commandFor("implement", "unset", null, null, null),
  nothing: picker.commandFor("understand", "keep", null, picker.KEEP, null),
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
        scopes = [row["label"] for row in out["scopes"]]
        self.assertEqual(
            "All task types (default): anthropic/claude-sonnet-5, low", scopes[0]
        )
        self.assertIn("implement: local/plain-7, low (own setting)", scopes)
        self.assertEqual("Done", scopes[-1])
        self.assertEqual(
            ["keep", "set", "set"], [row["action"] for row in out["defaultModels"]]
        )
        self.assertEqual(
            ["keep", "unset", "set", "set"],
            [row["action"] for row in out["implementModels"]],
        )
        self.assertIn(
            "local/plain-7 (200K context, no reasoning)",
            [row["label"] for row in out["implementModels"]],
        )
        self.assertEqual(["Keep the current value", "off"], out["levelsPlain"])
        self.assertEqual(
            ["Keep the current value", "off", "low", "high"], out["levelsCurrent"]
        )
        self.assertEqual(
            [
                "workers",
                "set",
                "--backend",
                "pi",
                "--model",
                "local/plain-7",
                "--reasoning",
                "off",
            ],
            out["setDefault"],
        )
        self.assertEqual(
            [
                "workers",
                "set",
                "--backend",
                "pi",
                "--task-type",
                "implement",
                "--task",
                "t1",
                "--reasoning",
                "high",
            ],
            out["setTask"],
        )
        self.assertEqual(
            ["workers", "unset", "--backend", "pi", "--task-type", "implement"],
            out["unset"],
        )
        self.assertIsNone(out["nothing"])
        self.assertIn("Workers (concorde workers set): unknown_model", out["refusal"])
        self.assertIn("not handled: only listed models are admitted", out["refusal"])
        self.assertIn(
            "option: choose a model from concorde workers models", out["refusal"]
        )
        self.assertIn("\n  pi: listing: two models", out["refusal"])
        self.assertEqual("Traceback: boom", out["bare"])


if __name__ == "__main__":
    unittest.main()
