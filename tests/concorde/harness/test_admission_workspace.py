"""Where an admitted request runs: the entry directory, relays, delivery and configuration checks."""

import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import textwrap
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from concorde.harness import relay as relay_module
from concorde.harness.change_worktree import (
    create_worktree,
    ensure_change,
    git,
    git_value,
    progress,
    read_change,
    workspace_context,
)
from concorde.harness.entry import json_main
from concorde.harness.host import AdmissionServices, OperationHost
from concorde.harness.relay import relay_operation
from concorde.operations.catalog import declarations
from concorde.operations.dispatch import dispatch, run_operation
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.support.environment import (
    child_environment,
    scrubbed_process_environment,
)
from tests.concorde.support.spec_project import CONFIGURATION, PACKAGE, project
from tests.concorde.support.worktree_project import WorktreeProject

LAUNCHER = PACKAGE / "scripts/run-operation.py"


def invocation(operation, data, *, configuration=CONFIGURATION, mode="execute"):
    return {
        "type_id": "concorde-operation-invocation",
        "schema_version": 3,
        "operation_id": operation,
        "mode": mode,
        "configuration": configuration,
        "input": typed(operation + "-request", data),
    }


def launch(root: Path, operation: str, value: dict) -> dict:
    """The launcher's entry process run in ``root``, as the Pi tool starts it."""
    process = subprocess.run(
        [sys.executable, str(LAUNCHER), operation],
        cwd=root,
        input=json.dumps(value),
        text=True,
        capture_output=True,
        env=child_environment(),
    )
    result = json.loads(process.stdout)
    assert process.returncode == (0 if result["status"] == "succeeded" else 3)
    return result


class SpyServices:
    """The catalog and the real dispatcher, recording each admitted request it dispatches."""

    def __init__(self, installation=None):
        self.dispatched = []
        self.services = AdmissionServices(
            catalog=declarations(),
            dispatcher=self.dispatch,
            installation=installation,
        )

    def dispatch(self, request):
        self.dispatched.append(request)
        return dispatch(request)


def files(root: Path) -> dict:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }


def run_in_process(root: Path, operation: str, value: dict, services) -> dict:
    """``json_main`` with ``root`` as the entry process's working directory."""
    output = io.StringIO()
    with (
        contextlib.chdir(root),
        patch("sys.stdin", io.StringIO(json.dumps(value))),
        patch("sys.argv", ["run-operation.py"]),
        contextlib.redirect_stdout(output),
    ):
        json_main(PACKAGE, operation, services=services)
    return json.loads(output.getvalue())


