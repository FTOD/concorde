"""The check service: selecting Modules, running their checks read-only, logs and staleness."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from concorde.kernel.errors import ERROR_SCHEMA
from concorde.execution.checks.check_executor import execute_check
from concorde.execution.checks.checks import (
    CheckError,
    _timeout,
    check_revision,
    configured_checks,
    environment,
    measured_digest,
    project_python,
    run_checks,
    service_error,
    validate_checks,
)
from concorde.method.checks import (
    affected_modules,
    checked_modules,
    measured_files,
    run_module_checks,
    verified_tests,
)
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from tests.concorde.harness.workers.test_workers import WorkerProject
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT
from tests.concorde.support.spec_project import read_checks, write_checks


class CheckServiceTests(unittest.TestCase):
    def setUp(self):
        self.project = WorkerProject(self)
        self.root = self.project.root
        # The folder of the trace node the check nodes are written below.
        self.logs = self.project.base / "checks"

    def repository(self):
        return SpecRepository(self.root, REPOSITORY_ROOT)

    def run_checks(self, modules, **options):
        """Run the checks of ``modules`` as Method's steps call the service: with each Module's
        implementation files, the tests verifying its scenarios and the project's interpreter."""
        return run_module_checks(
            self.root,
            modules,
            trace_directory=self.logs,
            repository=self.repository(),
            **options,
        )

    def revision(self, module: str) -> str:
        """The check revision of ``module`` over its implementation files."""
        return check_revision(
            self.root,
            configured_checks(self.root),
            module,
            self.repository().bound_files(module),
        )

    def digest(self, check: dict, modules) -> str:
        """The measured digest of ``check`` for ``modules``, as Method selects its input."""
        repository = self.repository()
        return measured_digest(
            self.root,
            check,
            modules,
            measured=measured_files(repository, modules),
            tests=verified_tests(repository, modules),
        )

    @verifies("scenario.checks.service-run", "scenario.checks.service-no-checks")
    def test_the_checks_of_changed_modules_run_and_log(self):
        self.assertEqual(
            ["module.a"],
            affected_modules(self.repository(), ["src/a/calc.py"]),
        )
        self.assertEqual(
            ["module.a"],
            affected_modules(self.repository(), ["specs/a/module.md"]),
        )
        [result] = self.run_checks(
            affected_modules(self.repository(), ["src/a/calc.py"])
        )
        self.assertEqual(
            ("check.a", "module.a", "passed", 0),
            (
                result["check_id"],
                result["module"],
                result["status"],
                result["exit_code"],
            ),
        )
        self.assertEqual(self.logs / "check.a/output.log", Path(result["log"]))
        # Each check run is a check node: its trace and its output.
        node = json.loads((self.logs / "check.a/trace.json").read_text())
        self.assertEqual(
            ("check", "check.a", "ok", "passed"),
            (node["kind"], node["id"], node["status"], node["outcome"]),
        )
        self.assertEqual(
            ("passed", 0, result["source_digest"]),
            tuple(
                node["content"]["data"][k]
                for k in ("status", "exit_code", "source_digest")
            ),
        )
        self.assertEqual(self.revision("module.a"), result["source_digest"])
        (self.root / "src/a/flag").write_text("broken")
        [failed] = self.run_checks(["module.a"])
        self.assertEqual(("failed", 1), (failed["status"], failed["exit_code"]))
        self.assertEqual([], self.run_checks(["module.b"]))

    def configure(self, **changes) -> None:
        path = self.root / ".concorde/config.json"
        config = json.loads(path.read_text())
        config.update(changes)
        path.write_text(json.dumps(config))

    def change_check(self, **changes) -> None:
        checks = read_checks(self.root)
        checks[0].update(changes)
        write_checks(self.root, checks)

    @verifies(
        "scenario.checks.project-python",
        "scenario.checks.project-python-missing",
        "scenario.checks.check-env-invalid",
    )
    def test_python_is_the_projects_interpreter_and_env_is_the_checks(self):
        probe = (
            "import os; print('mark=' + str(os.environ.get('MARK')), "
            "'pythonpath=' + str(os.environ.get('PYTHONPATH')))"
        )
        self.change_check(argv=["{python}", "-c", probe], env={"MARK": "yes"})
        self.configure(python="env/bin/python")
        with self.assertRaises(CheckError) as raised:
            self.run_checks(["module.a"])
        self.assertEqual("project_python_missing", raised.exception.code)
        self.assertIn(str(self.root / "env/bin/python"), str(raised.exception))
        interpreter = self.root / "env/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_text(
            f'#!/bin/sh\necho "project interpreter"\nexec {sys.executable} "$@"\n'
        )
        interpreter.chmod(0o755)
        [result] = self.run_checks(["module.a"])
        self.assertEqual("passed", result["status"])
        log = (self.logs / "check.a/output.log").read_text()
        self.assertIn("project interpreter", log)
        # The check's own env, and nothing of Concorde's runtime on the path.
        self.assertIn("mark=yes pythonpath=None", log)
        self.change_check(env={"not a name": "x"})
        with self.assertRaises(CheckError) as raised:
            self.run_checks(["module.a"])
        self.assertEqual("invalid_check", raised.exception.code)

    @verifies("scenario.checks.transport-environment")
    def test_transport_settings_are_inherited_with_explicit_overrides(self):
        transport = {
            "HTTP_PROXY": "http://upper.invalid:1234",
            "HTTPS_PROXY": "http://secure.invalid:1234",
            "ALL_PROXY": "socks5://upper.invalid:1234",
            "NO_PROXY": "upper.invalid",
            "http_proxy": "http://lower.invalid:1234",
            "https_proxy": "http://secure-lower.invalid:1234",
            "all_proxy": "socks5://lower.invalid:1234",
            "no_proxy": "lower.invalid",
            "SSL_CERT_FILE": "/transport/cert.pem",
            "SSL_CERT_DIR": "/transport/certs",
            "REQUESTS_CA_BUNDLE": "/transport/requests.pem",
            "CURL_CA_BUNDLE": "/transport/curl.pem",
            "NODE_EXTRA_CA_CERTS": "/transport/node.pem",
        }
        pollution = dict.fromkeys(
            (
                "PYTHONPATH",
                "PYTHONHOME",
                "VIRTUAL_ENV",
                "NODE_OPTIONS",
                "CONCORDE_RUN_ID",
                "CONCORDE_TASK_SESSION",
                "CLAUDE_CONFIG_DIR",
                "PI_CODING_AGENT_DIR",
                "UNLISTED_PROXY",
                "HTTP_PROXY_EXTRA",
                "TMPDIR",
                "XDG_CACHE_HOME",
                "npm_config_cache",
                "CONCORDE_CHECK_TMPDIR",
                "CONCORDE_CHECK_REPORT_DIR",
            ),
            "not-inherited",
        )
        host = {"PATH": os.environ["PATH"], "LANG": "C.UTF-8", **transport}
        with patch.dict(os.environ, {**host, **pollution}, clear=True):
            self.assertEqual(host, environment())
            overrides = {
                "http_proxy": "",
                "SSL_CERT_FILE": "/project/ca.pem",
                "PYTHONPATH": "src",
            }
            self.assertEqual(
                {**host, **overrides},
                environment({"id": "check.a", "env": overrides}),
            )
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}, environment()
            )

    @verifies(
        "scenario.checks.transport-environment", "scenario.checks.service-read-only"
    )
    def test_nested_configured_check_uses_local_proxy_and_remains_read_only(self):
        requests = []

        class Proxy(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                body = b"local proxy reached"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Proxy)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        proxy = f"http://127.0.0.1:{server.server_port}"
        probe = """
import errno, os, tempfile, urllib.request
from pathlib import Path
assert 'PYTHONPATH' not in os.environ
assert 'CONCORDE_RUN_ID' not in os.environ
assert 'NODE_OPTIONS' not in os.environ
with urllib.request.urlopen('http://concorde-proxy.invalid/probe', timeout=5) as response:
    assert response.read() == b'local proxy reached'
try:
    Path('src/a/calc.py').write_text('changed')
except OSError as error:
    assert error.errno in (errno.EROFS, errno.EACCES, errno.EPERM)
else:
    raise AssertionError('nested check changed its project')
scratch = Path(os.environ['CONCORDE_CHECK_TMPDIR'])
for key in ('TMPDIR', 'XDG_CACHE_HOME', 'npm_config_cache', 'CONCORDE_CHECK_REPORT_DIR'):
    path = Path(os.environ[key])
    assert path.is_relative_to(scratch), (key, path)
    path.mkdir(parents=True, exist_ok=True)
    (path/'probe').write_text('scratch only')
print('proxy reached; project read-only; scratch writable')
"""
        self.change_check(
            argv=["{python}", "-c", probe],
            env=dict.fromkeys(
                (
                    "TMPDIR",
                    "XDG_CACHE_HOME",
                    "npm_config_cache",
                    "CONCORDE_CHECK_REPORT_DIR",
                ),
                "/unusable",
            ),
        )
        outer = """
import json, os
from pathlib import Path
from concorde.execution.checks.checks import run_checks
os.environ['CONCORDE_RUN_ID'] = 'runtime-pollution'
os.environ['NODE_OPTIONS'] = '--runtime-pollution'
python = json.loads(Path('.concorde/config.json').read_text()).get('python')
[result] = run_checks(Path.cwd(), modules=['module.a'], python=python,
                      trace_directory=Path(os.environ['CONCORDE_CHECK_TMPDIR'])/'nested-trace')
print(Path(result['log']).read_text())
assert result['status'] == 'passed', result
"""
        result = execute_check(
            self.root,
            [sys.executable, "-c", outer],
            timeout=20,
            environment=child_environment(
                PYTHONPATH=str(RUNTIME_ROOT),
                HTTP_PROXY=proxy,
                http_proxy=proxy,
                HTTPS_PROXY=proxy,
                https_proxy=proxy,
                ALL_PROXY=proxy,
                all_proxy=proxy,
                NO_PROXY="",
                no_proxy="",
            ),
        )
        self.assertEqual(0, result.returncode, result)
        self.assertEqual(["http://concorde-proxy.invalid/probe"], requests)
        self.assertIn(
            b"proxy reached; project read-only; scratch writable", result.stdout
        )
        self.assertIn("def add", (self.root / "src/a/calc.py").read_text())

    @verifies("scenario.checks.project-python-primary")
    def test_a_task_worktree_uses_the_primary_interpreter(self):
        def git(cwd, *argv):
            subprocess.run(
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

        primary = Path(tempfile.mkdtemp()) / "primary"
        primary.mkdir()
        git(primary, "init", "-q")
        git(primary, "commit", "-q", "--allow-empty", "-m", "base")
        worktree = primary / ".claude/worktrees/t1"
        git(primary, "worktree", "add", "-q", "-b", "t1", str(worktree))
        interpreter = primary / ".venv/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_text("#!/bin/sh\n")
        interpreter.chmod(0o755)
        config = ".venv/bin/python"
        self.assertEqual(
            os.path.realpath(interpreter),
            os.path.realpath(project_python(worktree, config, "check.a")),
        )
        own = worktree / ".venv/bin/python"
        own.parent.mkdir(parents=True)
        own.write_text("#!/bin/sh\n")
        own.chmod(0o755)
        self.assertEqual(
            os.path.realpath(own),
            os.path.realpath(project_python(worktree, config, "check.a")),
        )

    def test_the_modules_that_use_a_changed_module_are_checked_too(self):
        self.assertEqual(
            ["module.b", "module.a"], checked_modules(self.repository(), ["module.b"])
        )
        self.assertEqual(["module.a"], checked_modules(self.repository(), ["module.a"]))

    @verifies(
        "scenario.checks.selective",
        "scenario.checks.selective-none",
        "scenario.checks.readiness-only",
    )
    def test_a_selective_check_runs_the_tests_verifying_the_checked_modules(self):
        (self.root / "src/a/test_answer.py").write_text(
            "def verifies(*scenarios):\n    return lambda test: test\n\n\n"
            '@verifies("scenario.a.answer")\ndef test_answer():\n    pass\n'
        )
        checks = [
            {
                "id": "check.a.selected",
                "module": "module.b",
                "argv": [
                    "{python}",
                    "-c",
                    "import sys; print(sys.argv[1:])",
                    "{tests}",
                ],
                "timeout_seconds": 60,
            },
            {
                "id": "check.a.full",
                "module": "module.a",
                "argv": ["{python}", "-c", "print('full suite')"],
                "timeout_seconds": 60,
                "when": "readiness",
            },
        ]
        write_checks(self.root, checks)
        # No test verifies a scenario of B: the selective check is skipped.
        self.assertEqual([], self.run_checks(["module.b"]))
        [result] = self.run_checks(["module.a"])
        self.assertEqual(
            ("check.a.selected", "passed"), (result["check_id"], result["status"])
        )
        log = (self.logs / "check.a.selected/output.log").read_text()
        self.assertIn("selected tests: src/a/test_answer.py::test_answer", log)
        self.assertIn("['src/a/test_answer.py::test_answer']", log)
        # Its measured digest names the selection: other Modules or a changed test file are
        # other input, although the check's own Module is unchanged.
        [check] = [
            item for item in read_checks(self.root) if item["id"] == checks[0]["id"]
        ]
        alone = self.digest(check, ["module.a"])
        self.assertEqual(alone, result["source_digest"])
        self.assertNotEqual(self.revision("module.b"), alone)
        [both] = self.run_checks(["module.a", "module.b"])
        self.assertEqual(
            self.digest(check, ["module.b", "module.a"]),
            both["source_digest"],
        )
        self.assertNotEqual(alone, both["source_digest"])
        with (self.root / "src/a/test_answer.py").open("a") as stream:
            stream.write("# changed\n")
        self.assertNotEqual(alone, self.digest(check, ["module.a"]))
        # A readiness check runs only when readiness is decided.
        results = self.run_checks(
            ["module.a"],
            stage="readiness",
        )
        self.assertEqual(
            ["check.a.full", "check.a.selected"], [item["check_id"] for item in results]
        )

    @verifies("scenario.checks.service-read-only")
    def test_a_check_cannot_change_the_worktree(self):
        check = self.root / "checks/a_check.py"
        check.write_text("open('src/a/calc.py', 'w').write('changed')\n")
        [result] = self.run_checks(["module.a"])
        self.assertEqual("failed", result["status"])
        self.assertIn("def add", (self.root / "src/a/calc.py").read_text())
        self.assertIn(
            "Read-only file system", (self.logs / "check.a/output.log").read_text()
        )

    @verifies("scenario.checks.service-stale")
    def test_input_changed_during_the_run_is_stale(self):
        from concorde.execution.checks import checks

        real = checks.execute_check

        def changing(worktree, argv, **options):
            outcome = real(worktree, argv, **options)
            (self.root / "src/a/calc.py").write_text("changed = True\n")
            return outcome

        with patch.object(checks, "execute_check", changing):
            with self.assertRaises(CheckError) as raised:
                self.run_checks(["module.a"])
        self.assertEqual("stale_evidence", raised.exception.code)
        error = service_error(raised.exception)
        validate(error, ERROR_SCHEMA)
        self.assertEqual(
            ("component", "Check execution", "stale_evidence", "environment"),
            (
                error["level"],
                error["actor"],
                error["code"],
                error["unhandled"]["reason"],
            ),
        )
        self.assertIn("check.a", error["detail"])

    @verifies("scenario.checks.service-refused")
    def test_a_refused_check_has_no_result(self):
        from concorde.execution.checks import checks
        from concorde.execution.checks.check_executor import CheckSandboxError

        def refused(*_arguments, **_options):
            raise CheckSandboxError("bubblewrap is unavailable", stderr=b"why")

        with patch.object(checks, "execute_check", refused):
            with self.assertRaises(CheckError) as raised:
                self.run_checks(["module.a"])
        self.assertEqual("check_sandbox_unavailable", raised.exception.code)
        self.assertIn("why", (self.logs / "check.a/output.log").read_text())
        node = json.loads((self.logs / "check.a/trace.json").read_text())
        self.assertEqual(("failed", "refused"), (node["status"], node["outcome"]))
        error = service_error(raised.exception)
        self.assertEqual(
            ("check_sandbox_unavailable", "environment"),
            (error["code"], error["unhandled"]["reason"]),
        )

    @verifies("scenario.checks.service-input-missing")
    def test_a_missing_input_stops_before_any_command(self):
        self.change_check(inputs=["checks/missing.py"])
        with self.assertRaises(CheckError) as raised:
            self.run_checks(["module.a"])
        self.assertIn("checks/missing.py", str(raised.exception))
        self.assertFalse((self.logs / "check.a").exists())
        # A wrong configuration is input only its sender can correct.
        error = service_error(raised.exception)
        self.assertEqual(
            ("check_input_missing", "input"),
            (error["code"], error["unhandled"]["reason"]),
        )
        system = service_error(OSError("disk"))
        self.assertEqual(
            ("system_error", "environment"),
            (system["code"], system["unhandled"]["reason"]),
        )


if __name__ == "__main__":
    unittest.main()


class ChecksFileTests(unittest.TestCase):
    """Check execution reads its own checks files, with no Spec in the worktree."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.folder = self.root / ".concorde/checks"
        self.folder.mkdir(parents=True)

    def write(self, name: str, value) -> None:
        text = value if isinstance(value, str) else json.dumps(value)
        (self.folder / name).write_text(text)

    def refused(self, code: str = "invalid_check") -> CheckError:
        with self.assertRaises(CheckError) as raised:
            configured_checks(self.root)
        self.assertEqual(code, raised.exception.code)
        return raised.exception

    @verifies("scenario.checks.checks-files")
    def test_checks_are_read_from_one_file_per_module(self):
        self.write(
            "module.b.json", {"checks": [{"id": "check.b1"}, {"id": "check.b2"}]}
        )
        self.write("module.a.json", {"checks": [{"id": "check.a"}]})
        self.assertEqual(
            [
                ("check.a", "module.a"),
                ("check.b1", "module.b"),
                ("check.b2", "module.b"),
            ],
            [(check["id"], check["module"]) for check in configured_checks(self.root)],
        )
        # A Module identity is a label: nothing checks it against a registry.
        self.write("module.unregistered.json", {"checks": [{"id": "check.c"}]})
        self.assertEqual(4, len(configured_checks(self.root)))
        (self.folder / "module.unregistered.json").unlink()
        for name, value, named in (
            ("module.c.json", {"checks": [{"id": "check.c", "module": "x"}]}, "module"),
            ("module.c.json", {"checks": [{"id": "check.a"}]}, "check.a"),
            ("module.c.json", {"checks": [], "extra": 1}, "module.c.json"),
            ("module.c.json", "{not json", "module.c.json"),
            ("checks.txt", {"checks": []}, "checks.txt"),
            (
                "module.c.json",
                {"checks": [{"id": "check.c", "inputs": ["../outside"]}]},
                "../outside",
            ),
            ("module.c.json", {"checks": [{"id": "check.c", "flag": 1}]}, "flag"),
            ("module.c.json", '{"checks": [], "checks": []}', "duplicate JSON field"),
            ("module.c.json", '{"checks": [{"id": "check.c", "x": NaN}]}', "NaN"),
        ):
            with self.subTest(name=name, value=value):
                self.write(name, value)
                self.assertIn(named, str(self.refused()))
                (self.folder / name).unlink()
        # An input reached through a directory that is a symbolic link may leave the worktree.
        outside = Path(tempfile.mkdtemp())
        (outside / "file.py").write_text("")
        (self.root / "alias").symlink_to(outside)
        self.write(
            "module.c.json",
            {"checks": [{"id": "check.c", "inputs": ["alias/file.py"]}]},
        )
        self.assertIn("symbolic link", str(self.refused()))
        (self.folder / "module.c.json").unlink()

    def test_a_nonfinite_timeout_is_an_invalid_check(self):
        for value, number in (("NaN", math.nan), ("Infinity", math.inf)):
            with self.subTest(value=value):
                # The checks file cannot hold the constant, nor can a caller's entry.
                self.write(
                    "module.a.json",
                    '{"checks": [{"id": "check.a", "argv": ["true"], '
                    f'"timeout_seconds": {value}}}]}}',
                )
                self.refused()
                with self.assertRaises(CheckError) as raised:
                    _timeout({"id": "check.a", "timeout_seconds": number})
                self.assertEqual("invalid_check", raised.exception.code)

    @verifies("scenario.checks.check-input-missing")
    def test_validating_the_checks_names_a_missing_input_and_runs_nothing(self):
        self.write(
            "module.a.json",
            {
                "checks": [
                    {"id": "check.a", "argv": ["false"], "inputs": ["src/gone.py"]}
                ]
            },
        )
        with self.assertRaises(CheckError) as raised:
            validate_checks(self.root)
        self.assertEqual("check_input_missing", raised.exception.code)
        self.assertIn("check.a", str(raised.exception))
        self.assertIn("src/gone.py", str(raised.exception))
        (self.root / "src").mkdir()
        (self.root / "src/gone.py").write_text("")
        self.assertEqual(["check.a"], [c["id"] for c in validate_checks(self.root)])

    def test_checks_run_in_a_worktree_without_specs(self):
        (self.root / "code.py").write_text("x = 1\n")
        self.write(
            "module.a.json",
            {
                "checks": [
                    {
                        "id": "check.a",
                        "argv": ["{python}", "-c", "print('ran')"],
                        "timeout_seconds": 60,
                    }
                ]
            },
        )
        logs = self.root.parent / f"{self.root.name}-logs"
        [result] = run_checks(
            self.root,
            modules=["module.a"],
            trace_directory=logs,
            # A one-shot iterator is measured alike before and after the check.
            measured={"module.a": iter(["code.py"])},
            python=sys.executable,
        )
        self.assertEqual("passed", result["status"])
        self.assertEqual(
            check_revision(
                self.root, configured_checks(self.root), "module.a", ["code.py"]
            ),
            result["source_digest"],
        )
        # The measured files are the caller's: another file set is another revision.
        self.assertNotEqual(
            result["source_digest"],
            check_revision(self.root, configured_checks(self.root), "module.a"),
        )
