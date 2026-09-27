"""Read-only inspection, shared validation, draft isolation and real terminal Save/Cancel."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import signal
import subprocess
import sys
import unittest
from unittest.mock import patch

from concorde.harness import models
from concorde.harness.configure import CONFIGURATION_SCHEMA, RESULT_SCHEMA, main
from concorde.harness.configure_tui import Draft
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from concorde.tasks import store
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT


def spec_contract(identity):
    path = REPOSITORY_ROOT / "specs/concorde/execution/workers/contracts.md"
    for block in re.findall(
        r"```concorde-contract\n(.*?)\n```", path.read_text(), re.DOTALL
    ):
        value = json.loads(block)
        if value["id"] == identity:
            return value
    raise AssertionError(identity)


class ConfigureWorkersTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.path = models.config_path(self.root)
        self.path.unlink()

    def configure(self, *args, cwd=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(args, cwd=cwd or self.root)
        return code, json.loads(out.getvalue())

    @verifies("scenario.workers.configure-list")
    def test_inspection_is_read_only_and_does_not_discover(self):
        with patch(
            "concorde.harness.available_models.candidates",
            side_effect=AssertionError("discovery called"),
        ):
            status, value = self.configure("--show", "--json", cwd=self.root / "src")
            self.assertEqual(0, status, value)
            validate(value, RESULT_SCHEMA)
            output = value["output"]
            validate(output, CONFIGURATION_SCHEMA)
            self.assertEqual("show", output["action"])
            self.assertEqual(str(self.root), output["worktree"])
            self.assertEqual(
                ["reviewer", "checker"], list(output["effective"]["spec_review"])
            )
            self.assertEqual(6, len(output["effective"]["spec_panel"]))
            self.assertNotIn("delivery", output["effective"])
            self.assertNotIn("candidates", output)
            self.assertFalse(self.path.exists())
            status, value = self.configure("--check", "--json")
            self.assertEqual((0, "check"), (status, value["output"]["action"]))

    @verifies("scenario.workers.configure-change")
    def test_draft_save_cancel_and_task_inheritance(self):
        draft = Draft(self.root)
        draft.set_field(None, None, "model", "offline/custom")
        draft.set_field(None, None, "reasoning", "medium")
        self.assertFalse(self.path.exists())
        self.assertTrue(draft.commit())
        self.project.open_task("t1")
        task = self.project.worktree("t1")
        self.assertEqual(models.load(self.root), models.load(task))
        before = store.load_task(self.root, "t1")
        task_draft = Draft(task)
        task_draft.set_field("spec_review", "checker", "model", "other/model")
        self.assertEqual("offline/custom", models.load(task)["default"]["model"])
        task_draft.commit()
        self.assertNotIn("operations", models.load(self.root))
        self.assertEqual(before, store.load_task(self.root, "t1"))
        self.assertFalse((self.root / ".concorde/runs").exists())
        abandoned = Draft(task)
        abandoned.reset(None, None)
        self.assertIn("default", models.load(task))
        self.assertFalse(Draft(task).commit())

    @verifies("scenario.workers.configure-backend", "scenario.workers.configure-worker")
    def test_backend_reset_and_sparse_field_inheritance(self):
        draft = Draft(self.root)
        draft.set_field(None, None, "model", "pi/default")
        draft.set_field(None, None, "reasoning", "medium")
        draft.set_field("spec_panel", None, "model", "pi/panel")
        draft.set_field("spec_panel", "reviewer2", "reasoning", "high")
        draft.set_field("spec_panel", "chair", "backend", "claude")
        draft.set_field("spec_panel", "chair", "model", "opus")
        draft.commit()
        chair = models.choice(models.load(self.root), "spec_panel", "chair")
        self.assertEqual(
            ("claude", "opus", None),
            (chair["backend"], chair["model"], chair["reasoning"]),
        )
        self.assertEqual("operations.spec_panel.workers.chair", chair["backend_source"])
        draft = Draft(self.root)
        draft.set_field("spec_panel", "reviewer2", "reasoning", None)
        self.assertNotIn(
            "reviewer2", draft.config["operations"]["spec_panel"]["workers"]
        )
        self.assertEqual(
            "medium",
            models.choice(draft.config, "spec_panel", "reviewer2")["reasoning"],
        )
        draft.set_field("spec_panel", "chair", "backend", "pi")
        self.assertEqual({"backend": "pi"}, draft.own("spec_panel", "chair"))
        draft.reset("spec_panel", "chair")
        self.assertNotIn("workers", draft.config["operations"]["spec_panel"])
        self.assertIn(("spec_panel", None), draft.scopes())

    @verifies("scenario.workers.configure-refused")
    def test_invalid_and_concurrent_edits_do_not_overwrite(self):
        draft = Draft(self.root)
        draft.set_field(None, None, "reasoning", "invalid")
        with self.assertRaises(models.ModelConfigError):
            draft.commit()
        self.assertFalse(self.path.exists())
        draft.set_field(None, None, "reasoning", "high")
        self.path.write_text('{"schema_version":3,"default":{"model":"concurrent"}}')
        before = self.path.read_bytes()
        with self.assertRaisesRegex(models.ModelConfigError, "file changed"):
            draft.commit()
        self.assertEqual(before, self.path.read_bytes())

    @verifies("scenario.workers.configure-refused")
    def test_removed_flags_and_nonterminal_require_explicit_inspection(self):
        for args in (
            ("--model", "x"),
            ("--candidates", "pi"),
            ("--backend", "pi"),
            ("--unset",),
            ("--allow-unlisted",),
            ("--operation", "implement"),
            ("--worker", "worker"),
            ("--reasoning", "high"),
            ("--json",),
            ("--show", "--check"),
        ):
            status, value = self.configure(*args)
            self.assertEqual(2, status, args)
            self.assertEqual("invalid_request", value["error"]["code"])
        status, value = self.configure()
        self.assertEqual(2, status)
        self.assertIn("interactive terminal", value["error"]["detail"])
        status, value = self.configure("--check", "--json", cwd=self.project.base)
        self.assertEqual(2, status)
        self.assertIn("not inside a Git worktree", value["error"]["detail"])
        self.assertFalse(self.path.exists())

    def test_check_reports_same_invalid_catalog_as_runtime(self):
        value = {
            "schema_version": 3,
            "operations": {"implement": {"workers": {"typo": {"model": "custom"}}}},
        }
        self.path.write_text(json.dumps(value))
        before = self.path.read_bytes()
        status, result = self.configure("--check", "--json")
        self.assertEqual(1, status)
        self.assertEqual("config_invalid", result["error"]["causes"][0]["code"])
        with self.assertRaisesRegex(models.ModelConfigError, "unknown worker 'typo'"):
            models.worker_choice(value, "implement", "worker", {})
        self.assertEqual(before, self.path.read_bytes())

    def test_contracts_match(self):
        for identity, schema in (
            ("contract.workers.worker-configuration", CONFIGURATION_SCHEMA),
            ("contract.workers.configure-workers-result", RESULT_SCHEMA),
        ):
            contract = spec_contract(identity)
            self.assertEqual(schema, contract["schema"])
            validate(contract["example"], schema)

    @contextlib.contextmanager
    def terminal(self, argv=None, environ=None):
        import fcntl
        import pty
        import select
        import struct
        import termios
        import time

        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
        process = subprocess.Popen(
            argv
            or [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/concorde.py"),
                "configure-workers",
            ],
            cwd=self.root,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=dict(os.environ, TERM="xterm", **(environ or {})),
        )
        os.close(slave)
        transcript = bytearray()

        def wait_for(text):
            deadline = time.monotonic() + 10
            start = len(transcript)
            while text not in transcript[start:]:
                if time.monotonic() > deadline:
                    self.fail(f"terminal did not show {text!r}: {transcript!r}")
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        transcript.extend(os.read(master, 65536))
                    except OSError:
                        self.fail(
                            f"terminal exited waiting for {text!r}: {transcript!r}"
                        )

        def send(keys):
            os.write(master, keys)

        try:
            yield process, send, wait_for
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)

    def enter_custom_model(self, send, wait):
        send(b"\n")
        wait(b"backend:")
        send(b"\x1bOB\n")
        wait(b"Custom model name")
        send(b"\x1bOB\n")
        wait(b"Custom model (")
        send(b"offline/custom\n")
        wait(b"offline/custom")
        self.assertFalse(self.path.exists())
        send(b"q")
        wait(b"unsaved")

    @unittest.skipIf(sys.platform == "win32", "requires a pseudo-terminal")
    @verifies("scenario.workers.configure-terminal")
    def test_terminal_dirty_exit_defaults_to_keep_then_explicit_discard(self):
        for ending in (b"q", b"\x1b", b"\x1bOA\n", b"\x03"):
            with self.subTest(ending=ending), self.terminal() as (process, send, wait):
                wait(b"Every worker")
                self.enter_custom_model(send, wait)

                def request_exit(ending=ending, process=process, send=send):
                    if ending == b"\x03":
                        process.send_signal(signal.SIGINT)
                    else:
                        send(ending)

                request_exit()
                wait(b"Discard changes")
                self.assertIsNone(process.poll())
                self.assertFalse(self.path.exists())
                # Enter chooses the safe default. A second Ctrl-C is safe too.
                if ending == b"\x03":
                    process.send_signal(signal.SIGINT)
                elif ending == b"\x1b":
                    send(b"\x1b")
                else:
                    send(b"\n")
                wait(b"unsaved")
                # Use q here because the explicit Cancel row remains selected.
                send(b"q")
                wait(b"Discard changes")
                send(b"\x1bOB\n")
                process.wait(timeout=10)
                self.assertEqual(0, process.returncode)
                self.assertFalse(self.path.exists())

    @unittest.skipIf(sys.platform == "win32", "requires a pseudo-terminal")
    def test_terminal_save_and_clean_cancel(self):
        with self.terminal() as (process, send, wait):
            wait(b"Every worker")
            send(b"q")
            process.wait(timeout=10)
            self.assertEqual(0, process.returncode)
            self.assertFalse(self.path.exists())
        with self.terminal() as (process, send, wait):
            wait(b"Every worker")
            self.enter_custom_model(send, wait)
            send(b"s")
            process.wait(timeout=10)
            self.assertEqual(0, process.returncode)
        self.assertEqual("offline/custom", models.load(self.root)["default"]["model"])

    @unittest.skipIf(sys.platform == "win32", "requires a pseudo-terminal")
    @verifies("scenario.workers.configure-search")
    def test_terminal_scope_and_model_search_retains_scope_after_edit(self):
        agent = self.project.base / "listing.py"
        agent.write_text(
            "#!/usr/bin/env python3\nimport sys\n"
            "if '--list-models' in sys.argv:\n"
            " for i in range(80): print(f'local model-{i:02} 32K 4K yes no')\n"
            "else: print('test agent')\n"
        )
        agent.chmod(0o755)
        with self.terminal(environ={"CONCORDE_PI": str(agent)}) as (
            process,
            send,
            wait,
        ):
            wait(b"Every worker")
            send(b"/")
            wait(b"Search (")
            send(b"spec_panel / reviewer5\n")
            wait(b"Selected: spec_panel / reviewer5")
            send(b"\n")
            wait(b"backend:")
            send(b"\x1bOB\n")
            wait(b"Discover candidates")
            send(b"\x1bOB\x1bOB\n")
            wait(b"local/model-00")
            send(b"/")
            wait(b"Search (")
            send(b"model-79\n")
            wait(b"local/model-79")
            send(b"\n")
            wait(b"Draft updated")
            send(b"q")
            wait(b"Selected: spec_panel / reviewer5")
            # Enter immediately reopens the same filtered scope, not the global default.
            send(b"\n")
            wait(b"model: local/model-79")
            # Ctrl-C inside a nested edit must offer the same dirty-exit confirmation.
            process.send_signal(signal.SIGINT)
            wait(b"Discard changes")
            send(b"\n")
            wait(b"Selected: spec_panel / reviewer5")
            # Clearing the filter keeps the selection while exposing all scopes again.
            send(b"/")
            wait(b"Search (")
            send(b"\n")
            wait(b"(all)")
            send(b"s")
            process.wait(timeout=10)
            self.assertEqual(0, process.returncode)
        config = models.load(self.root)
        self.assertEqual(
            {
                "schema_version": 3,
                "operations": {
                    "spec_panel": {
                        "workers": {"reviewer5": {"model": "local/model-79"}}
                    }
                },
            },
            config,
        )

    @unittest.skipIf(sys.platform == "win32", "requires a pseudo-terminal")
    def test_pi_adapter_runs_real_terminal_editor_and_restores_terminal(self):
        import shutil

        if not shutil.which("node"):
            self.skipTest("Node required for pi adapter")
        probe = self.project.base / "adapter.mts"
        source = REPOSITORY_ROOT / "src/concorde/main_session/pi_models.ts"
        command = [
            sys.executable,
            str(REPOSITORY_ROOT / "scripts/concorde.py"),
            "configure-workers",
        ]
        probe.write_text(
            f"import {{runEditor}} from {json.dumps(source.as_uri())};\n"
            "const tui = {stop() {console.log('PI STOP');}, start() {console.log('PI RESTORED');}, requestRender(force) {console.log('PI RENDER', force);}};\n"
            f"process.exitCode = runEditor(tui, {json.dumps(command)}, {json.dumps(str(self.root))});\n"
        )
        with self.terminal(
            argv=["node", "--experimental-strip-types", "--no-warnings", str(probe)]
        ) as (process, send, wait):
            wait(b"Every worker")
            send(b"q")
            wait(b"PI RESTORED")
            process.wait(timeout=10)
            self.assertEqual(0, process.returncode)
            self.assertFalse(self.path.exists())
