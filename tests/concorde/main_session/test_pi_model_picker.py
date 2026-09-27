"""The pi picker launches the shared editor with terminal restoration on every exit."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

SOURCE = REPOSITORY_ROOT / "src/concorde/main_session/pi_models.ts"


@unittest.skipUnless(shutil.which("node"), "Node is needed for the pi adapter")
class ModelPickerTests(unittest.TestCase):
    @verifies("scenario.main-session.pi-model-picker")
    def test_shared_editor_restores_terminal_and_uses_target_worktree(self):
        probe = """
import * as picker from SOURCE;
const calls = [];
const tui = {
  stop: () => calls.push("stop"),
  start: () => calls.push("start"),
  requestRender: (force) => calls.push(["render", force]),
};
const code = picker.runEditor(tui, ["python3", "scripts/concorde.py", ...picker.editorCommand()], "/task", (cmd, args, options) => {
  calls.push({cmd, args, cwd: options.cwd, stdio: options.stdio});
  return {status: 0};
});
let failed = false;
try {
  picker.runEditor(tui, ["missing"], "/task", () => { throw new Error("missing"); });
} catch { failed = true; }
const refusal = picker.refusalText({code: 1, text: "", value: {error: {
  actor: "command", code: "configuration_refused", detail: "invalid config",
  unhandled: {reason: "input", explanation: "the command cannot repair the file"},
  causes: [{actor: "Workers", code: "config_invalid", detail: "unknown worker", unhandled: {reason: "input", explanation: "catalog name required"}, causes: []}]
}}});
console.log(JSON.stringify({code, calls, failed, listing: picker.listingCommand(), refusal}));
""".replace("SOURCE", json.dumps(SOURCE.as_uri()))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probe.mts"
            path.write_text(probe)
            done = subprocess.run(
                ["node", "--experimental-strip-types", "--no-warnings", str(path)],
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, done.returncode, done.stderr)
        value = json.loads(done.stdout)
        self.assertEqual(0, value["code"])
        self.assertTrue(value["failed"])
        self.assertEqual(["configure-workers", "--show", "--json"], value["listing"])
        self.assertEqual(
            [
                "stop",
                {
                    "cmd": "python3",
                    "args": ["scripts/concorde.py", "configure-workers"],
                    "cwd": "/task",
                    "stdio": "inherit",
                },
                "start",
                ["render", True],
                "stop",
                "start",
                ["render", True],
            ],
            value["calls"],
        )
        self.assertIn("Workers: config_invalid: unknown worker", value["refusal"])
        self.assertIn(
            "not handled: input: the command cannot repair the file", value["refusal"]
        )
        self.assertIn("not handled: input: catalog name required", value["refusal"])
