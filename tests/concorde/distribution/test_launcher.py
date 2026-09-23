"""The launcher: catalog dispatch into Request admission, refusals and the session selection."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.local_installation import LocalInstallationService
from concorde.harness import entry
from concorde.operations.catalog import PUBLIC_OPERATIONS
from concorde.operations.dispatch import declarations, dispatch
from concorde.spec.typed_data import canonical
from concorde.spec.verification import verifies
from tests.concorde.support.pi_session_project import set_up_selected_project

LAUNCHER = REPOSITORY_ROOT / "scripts/run-operation.py"
REQUEST = {
    "type_id": "concorde-operation-invocation",
    "schema_version": 3,
    "operation_id": "concorde-validate",
    "mode": "describe-policy",
    "configuration": None,
    "input": {
        "type_id": "concorde-validate-request",
        "schema_version": 1,
        "data": {"target_id": "module.distribution", "task": "check"},
    },
}


def load_launcher(path: Path):
    """Import one launcher script as a module, without running it."""
    spec = importlib.util.spec_from_file_location(
        f"launcher_{abs(hash(str(path)))}", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Admission:
    """Stands in for Request admission's run: records the handover and returns one envelope."""

    def __init__(self):
        self.calls = []
        self.envelope = {
            "type_id": "concorde-operation-result",
            "schema_version": 3,
            "operation_id": "concorde-validate",
            "invocation_id": "admission-invocation",
            "mode": "describe-policy",
            "status": "described",
            "workspace": None,
            "output": {"admitted": True},
            "errors": [],
        }

    def __call__(self, operation, configuration, runtime_input, *, host_context):
        self.calls.append((operation, configuration, runtime_input, host_context))
        return self.envelope


class InProcessLauncherCase(unittest.TestCase):
    """Runs a launcher's ``main`` in this process, restoring what it changes."""

    def setUp(self):
        handler = signal.getsignal(signal.SIGTERM)
        self.addCleanup(signal.signal, signal.SIGTERM, handler)
        for name in ("argv", "path", "dont_write_bytecode"):
            value = getattr(sys, name)
            self.addCleanup(
                setattr, sys, name, list(value) if isinstance(value, list) else value
            )
        environment = mock.patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("CONCORDE_SESSION_SELECTION", None)
        self.admission = Admission()
        spy = mock.patch.object(entry, "run_operation", side_effect=self.admission)
        spy.start()
        self.addCleanup(spy.stop)

    def launch(self, launcher: Path, arguments: list[str], request: dict | None):
        module = load_launcher(launcher)
        data = json.dumps(request if request is not None else REQUEST).encode()
        with (
            mock.patch.object(sys, "stdin", io.TextIOWrapper(io.BytesIO(data))),
            contextlib.redirect_stdout(io.StringIO()) as printed,
        ):
            code = module.main(arguments)
        return code, printed.getvalue()


class LauncherDispatchTests(InProcessLauncherCase):
    @verifies("scenario.distribution.launcher-dispatch")
    def test_a_catalog_capability_is_handed_to_admission_with_its_services(self):
        code, printed = self.launch(LAUNCHER, ["concorde-validate"], REQUEST)
        self.assertEqual(0, code)
        [(operation, configuration, runtime_input, host)] = self.admission.calls
        self.assertEqual("concorde-validate", operation)
        self.assertIsNone(configuration)
        self.assertEqual(REQUEST["input"], runtime_input)
        self.assertEqual("describe-policy", host.mode)
        self.assertEqual(REPOSITORY_ROOT.resolve(), host.package_root)
        # The catalog's declarations, Operations' dispatcher and the installation service.
        self.assertEqual(declarations(), host.services.catalog)
        self.assertIs(dispatch, host.services.dispatcher)
        self.assertIsInstance(host.services.installation, LocalInstallationService)
        self.assertIsNone(host.session_provenance)
        # Exactly the one envelope admission returned is printed.
        self.assertEqual(canonical(self.admission.envelope) + "\n", printed)


