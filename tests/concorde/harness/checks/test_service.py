"""The check service: selecting Modules, running their checks read-only, logs and staleness."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from concorde.harness.check_executor import execute_check
from concorde.harness.checks import (
    affected_modules,
    check_revision,
    environment,
    project_python,
    run_checks,
)
from concorde.spec.repository import SpecRepository
from concorde.spec.repository_base import SpecError
from concorde.spec.verification import verifies
from tests.concorde.harness.workers.test_workers import WorkerProject
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT


class CheckServiceTests(unittest.TestCase):
    def setUp(self):
        self.project = WorkerProject(self)
        self.root = self.project.root
        self.logs = Path(tempfile.mkdtemp())

    def repository(self):
        return SpecRepository(self.root, REPOSITORY_ROOT)

    @verifies("scenario.checks.service-run")
    def test_the_checks_of_changed_modules_run_and_log(self):
        self.assertEqual(
            ["module.a"],
            affected_modules(self.repository(), ["src/a/calc.py"]),
        )
        self.assertEqual(
            ["module.a"],
            affected_modules(self.repository(), ["specs/a/module.md"]),
        )
        [result] = run_checks(
            self.root, changed=["src/a/calc.py"], log_directory=self.logs
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
        self.assertEqual(self.logs / "check.a.log", Path(result["log"]))
        self.assertEqual(
            check_revision(self.repository(), "module.a"), result["source_digest"]
        )
        (self.root / "src/a/flag").write_text("broken")
        [failed] = run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual(("failed", 1), (failed["status"], failed["exit_code"]))
        self.assertEqual(
            [], run_checks(self.root, modules=["module.b"], log_directory=self.logs)
        )

    def configure(self, **changes) -> None:
        path = self.root / ".concorde/config.json"
        config = json.loads(path.read_text())
        config.update(changes)
        path.write_text(json.dumps(config))

    def change_check(self, **changes) -> None:
        path = self.root / ".concorde/config.json"
        config = json.loads(path.read_text())
        config["checks"][0].update(changes)
        path.write_text(json.dumps(config))

    @verifies("scenario.checks.project-python")
    def test_python_is_the_projects_interpreter_and_env_is_the_checks(self):
        probe = (
            "import os; print('mark=' + str(os.environ.get('MARK')), "
            "'pythonpath=' + str(os.environ.get('PYTHONPATH')))"
        )
        self.change_check(argv=["{python}", "-c", probe], env={"MARK": "yes"})
        self.configure(python="env/bin/python")
        with self.assertRaises(SpecError) as raised:
            run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("project_python_missing", raised.exception.code)
        self.assertIn(str(self.root / "env/bin/python"), str(raised.exception))
        interpreter = self.root / "env/bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.write_text(
            f'#!/bin/sh\necho "project interpreter"\nexec {sys.executable} "$@"\n'
        )
        interpreter.chmod(0o755)
        [result] = run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("passed", result["status"])
        log = (self.logs / "check.a.log").read_text()
        self.assertIn("project interpreter", log)
        # The check's own env, and nothing of Concorde's runtime on the path.
        self.assertIn("mark=yes pythonpath=None", log)
        self.change_check(env={"not a name": "x"})
        with self.assertRaises(SpecError) as raised:
            run_checks(self.root, modules=["module.a"], log_directory=self.logs)
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
import os
from pathlib import Path
from concorde.harness.checks import run_checks
os.environ['CONCORDE_RUN_ID'] = 'runtime-pollution'
os.environ['NODE_OPTIONS'] = '--runtime-pollution'
[result] = run_checks(Path.cwd(), modules=['module.a'],
                      log_directory=Path(os.environ['CONCORDE_CHECK_TMPDIR'])/'nested-logs')
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

    @verifies("scenario.checks.project-python")
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
        config = {"python": ".venv/bin/python"}
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
        from concorde.harness.checks import checked_modules

        self.assertEqual(
            ["module.b", "module.a"], checked_modules(self.repository(), ["module.b"])
        )
        self.assertEqual(["module.a"], checked_modules(self.repository(), ["module.a"]))

    @verifies("scenario.checks.selective")
    def test_a_selective_check_runs_the_tests_verifying_the_checked_modules(self):
        (self.root / "src/a/test_answer.py").write_text(
            "def verifies(*scenarios):\n    return lambda test: test\n\n\n"
            '@verifies("scenario.a.answer")\ndef test_answer():\n    pass\n'
        )
        path = self.root / ".concorde/config.json"
        config = json.loads(path.read_text())
        config["checks"] = [
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
        path.write_text(json.dumps(config))
        # No test verifies a scenario of B: the selective check is skipped.
        self.assertEqual(
            [], run_checks(self.root, modules=["module.b"], log_directory=self.logs)
        )
        [result] = run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual(
            ("check.a.selected", "passed"), (result["check_id"], result["status"])
        )
        log = (self.logs / "check.a.selected.log").read_text()
        self.assertIn("selected tests: src/a/test_answer.py::test_answer", log)
        self.assertIn("['src/a/test_answer.py::test_answer']", log)
        # A readiness check runs only when readiness is decided.
        results = run_checks(
            self.root,
            modules=["module.a"],
            log_directory=self.logs,
            stage="readiness",
        )
        self.assertEqual(
            ["check.a.selected", "check.a.full"], [item["check_id"] for item in results]
        )

    @verifies("scenario.checks.service-read-only")
    def test_a_check_cannot_change_the_worktree(self):
        check = self.root / "checks/a_check.py"
        check.write_text("open('src/a/calc.py', 'w').write('changed')\n")
        [result] = run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("failed", result["status"])
        self.assertIn("def add", (self.root / "src/a/calc.py").read_text())
        self.assertIn("Read-only file system", (self.logs / "check.a.log").read_text())

    @verifies("scenario.checks.service-stale")
    def test_input_changed_during_the_run_is_stale(self):
        from concorde.harness import checks

        real = checks.execute_check

        def changing(worktree, argv, **options):
            outcome = real(worktree, argv, **options)
            (self.root / "src/a/calc.py").write_text("changed = True\n")
            return outcome

        with patch.object(checks, "execute_check", changing):
            with self.assertRaises(SpecError) as raised:
                run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("stale_evidence", raised.exception.code)

    @verifies("scenario.checks.service-refused")
    def test_a_refused_check_has_no_result(self):
        from concorde.harness import checks
        from concorde.harness.check_executor import CheckSandboxError

        def refused(*_arguments, **_options):
            raise CheckSandboxError("bubblewrap is unavailable", stderr=b"why")

        with patch.object(checks, "execute_check", refused):
            with self.assertRaises(SpecError) as raised:
                run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertEqual("check_sandbox_unavailable", raised.exception.code)
        self.assertIn("why", (self.logs / "check.a.log").read_text())

    @verifies("scenario.checks.service-input-missing")
    def test_a_missing_input_stops_before_any_command(self):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        config["checks"][0]["inputs"] = ["checks/missing.py"]
        (self.root / ".concorde/config.json").write_text(json.dumps(config))
        with self.assertRaises(SpecError) as raised:
            run_checks(self.root, modules=["module.a"], log_directory=self.logs)
        self.assertIn("checks/missing.py", str(raised.exception))
        self.assertFalse((self.logs / "check.a.log").exists())


if __name__ == "__main__":
    unittest.main()
