"""Real native refusal -> loaded tester tool -> primary evidence after scratch removal."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.harness.native_runtime import admit_native_runtime
from concorde.spec.verification import verifies
from tests.concorde.harness.feedback_export_driver import nodes
from tests.concorde.support.paths import REPOSITORY_ROOT


@unittest.skipUnless(
    os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
    and os.environ.get("CONCORDE_NATIVE_PI"),
    "explicit admitted native and SDK roots required",
)
class FeedbackExportTests(unittest.TestCase):
    @verifies(
        "scenario.harness.execution-feedback",
        "scenario.harness.check-result",
        "scenario.harness.native-context-public",
        "scenario.harness.optional-operation",
    )
    def test_refusals_survive_registered_tester_failure_and_scratch_cleanup(self):
        source = REPOSITORY_ROOT
        native = Path(os.environ["CONCORDE_NATIVE_SUBAGENTS"])
        sdk = Path(os.environ["CONCORDE_NATIVE_PI"])
        binding = admit_native_runtime(native)
        # Optional retention names a new disposable Git primary, never an evidence destination
        # in test_command or a replacement candidate-local status/runs store.
        retained = os.environ.get("CONCORDE_FEEDBACK_FIXTURE_PARENT")
        if retained:
            parent = Path(retained)
            self.assertTrue(parent.is_absolute() and parent.is_dir())
            root = Path(tempfile.mkdtemp(prefix="feedback-primary-", dir=parent))
        else:
            temporary = tempfile.TemporaryDirectory(prefix="concorde-feedback-export-")
            self.addCleanup(temporary.cleanup)
            root = Path(temporary.name)
        primary = root / "primary"
        primary.mkdir()
        (primary / "input.txt").write_text("governing input\n")
        for args in (
            ("init", "-q"),
            ("config", "user.name", "Fixture"),
            ("config", "user.email", "fixture@example.invalid"),
            ("add", "input.txt"),
            ("commit", "-qm", "Fixture primary"),
        ):
            subprocess.run(["git", "-C", str(primary), *args], check=True)
        scratch_parent = root / "scratch"
        scratch_parent.mkdir()
        environment = {
            **os.environ,
            "CONCORDE_SESSION_SELECTION": str(
                source / ".concorde/work/pi-first-context-selection.json"
            ),
            "PYTHONPATH": os.pathsep.join((str(source / "src"), str(source))),
            "TMPDIR": str(scratch_parent),
        }
        for key in (
            "PI_SUBAGENT_EXTENSION_BINDINGS",
            "CONCORDE_NATIVE_PROJECT_ROOT",
            "CONCORDE_STUDIO_URL",
        ):
            environment.pop(key, None)
        receipts = []
        for case in ("direct", "schema", "workflow", "optional", "cancel"):
            with self.subTest(case=case):
                agent = root / ("agent-" + case)
                agent.mkdir()
                command = shlex.join(
                    [
                        "env",
                        "PYTHONPATH=" + environment["PYTHONPATH"],
                        sys.executable,
                        "-m",
                        "tests.concorde.harness.feedback_export_driver",
                        str(source),
                        str(native),
                        str(sdk),
                        case,
                    ]
                )
                result = subprocess.run(
                    [
                        "node",
                        str(
                            source / "tests/concorde/harness/tester_command_driver.mjs"
                        ),
                        str(source),
                        str(sdk),
                        str(primary),
                        str(agent),
                    ],
                    input=json.dumps(
                        {
                            "params": {
                                "command": command,
                                "timeout": 150,
                                "reports": ["causal.json"],
                            }
                        }
                    ),
                    cwd=primary,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                tool = json.loads(result.stdout.splitlines()[-1])
                self.assertTrue(tool["sdkLoaded"])
                self.assertEqual(tool["realModelCalls"], 0)
                self.assertTrue(tool["isError"], tool)
                response = tool["response"]
                self.assertEqual(response["returncode"], 17, response)
                self.assertFalse(response["timed_out"])
                self.assertFalse(response["cancelled"])
                evidence = response["evidence"]
                # A complete capture of a failed command is NOT a successful test.
                self.assertTrue(evidence["complete"], evidence)
                self.assertTrue(evidence["artifacts_complete"])
                self.assertEqual(evidence["errors"], [])
                manifest = json.loads(
                    self.verified_bytes(evidence["manifest"], primary)
                )
                artifacts = {a["name"]: a for a in manifest["artifacts"]}
                for artifact in artifacts.values():
                    self.verified_bytes(artifact["artifact"], primary)
                raw = self.verified_bytes(
                    artifacts["reports/causal.json"]["artifact"], primary
                )
                report = json.loads(raw)
                self.assertFalse(Path(report["scratch"]).exists())
                self.assertEqual(list(scratch_parent.glob("concorde-check-*")), [])
                self.assertFalse(report["accepted"])
                self.assertEqual(report["native_source_digest"], binding.source_digest)
                failures = list(nodes(report["failure"]))
                if case in ("direct", "optional"):
                    causes = [f for f in failures if f["layer"] == "host-submit"]
                    self.assertTrue(causes, failures)
                    cause = causes[0]
                    self.assertEqual(cause["code"], "invalid_completion")
                    self.assertEqual(cause["category"], "host-refusal")
                    self.assertEqual(
                        cause["message"],
                        "stage outcome does not match its task blockers",
                    )
                    self.assertTrue(cause["attempt"])
                    if case == "optional":
                        self.assertEqual(report["failure"]["layer"], "operation")
                elif case == "schema":
                    causes = [
                        f for f in failures if f["category"] == "schema-rejection"
                    ]
                    self.assertTrue(causes)
                    self.assertEqual(causes[0]["attempt"], "structured-1")
                    self.assertIn(
                        'Validation failed for tool "structured_output"',
                        causes[0]["diagnostics"]["text"],
                    )
                    self.assertIn("answer", causes[0]["diagnostics"]["text"])
                    self.assertNotIn("Received arguments:", raw.decode())
                elif case == "workflow":
                    self.assertEqual(report["scripted_calls"], 2)
                    self.assertIn("native-workflow", [f["layer"] for f in failures])
                    causes = [f for f in failures if f["layer"] == "host-submit"]
                    self.assertEqual(
                        causes[0]["message"], "planning produced no usable plan"
                    )
                    self.assertEqual(causes[0]["code"], "invalid_completion")
                    self.assertTrue(causes[0]["attempt"])
                    # Captured-byte completeness cannot cure native semantic incompleteness.
                    self.assertFalse(report["semantic_complete"])
                else:
                    self.assertIn("cancelled", [f["category"] for f in failures])
                if case in ("direct", "workflow", "optional"):
                    self.assertTrue(report["selected_diagnostics"], report)
                for selected in report["selected_diagnostics"]:
                    self.assertFalse(Path(selected["source"]).exists())
                    self.assertIn(selected["feedback"], failures)
                receipts.append(
                    {
                        "case": case,
                        "manifest": evidence["manifest"],
                        "report": artifacts["reports/causal.json"]["artifact"],
                        "semantic_complete": report["semantic_complete"],
                    }
                )
                print(json.dumps(receipts[-1]))
        if retained:
            (root / "receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")

    def verified_bytes(self, reference, primary):
        path = Path(reference["path"])
        self.assertTrue(path.is_relative_to(primary / ".concorde/runs"))
        raw = path.read_bytes()
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(
            reference["digest"], "sha256:" + hashlib.sha256(raw).hexdigest()
        )
        self.assertEqual(reference["bytes"], len(raw))
        return raw