class LauncherRefusalTests(unittest.TestCase):
    def start(self, *arguments: str, python: list[str] | None = None):
        return subprocess.Popen(
            [*(python or [sys.executable]), str(LAUNCHER), *arguments],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=REPOSITORY_ROOT,
            env=child_environment(),
            text=True,
        )

    @verifies("scenario.distribution.launcher-unknown")
    def test_an_unknown_name_or_argument_list_is_refused_without_reading(self):
        self.assertNotIn("concorde-unknown", PUBLIC_OPERATIONS)
        for arguments in (
            ("concorde-unknown",),
            (),
            ("concorde-validate", "extra"),
            ("concorde-validate", "--runtime-check", "extra"),
            ("--runtime-check",),
        ):
            with self.subTest(arguments=arguments):
                process = self.start(*arguments)
                try:
                    # Standard input stays open: a launcher that read it would never exit.
                    code = process.wait(timeout=60)
                    stdout = process.stdout.read()
                finally:
                    process.kill()
                    process.communicate()
                self.assertEqual(3, code)
                result = json.loads(stdout)
                self.assertEqual("concorde-operation-result", result["type_id"])
                self.assertEqual("blocked", result["status"])
                self.assertIsNone(result["output"])
                self.assertEqual("unknown_operation", result["errors"][0]["code"])

    @verifies("scenario.distribution.launcher-missing-runtime")
    def test_a_runtime_check_without_langgraph_fails_with_missing_runtime(self):
        # An interpreter that cannot import LangGraph: its import is blocked before the launcher runs.
        bootstrap = (
            "import runpy,sys;"
            "sys.modules['langgraph']=None;sys.modules['langgraph.graph']=None;"
            "sys.argv=sys.argv[1:];"
            "runpy.run_path(sys.argv[0],run_name='__main__')"
        )
        process = self.start(
            "concorde-validate",
            "--runtime-check",
            python=[sys.executable, "-c", bootstrap],
        )
        stdout, stderr = process.communicate(timeout=60)
        self.assertEqual(3, process.returncode, stderr)
        result = json.loads(stdout)
        self.assertEqual("concorde-validate", result["operation_id"])
        self.assertEqual("missing_runtime", result["errors"][0]["code"])
        self.assertIn(sys.executable, result["errors"][0]["message"])


class LauncherSelectionTests(InProcessLauncherCase):
    """A launcher of a built candidate copy started with that candidate's saved selection."""

    def setUp(self):
        super().setUp()
        set_up_selected_project(self)
        self.launcher = self.project / "scripts/run-operation.py"
        os.environ["CONCORDE_SESSION_SELECTION"] = str(self.selection_path)
        cwd = Path.cwd()
        os.chdir(self.project)
        self.addCleanup(os.chdir, cwd)

    @verifies("scenario.distribution.launcher-selection")
    def test_the_verified_selection_is_the_runs_session_provenance(self):
        code, printed = self.launch(self.launcher, ["concorde-validate"], REQUEST)
        self.assertEqual(0, code, printed)
        [(_, _, _, host)] = self.admission.calls
        self.assertEqual(self.project, host.package_root)
        self.assertEqual(
            json.loads(self.selection_path.read_text()), host.session_provenance
        )
        self.assertEqual(self.selection, host.session_provenance)

    @verifies("scenario.distribution.launcher-selection-refused")
    def test_a_selection_that_no_longer_verifies_stops_before_admission(self):
        entry_file = self.project / "pi/extensions/concorde-session.ts"
        entry_file.write_text(entry_file.read_text() + "\n// changed after selection\n")
        code, printed = self.launch(self.launcher, ["concorde-validate"], REQUEST)
        self.assertEqual(3, code)
        result = json.loads(printed)
        self.assertEqual("concorde-operation-result", result["type_id"])
        self.assertEqual("blocked", result["status"])
        self.assertEqual("concorde-validate", result["operation_id"])
        self.assertTrue(result["errors"])
        self.assertEqual([], self.admission.calls)


if __name__ == "__main__":
    unittest.main()