class EntryDirectoryTests(WorktreeProject, unittest.TestCase):
    """The project root is the directory the launcher was started in, nothing else."""

    def setUp(self):
        super().setUp()
        self.unversioned = self.directory / "unversioned"
        self.unversioned.mkdir()
        project(self.unversioned)

    @verifies("scenario.admission.worktree-binding")
    def test_a_request_binds_to_the_worktree_it_was_started_in(self):
        propose = invocation(
            "concorde-configure",
            {
                "action": "propose",
                "configuration": typed(
                    "concorde-operation-configuration",
                    {"model": "openai-codex/gpt-6-astra", "thinking": "high"},
                ),
            },
        )
        # The candidate's Specs differ from the primary's without a commit.
        (self.change / "specs/transfer/module.md").write_text(
            (self.change / "specs/transfer/module.md").read_text() + "\nCandidate.\n"
        )
        for root, kind, archive in (
            (self.primary, "primary", self.primary),
            (self.change, "change", self.primary),
            (self.unversioned, "unversioned", self.unversioned),
        ):
            with self.subTest(kind=kind):
                spy = SpyServices()
                result = run_in_process(
                    root, "concorde-configure", propose, spy.services
                )
                self.assertEqual("succeeded", result["status"], result)
                [request] = spy.dispatched
                self.assertEqual(root.resolve(), request.host.project_root.resolve())
                self.assertEqual(archive.resolve(), request.host.archive_root.resolve())
                self.assertEqual(
                    kind, workspace_context(request.host.project_root)["kind"]
                )
                self.assertEqual(
                    root / "specs/transfer/module.md",
                    request.host.project_root / "specs/transfer/module.md",
                )
                record = json.loads(
                    (
                        archive
                        / ".concorde/runs"
                        / result["invocation_id"]
                        / "run.json"
                    ).read_text()
                )
                self.assertEqual(str(root.resolve()), record["source_worktree"])
                self.assertEqual(result, record["result"])
        # Change status and run records stay in the primary, never in the candidate.
        self.assertFalse((self.change / ".concorde/runs").exists())
        self.assertFalse((self.change / ".concorde/status").exists())

    @verifies("scenario.admission.worktree-binding")
    def test_parent_directories_are_never_searched_for_a_project(self):
        nested = self.unversioned / "nested"
        nested.mkdir()
        spy = SpyServices()
        result = run_in_process(
            nested,
            "concorde-configure",
            invocation(
                "concorde-configure",
                {"action": "propose", "configuration": CONFIGURATION},
            ),
            spy.services,
        )
        # The nested directory is the project; it has no configuration of its own.
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("configuration_mismatch", result["errors"][0]["code"])
        self.assertEqual([], spy.dispatched)

    @verifies("scenario.admission.subdirectory-refused")
    def test_a_directory_inside_a_worktree_is_refused(self):
        for root in (self.primary, self.change):
            with self.subTest(worktree=root.name):
                before = files(self.primary), files(self.change)
                inside = root / "specs"
                result = launch(
                    inside,
                    "concorde-configure",
                    invocation(
                        "concorde-configure",
                        {"action": "propose", "configuration": CONFIGURATION},
                    ),
                )
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual("workspace_mismatch", result["errors"][0]["code"])
                self.assertEqual("execute", result["mode"], result)
                self.assertIsNone(result["output"])
                self.assertEqual(before, (files(self.primary), files(self.change)))
        # In process: no Spec is read and no provider runs.
        spy = SpyServices()
        with patch("concorde.harness.admission.SpecRepository") as repository:
            result = run_operation(
                "concorde-validate",
                CONFIGURATION,
                typed("concorde-validate-request", self.task),
                host_context=OperationHost(
                    self.change / "specs", PACKAGE, services=spy.services
                ),
            )
        self.assertEqual("workspace_mismatch", result["errors"][0]["code"], result)
        repository.assert_not_called()
        self.assertEqual([], spy.dispatched)

    @verifies("scenario.admission.unversioned-mutation-refused")
    def test_a_mutation_outside_git_is_refused_through_the_launcher(self):
        _, request = self.configure_request()
        before = files(self.unversioned)
        result = launch(
            self.unversioned,
            "concorde-configure",
            invocation("concorde-configure", request),
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("workspace_mismatch", result["errors"][0]["code"], result)
        self.assertIsNone(result["output"])
        self.assertEqual(before, files(self.unversioned))
        self.assertFalse((self.unversioned / ".concorde/status").exists())
        self.assertFalse((self.unversioned / ".concorde/runs").exists())


class FixtureInstallation:
    """An installation service whose candidate launcher is the fixture ``script``."""

    def __init__(self, script: Path | None = None):
        self.script = script
        self.installs = []

    def verify(self, project_root, package_root):
        return None

    def install(self, candidate, package_root, bootstrap):
        self.installs.append((Path(candidate), bootstrap))
        return Path(sys.executable), self.script or LAUNCHER


class RelayTests(WorktreeProject, unittest.TestCase):
    """Relays from the primary into an existing candidate."""

    def setUp(self):
        super().setUp()
        with scrubbed_process_environment():
            self.candidate = create_worktree(
                self.primary, self.task, package_root=PACKAGE
            )
        self.path = Path(self.candidate["path"])
        self.addCleanup(self.remove_candidate, self.path)

    def status_bytes(self):
        return {
            path.name: path.read_bytes()
            for path in (self.primary / ".concorde/status").glob("*.json")
        }

    def worktrees(self):
        return git_value(self.primary, "worktree", "list", "--porcelain")

    def relay_request(self, installation, relay=None):
        spy = SpyServices(installation)
        return spy, run_operation(
            "concorde-validate",
            CONFIGURATION,
            typed(
                "concorde-validate-request",
                {
                    **self.task,
                    "change_id": self.candidate["change_id"],
                    "run_checks": False,
                },
            ),
            host_context=OperationHost(
                self.primary, PACKAGE, services=spy.services, relay=relay
            ),
        )

    @verifies("scenario.admission.relay-resume")
    def test_a_change_identity_continues_in_its_candidate(self):
        recorded = read_change(self.path, required=True)
        worktrees = self.worktrees()
        installation = FixtureInstallation()
        targets = []

        def relay(host, operation, value, candidate):
            targets.append(dict(host.relay_target))
            with scrubbed_process_environment():
                return relay_operation(host, operation, value, candidate)

        spy, result = self.relay_request(installation, relay)
        [target] = targets
        self.assertEqual(str(self.path), target["path"])
        self.assertFalse(target.get("bootstrap_installation"))
        # The candidate's launcher was selected without installing anything new.
        self.assertEqual([(self.path, False)], installation.installs)
        self.assertEqual([], spy.dispatched)
        self.assertEqual(
            self.candidate["change_id"],
            target["invocation"]["input"]["data"]["change_id"],
        )
        self.assertEqual(str(self.path), result["workspace"]["path"], result)
        self.assertEqual(self.candidate["change_id"], result["workspace"]["change_id"])
        self.assertEqual(worktrees, self.worktrees())
        self.assertEqual(1, len(self.status_bytes()))
        after = read_change(self.path, required=True)
        for field in ("change_id", "task", "target_hint", "constraints", "focus_id"):
            self.assertEqual(recorded[field], after[field], field)
        # The change's recorded target is the one the relayed request is bound to.
        self.assertEqual(recorded["target_hint"], after["target_id"])

    @verifies("scenario.admission.relay-failed")
    def test_a_launcher_without_an_envelope_fails_the_relay(self):
        script = self.directory / "silent-launcher.py"
        script.write_text(
            "import sys\n"
            "sys.stdin.read()\n"
            "print('not an envelope')\n"
            "print('launcher broke: password=hunter2', file=sys.stderr)\n"
            "sys.exit(7)\n"
        )
        (self.path / "work.txt").write_text("candidate edit\n")
        recorded = read_change(self.path, required=True)
        with scrubbed_process_environment():
            _, result = self.relay_request(FixtureInstallation(script))
        # A transport failure is an execution failure, never a refusal.
        self.assertEqual("failed", result["status"], result)
        [error] = result["errors"]
        self.assertEqual("relay_failed", error["code"], result)
        feedback = error["feedback"]
        self.assertEqual(
            ("relay", "transport"), (feedback["layer"], feedback["category"])
        )
        self.assertEqual(result["invocation_id"], feedback["attempt"])
        diagnostics = json.loads(feedback["diagnostics"]["text"])
        self.assertEqual(7, diagnostics["exit_code"])
        self.assertIn("not an envelope", diagnostics["stdout"])
        self.assertIn("launcher broke", diagnostics["stderr"])
        self.assertNotIn("hunter2", json.dumps(result))
        # The candidate, its edits and its change status are kept.
        self.assertEqual("candidate edit\n", (self.path / "work.txt").read_text())
        kept = read_change(self.path, required=True)
        for field in (
            "change_id",
            "path",
            "branch",
            "status",
            "phase",
            "task",
            "target_hint",
        ):
            self.assertEqual(recorded[field], kept[field], field)

    @verifies("scenario.admission.cancelled")
    def test_an_interrupted_relay_terminates_then_kills_its_launcher(self):
        self.assertEqual(30, relay_module.RELAY_GRACE_SECONDS)
        ready = self.directory / "ready"
        terminated = self.directory / "terminated"
        cooperative = self.directory / "cooperative.py"
        cooperative.write_text(
            textwrap.dedent(
                f"""
                import json, pathlib, signal, sys, time
                def stop(signum, frame):
                    pathlib.Path({str(terminated)!r}).write_text("SIGTERM")
                    print(json.dumps({{"type_id": "concorde-operation-result",
                                       "status": "failed"}}))
                    sys.exit(3)
                signal.signal(signal.SIGTERM, stop)
                pathlib.Path({str(ready)!r}).write_text("ready")
                time.sleep(60)
                """
            )
        )
        stubborn = self.directory / "stubborn.py"
        stubborn.write_text(
            textwrap.dedent(
                f"""
                import pathlib, signal, time
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
                pathlib.Path({str(ready)!r}).write_text("ready")
                time.sleep(60)
                """
            )
        )
        host = OperationHost(
            self.primary,
            PACKAGE,
            relay_target={
                "path": str(self.path),
                "change_id": self.candidate["change_id"],
                "mutates": False,
            },
        )

        def interrupted(script):
            ready.unlink(missing_ok=True)
            relayed = replace(
                host,
                services=AdmissionServices(
                    catalog={},
                    dispatcher=dispatch,
                    installation=FixtureInstallation(script),
                ),
            )

            def interrupt():
                deadline = time.monotonic() + 20
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                os.kill(os.getpid(), signal.SIGINT)

            previous = signal.signal(signal.SIGINT, signal.default_int_handler)
            self.addCleanup(signal.signal, signal.SIGINT, previous)
            thread = threading.Thread(target=interrupt)
            thread.start()
            started = time.monotonic()
            try:
                with scrubbed_process_environment():
                    return relay_operation(relayed, "concorde-validate", {}, self.path)
            finally:
                thread.join()
                self.elapsed = time.monotonic() - started

        with patch.object(relay_module, "RELAY_GRACE_SECONDS", 1.5):
            envelope, _ = interrupted(cooperative)
            self.assertEqual("SIGTERM", terminated.read_text())
            self.assertEqual("failed", envelope["status"])
            self.assertLess(self.elapsed, 1.5)
            with self.assertRaises(Exception) as raised:
                interrupted(stubborn)
        # The launcher ignoring SIGTERM is killed only after the grace period.
        self.assertGreaterEqual(self.elapsed, 1.5)
        self.assertEqual("relay_failed", raised.exception.code)
        diagnostics = json.loads(raised.exception.feedback["diagnostics"]["text"])
        self.assertEqual(-signal.SIGKILL, diagnostics["exit_code"])
        self.assertTrue(self.path.is_dir())
        self.assertIsNotNone(read_change(self.path))


class DeliverySessionTests(WorktreeProject, unittest.TestCase):
    """Delivery binds no candidate; the provider decides whether this worktree takes part."""

    def setUp(self):
        super().setUp()
        self.state = ensure_change(self.change, task=self.task)

    def status_bytes(self):
        return {
            path.name: path.read_bytes()
            for path in (self.primary / ".concorde/status").glob("*.json")
        }

    @verifies("scenario.admission.delivery-session")
    def test_delivery_runs_where_it_was_started(self):
        third = self.directory / "third"
        git(self.primary, "worktree", "add", "-q", "-b", "third", str(third))
        worktrees = git_value(self.primary, "worktree", "list", "--porcelain")
        registered = set(self.status_bytes())
        outcomes = {}
        for root in (self.change, self.primary, third):
            with self.subTest(worktree=root.name):
                spy = SpyServices()
                result = run_operation(
                    "concorde-deliver",
                    CONFIGURATION,
                    typed(
                        "concorde-deliver-request",
                        {"change_id": self.state["change_id"]},
                    ),
                    host_context=OperationHost(
                        root, PACKAGE, services=spy.services, relay=self.fail
                    ),
                )
                [request] = spy.dispatched
                self.assertEqual(root, request.host.project_root)
                self.assertIsNone(request.host.relay_target)
                self.assertEqual(str(root.resolve()), result["workspace"]["path"])
                outcomes[root.name] = (
                    result["errors"][0]["code"] if result["errors"] else None
                )
                self.assertEqual(
                    worktrees,
                    git_value(self.primary, "worktree", "list", "--porcelain"),
                )
                # No change is registered; the provider may record its own delivery attempt.
                self.assertEqual(registered, set(self.status_bytes()))
                self.assertIsNone(read_change(third))
                self.assertIsNone(read_change(self.primary))
        # A worktree that does not take part in the change is the provider's refusal.
        self.assertEqual("delivery_session_required", outcomes["third"])
        for participant in ("change", "primary"):
            self.assertNotEqual("delivery_session_required", outcomes[participant])

    @verifies("scenario.admission.delivery-in-progress")
    def test_a_change_being_delivered_accepts_no_other_mutation(self):
        _, request = self.configure_request()
        for status in ("delivering", "cleanup_pending"):
            with self.subTest(status=status):
                progress(self.change, status=status)
                before = self.status_bytes()
                spy = SpyServices()
                result = run_operation(
                    "concorde-configure",
                    CONFIGURATION,
                    typed("concorde-configure-request", request),
                    host_context=OperationHost(
                        self.change, PACKAGE, services=spy.services
                    ),
                )
                self.assertEqual("blocked", result["status"], result)
                self.assertEqual(
                    "delivery_in_progress", result["errors"][0]["code"], result
                )
                self.assertEqual([], spy.dispatched)
                self.assertEqual(before, self.status_bytes())
                self.assertEqual(CONFIGURATION, self.stored_configuration(self.change))


class ConfigurationMatchTests(WorktreeProject, unittest.TestCase):
    """Stored configuration must equal the request's."""

    @verifies("scenario.admission.configuration-mismatch")
    def test_a_request_with_another_configuration_is_refused(self):
        other = typed(
            "concorde-operation-configuration",
            {"model": "openai-codex/gpt-6-astra", "thinking": "low"},
        )
        request = {"action": "propose", "configuration": other}
        spy = SpyServices()

        def call(configuration):
            return run_operation(
                "concorde-configure",
                configuration,
                typed("concorde-configure-request", request),
                host_context=OperationHost(self.change, PACKAGE, services=spy.services),
            )

        mismatched = call(other)
        self.assertEqual("blocked", mismatched["status"], mismatched)
        self.assertEqual("configuration_mismatch", mismatched["errors"][0]["code"])
        self.assertIsNone(mismatched["output"])
        # A project with no stored configuration refuses the same way.
        path = self.change / ".concorde/config.json"
        document = json.loads(path.read_text())
        del document["operation_configuration"]
        path.write_text(json.dumps(document, indent=2) + "\n")
        missing = call(CONFIGURATION)
        self.assertEqual("blocked", missing["status"], missing)
        self.assertEqual("configuration_mismatch", missing["errors"][0]["code"])
        self.assertEqual([], spy.dispatched)
        # The stored configuration itself is admitted and dispatched.
        path.write_text(
            json.dumps({**document, "operation_configuration": CONFIGURATION}, indent=2)
        )
        self.assertEqual("succeeded", call(CONFIGURATION)["status"])
        self.assertEqual(1, len(spy.dispatched))


if __name__ == "__main__":
    unittest.main()
