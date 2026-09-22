"""Explicit source-to-installed fixture provenance, not selection weakening."""

import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.install_output_handoff import (
    install_selected_fixture,
    output_environment,
)
from tests.concorde.support.managed_runtime import independent_runtime_environment
from tests.concorde.support.paths import REPOSITORY_ROOT


class HandoffPolicyTests(unittest.TestCase):
    def test_environment_separation_is_local_and_narrow(self):
        source = {
            "CONCORDE_SESSION_SELECTION": "source-selection",
            "CONCORDE_NATIVE_PROJECT_ROOT": "source-data",
            "PYTHONPATH": "source-path",
            "PATH": "unchanged",
            "OTHER": "preserved",
            "PI_SUBAGENT_EXTENSION_BINDINGS": json.dumps(
                {
                    "concorde/1": {"selection": "source-selection"},
                    "other/1": {"opaque": "preserve"},
                }
            ),
        }
        child = output_environment(source)
        self.assertEqual(source["CONCORDE_SESSION_SELECTION"], "source-selection")
        self.assertNotIn("CONCORDE_SESSION_SELECTION", child)
        self.assertEqual(child["OTHER"], "preserved")
        self.assertEqual(
            json.loads(child["PI_SUBAGENT_EXTENSION_BINDINGS"]),
            {"other/1": {"opaque": "preserve"}},
        )
        with self.assertRaises(ValueError):
            output_environment({"CONCORDE_STUDIO_URL": "http://localhost:2024"})

    def test_outside_scratch_and_missing_governing_selection_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)
            with patch.dict(
                os.environ,
                {
                    "CONCORDE_CHECK_TMPDIR": str(scratch),
                    "CONCORDE_SESSION_SELECTION": "wrong",
                },
            ):
                for target in (scratch, REPOSITORY_ROOT, scratch / "consumer"):
                    with self.assertRaises(ValueError):
                        install_selected_fixture(target, Path("/not-selected"))

    @unittest.skipUnless(
        os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
        and os.environ.get("CONCORDE_NATIVE_PI"),
        "explicit native roots required",
    )
    @verifies(
        "scenario.harness.native-context-public",
        "scenario.harness.check-read-only",
        "scenario.distribution.install-local-worktree",
    )
    def test_readonly_tester_installs_selected_output_and_runs_native_smoke(self):
        with tempfile.TemporaryDirectory(
            prefix="concorde-install-handoff-input-"
        ) as temporary:
            environment = independent_runtime_environment(
                Path(temporary), REPOSITORY_ROOT
            )
            environment["NPM_CONFIG_OFFLINE"] = (
                "false"  # Locked acquisition writes only issued scratch.
            )
            environment.update(
                CONCORDE_SESSION_SELECTION=str(
                    REPOSITORY_ROOT / ".concorde/work/pi-first-repair-selection.json"
                ),
                PYTHONPATH=str(REPOSITORY_ROOT / "src"),
            )
            argv = [
                sys.executable,
                str(
                    REPOSITORY_ROOT
                    / "tests/concorde/distribution/installed_output_probe.py"
                ),
                os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                os.environ["CONCORDE_NATIVE_PI"],
            ]
            governing = Path(temporary) / "governing"
            governing.mkdir()
            result = subprocess.run(
                [sys.executable, "-m", "concorde.distribution.tester_check"],
                input=json.dumps({"command": shlex.join(argv), "timeout": 330}),
                cwd=governing,
                env=environment,
                capture_output=True,
                text=True,
                timeout=370,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr[-4000:])
            check = json.loads(result.stdout.splitlines()[-1])
            self.assertEqual(check["returncode"], 0, check)
            self.assertFalse(check["timed_out"])
            self.assertLess(len(check["stdout"].encode()), 8000)
            proof = json.loads(check["stdout"])
            self.assertTrue(proof["native"]["accepted"])
            self.assertTrue(proof["inherited_selection_refused"])
            print(json.dumps(proof))
