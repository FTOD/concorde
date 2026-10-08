"""The pi worker backend with a fake ``pi``: launch, extension, rounds, errors and progress.

What the permission extension and the sandbox enforce is covered by ``test_pi_live``; the path
decisions of ``pi_policy.ts`` are checked here under Node when Node is available.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from concorde.worker_harness import pi_backend
from concorde.worker_harness import runs as worker_runs
from concorde.worker_harness.settings import RunPaths, sandbox_filesystem
from concorde.worker_harness.workers import result_schema
from concorde.spec.verification import verifies
from tests.concorde.harness.workers.test_workers import LOOPBACK_PROXY, WorkerProject

FAKE = Path(__file__).with_name("fake_pi.py")
POLICY_SOURCE = Path(pi_backend.__file__).with_name("pi_policy.ts")
ENVIRONMENT = {
    "PATH",
    "LANG",
    "HOME",
    "TMPDIR",
    "CLAUDE_CODE_TMPDIR",
    "PI_CODING_AGENT_DIR",
    "PI_OFFLINE",
    "PI_SKIP_VERSION_CHECK",
    "PI_TELEMETRY",
}


def fake_which(name: str) -> str | None:
    return f"/usr/bin/{name}" if name in ("rg", "fd", "bwrap", "socat") else None


class PiProject(WorkerProject):
    """The worker fixture with a fake ``pi``, a fake sandbox-runtime and a pi configuration."""

    def __init__(self, test, **options):
        super().__init__(test, **{"linked": True, **options})
        self.pi = self.base / "pi"
        self.pi.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n')
        self.pi.chmod(0o755)
        self.runtime_package = self.base / "sandbox-runtime"
        (self.runtime_package / "dist").mkdir(parents=True)
        (self.runtime_package / "dist/index.js").write_text("export {};\n")
        (self.runtime_package / "vendor").mkdir()
        self.pi_config = self.base / "pi-agent"
        self.pi_config.mkdir()
        (self.pi_config / "auth.json").write_text('{"local": {"key": "k"}}')
        (self.pi_config / "models.json").write_text('{"providers": {}}')
        (self.pi_config / "settings.json").write_text('{"packages": ["npm:other"]}')
        which = patch.object(pi_backend, "which", side_effect=fake_which)
        which.start()
        test.addCleanup(which.stop)

    def request(self, plan, **options):
        values = {
            "backend": "pi",
            "pi": str(self.pi),
            "pi_config": self.pi_config,
            "sandbox_runtime": self.runtime_package,
        }
        values.update(options)
        return super().request(plan, **values)


class PiRunTests(unittest.TestCase):
    def setUp(self):
        self.project = PiProject(self)
        self.root = self.project.root

    def test_a_pi_worker_runs_with_only_the_permission_extension(self):
        record = self.project.run(
            [
                {
                    "writes": {
                        str(
                            self.root / "src/a/calc.py"
                        ): "def add(a, b):\n    return a + b\n"
                    },
                    "actions": [
                        ["read", {"path": str(self.root / "specs/a/module.md")}]
                    ],
                }
            ]
        )
        self.assertEqual("ok", record["status"], record["error"])
        self.assertEqual("pi", record["backend"])
        self.assertEqual(pi_backend.TOOL_SETS["implement"], record["tools"])
        [first] = self.project.rounds(record)
        arguments = first["argv"]
        # The runtime directory as it was just before Workers removed it.
        kept = self.project.runtime(record)
        run = Path(record["runtime_directory"])
        self.assertFalse(run.exists())
        for flag in (
            "--no-extensions",
            "--no-context-files",
            "--no-skills",
            "--no-prompt-templates",
        ):
            self.assertIn(flag, arguments)
        self.assertEqual("json", arguments[arguments.index("--mode") + 1])
        self.assertEqual(
            (run / "control/permission.ts").as_posix(),
            arguments[arguments.index("-e") + 1],
        )
        self.assertEqual(
            record["run_id"], arguments[arguments.index("--session-id") + 1]
        )
        self.assertEqual(record["run_id"], record["rounds"][0]["session"])
        self.assertEqual(
            ENVIRONMENT,
            set(first["env"])
            - {k for k in first["env"] if k.endswith("_API_KEY")}
            - {"PWD", "SHLVL", "_"},
        )
        self.assertEqual(
            (run / "config").as_posix(), first["env"]["PI_CODING_AGENT_DIR"]
        )
        self.assertEqual(first["env"]["TMPDIR"], first["env"]["CLAUDE_CODE_TMPDIR"])
        self.assertEqual(
            {"defaultProjectTrust": "never"},
            json.loads((kept / "config/settings.json").read_text()),
        )
        self.assertTrue((kept / "config/auth.json").is_file())
        self.assertEqual(0o600, (kept / "config/auth.json").stat().st_mode & 0o777)
        extension = (kept / "control/permission.ts").read_text()
        self.assertNotIn("{} as Policy", extension)
        self.assertIn(
            json.dumps((self.project.runtime_package / "dist/index.js").as_posix()),
            extension,
        )
        self.assertIn('"rw": ["src/a/", "src/new.py"]', extension)
        self.assertTrue((kept / "control/pi_policy.ts").is_file())
        # The session file pi wrote is kept as the run directory's transcript.
        trace = Path(record["run_directory"])
        self.assertEqual((trace / "transcript.jsonl").as_posix(), record["transcript"])
        self.assertIn(record["run_id"], (trace / "transcript.jsonl").read_text())
        self.assertIn("concorde_result", first["prompt"])
        status = json.loads((trace / "status.json").read_text())
        self.assertEqual(
            ("finished", "ok", "pi"),
            (status["phase"], status["status"], status["backend"]),
        )
        self.assertEqual("concorde_result", status["last_action"]["tool"])

    @verifies("scenario.workers.session-proxy")
    def test_a_pi_worker_behind_a_loopback_proxy_uses_it(self):
        with patch.dict(os.environ, LOOPBACK_PROXY):
            record = self.project.run([{}])
        self.assertEqual("ok", record["status"], record["error"])
        [first] = self.project.rounds(record)
        for name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            self.assertEqual(LOOPBACK_PROXY[name], first["env"][name])
        self.assertEqual("10.0.0.0/8", first["env"]["NO_PROXY"])
        self.assertEqual("10.0.0.0/8", first["env"]["no_proxy"])
        self.assertNotIn("ALL_PROXY", first["env"])

    @verifies("scenario.workers.project-interpreter")
    def test_the_project_interpreter_comes_first_on_pi(self):
        python = (self.root / ".venv/bin/python").as_posix()
        record = self.project.run([{}], project_python=python)
        self.assertEqual("ok", record["status"], record["error"])
        [first] = self.project.rounds(record)
        self.assertEqual(
            f"{self.root}/.venv/bin{os.pathsep}{os.environ.get('PATH')}",
            first["env"]["PATH"],
        )
        self.assertIn(f"The project's own interpreter is {python}", first["prompt"])

    def test_a_resume_round_continues_the_same_pi_session(self):
        flag = str(self.root / "src/a/flag")
        record = self.project.run([{"writes": {flag: "bad"}}, {"writes": {flag: "ok"}}])
        self.assertEqual("ok", record["status"], record["error"])
        first, second = self.project.rounds(record)
        self.assertEqual(
            first["argv"][first["argv"].index("--session-id") + 1],
            second["argv"][second["argv"].index("--session-id") + 1],
        )
        self.assertIn("check.a", second["prompt"])
        self.assertEqual(["initial", "repair"], [r["prompt"] for r in record["rounds"]])

    @verifies("scenario.workers.pi-runtime-missing")
    def test_a_pi_run_without_its_runtime_is_refused(self):
        record = self.project.run([{}], sandbox_runtime=self.project.base / "missing")
        self.assertEqual("failed", record["status"])
        error = record["error"]
        self.assertEqual("pi_runtime_missing", error["code"])
        self.assertIn("sandbox-runtime", error["detail"])
        self.assertIn("npm install --prefix", error["detail"])
        self.assertIn("@anthropic-ai/sandbox-runtime@0.0.77", error["detail"])
        self.assertEqual([], record["rounds"])
        self.assertTrue((Path(record["run_directory"]) / "trace.json").is_file())

    @verifies("scenario.workers.pi-settings-independent")
    def test_a_pi_worker_reads_nothing_of_the_users_pi_settings(self):
        settings = self.project.pi_config / "settings.json"
        for content in (
            json.dumps(
                {
                    "defaultProvider": "local-openai",
                    "defaultModel": "gpt-6",
                    "defaultThinkingLevel": "high",
                    "enabledModels": ["local-openai/*"],
                    "modelThinkingLevels": {"local-openai/gpt-6": "xhigh"},
                    "packages": ["npm:other"],
                    "defaultProjectTrust": "always",
                }
            ),
            # Not even a file pi would refuse stops the worker: it is never read.
            '{"defaultModel": 6,\n',
        ):
            settings.write_text(content)
            record = self.project.run(
                [{}],
                model="claude-sonnet-5",
                local_model="anthropic/claude-sonnet-5",
                reasoning="low",
            )
            self.assertEqual("ok", record["status"], record["error"])
            kept = self.project.runtime(record) / "config"
            self.assertEqual(
                {"defaultProjectTrust": "never"},
                json.loads((kept / "settings.json").read_text()),
            )
            # How to reach a model still comes from the user's pi.
            for name in ("auth.json", "models.json"):
                self.assertEqual(
                    (self.project.pi_config / name).read_text(),
                    (kept / name).read_text(),
                )
            [first] = self.project.rounds(record)
            arguments = first["argv"]
            self.assertEqual(
                "anthropic/claude-sonnet-5", arguments[arguments.index("--model") + 1]
            )
            self.assertEqual("low", arguments[arguments.index("--thinking") + 1])

    def test_the_pi_directory_is_found_as_pi_finds_it(self):
        agent = self.project.base / "home/agent-dir"
        agent.mkdir(parents=True)
        (agent / "auth.json").write_text('{"local": {"key": "found"}}')
        (agent / "settings.json").write_text('{"defaultModel": "gpt-6"}')
        config = self.project.base / "config"
        config.mkdir()
        request = SimpleNamespace(pi_config=None)
        with patch.dict(
            os.environ,
            {
                "HOME": str(self.project.base / "home"),
                "PI_CODING_AGENT_DIR": "~/agent-dir",
            },
        ):
            pi_backend.PiBackend()._configure(request, SimpleNamespace(config=config))
        self.assertEqual(
            '{"local": {"key": "found"}}', (config / "auth.json").read_text()
        )
        self.assertEqual(
            {"defaultProjectTrust": "never"},
            json.loads((config / "settings.json").read_text()),
        )

    @verifies("scenario.workers.pi-limit")
    def test_a_limit_entry_ends_the_run_at_its_limit(self):
        record = self.project.run(
            [{"limit": {"limit": "turns", "value": 3, "maximum": 2}}]
        )
        self.assertEqual("failed", record["status"])
        self.assertEqual("worker_limit_reached", record["error"]["code"])
        [cause] = record["error"]["causes"]
        self.assertEqual(
            ("pi_limit_reached", "exhausted"),
            (cause["code"], cause["unhandled"]["reason"]),
        )
        self.assertIn("turns limit (3 reached, at most 2 allowed)", cause["detail"])
        self.assertEqual(
            ("component", "pi process (pi -p)"), (cause["level"], cause["actor"])
        )

    def test_an_error_of_pi_is_reported_with_its_cause(self):
        record = self.project.run([{"error": "429 rate limited", "exit": 1}], retries=0)
        self.assertEqual("pi_failed", record["error"]["code"])
        self.assertEqual("exhausted", record["error"]["unhandled"]["reason"])
        [cause] = record["error"]["causes"]
        self.assertEqual(("component", "pi_error"), (cause["level"], cause["code"]))
        self.assertIn("429 rate limited", cause["detail"])
        self.assertIn("exit code 1", cause["detail"])

    @verifies("scenario.workers.transient-retry")
    def test_a_transient_error_is_retried_in_the_same_session(self):
        error = (
            "gateway_concurrency_limit: Concurrency limit exceeded for user, please "
            "retry later"
        )
        written = self.root / "src/a/calc.py"
        record = self.project.run(
            [
                {
                    "writes": {str(written): "def add(a, b):\n    return a + b\n"},
                    "actions": [["write", {"path": str(written)}]],
                    "error": error,
                },
                {},
            ],
            check_modules=None,
        )
        self.assertEqual("ok", record["status"], record["error"])
        first, second = record["rounds"]
        self.assertEqual(
            {"error": error, "retried": True, "delay_seconds": 0}, first["transient"]
        )
        self.assertEqual(("initial", "retry"), (first["prompt"], second["prompt"]))
        self.assertEqual(["src/a/calc.py"], second["audit"]["changed"])
        calls = self.project.rounds(record)
        session = [
            call["argv"][call["argv"].index("--session-id") + 1] for call in calls
        ]
        self.assertEqual(session[0], session[1])
        self.assertIn(error, calls[1]["prompt"])
        self.assertIn("Continue your task", calls[1]["prompt"])
        node = json.loads(
            (Path(record["run_directory"]) / "rounds/1/trace.json").read_text()
        )
        self.assertEqual("retry", node["outcome"])
        self.assertTrue(node["content"]["data"]["transient"]["retried"])
        kept = worker_runs.read_record(self.project.trace, record["run_id"])
        self.assertEqual(first["transient"], kept["rounds"][0]["transient"])

    @verifies("scenario.workers.retries-limited")
    def test_retries_stop_at_their_limit(self):
        record = self.project.run(
            [{"error": "503 Service Unavailable"}], check_modules=None, retries=2
        )
        self.assertEqual(3, len(record["rounds"]))
        error = record["error"]
        self.assertEqual(
            ("pi_failed", "exhausted"), (error["code"], error["unhandled"]["reason"])
        )
        self.assertIn("at most 2 time(s)", error["unhandled"]["explanation"])
        self.assertEqual(2, len(error["attempts"]))
        self.assertIn("retry 2 of 2", error["attempts"][1])
        self.assertEqual(
            {
                "error": "503 Service Unavailable",
                "retried": False,
                "delay_seconds": None,
            },
            record["rounds"][-1]["transient"],
        )

    @verifies("scenario.workers.lasting-error-not-retried")
    def test_any_other_error_fails_at_once(self):
        for message in (
            "insufficient_quota: You exceeded your current quota, please retry later",
            "invalid model id",
        ):
            with self.subTest(message=message):
                record = self.project.run([{"error": message}], check_modules=None)
                self.assertEqual(1, len(record["rounds"]))
                self.assertEqual("pi_failed", record["error"]["code"])
                self.assertEqual("environment", record["error"]["unhandled"]["reason"])
                self.assertNotIn("transient", record["rounds"][0])

    @verifies("scenario.workers.transient-violation-not-retried")
    def test_a_round_that_wrote_outside_the_grant_is_not_retried(self):
        outside = self.root / "src/bmod/other.py"
        record = self.project.run(
            [{"writes": {str(outside): "x = 1\n"}, "error": "Request timed out."}],
            check_modules=None,
        )
        self.assertEqual(1, len(record["rounds"]))
        error = record["error"]
        self.assertEqual("pi_failed", error["code"])
        self.assertIn("outside the grant", error["detail"])
        self.assertIn("src/bmod/other.py", error["detail"])
        self.assertIn("never retries", error["unhandled"]["explanation"])
        self.assertFalse(record["rounds"][0]["transient"]["retried"])

    def test_a_pi_worker_without_a_result_is_invalid(self):
        record = self.project.run([{"no_result": True, "text": "I forgot the tool."}])
        self.assertEqual("worker_result_invalid", record["error"]["code"])
        self.assertIn("I forgot the tool.", record["error"]["detail"])

    def test_the_extension_policy_uses_the_claude_sandbox_lists(self):
        run = RunPaths(
            self.project.base / "runtime", self.project.trace / "workers/x", "x"
        )
        request = self.project.request([])
        programs = {
            "rg": "/usr/bin/rg",
            "fd": "/usr/bin/fd",
            "sandbox_runtime": str(self.project.runtime_package),
        }
        value = pi_backend.policy(
            request, self.root, run, programs, self.project.home, {"type": "object"}
        )
        expected = sandbox_filesystem(
            self.root, self.project.grant, run, (), self.project.home
        )
        self.assertEqual(expected["denyRead"], value["sandbox"]["denyRead"])
        self.assertEqual(expected["allowWrite"], value["sandbox"]["allowWrite"])
        self.assertEqual(expected["denyWrite"], value["sandbox"]["denyWrite"])
        self.assertEqual(
            sorted(
                set(expected["allowRead"])
                | {(self.project.runtime_package / "vendor").as_posix()}
            ),
            value["sandbox"]["allowRead"],
        )
        self.assertEqual(
            [run.control.as_posix(), run.config.as_posix()], value["hidden"]
        )

    @verifies("scenario.workers.pi-commands-sandboxed")
    def test_the_extension_sandbox_denies_reads_of_names_below_a_readable_directory(
        self,
    ):
        run = RunPaths(
            self.project.base / "runtime", self.project.trace / "workers/x", "x"
        )
        self.project.grant = {
            **self.project.grant,
            "entries": [
                *self.project.grant["entries"],
                {"path": "src/a/notes.txt", "level": "names"},
                {"path": "src/a/generated/", "level": "names"},
            ],
        }
        request = self.project.request([])
        programs = {
            "rg": "/usr/bin/rg",
            "fd": "/usr/bin/fd",
            "sandbox_runtime": str(self.project.runtime_package),
        }
        value = pi_backend.policy(
            request, self.root, run, programs, self.project.home, {"type": "object"}
        )
        # pi's extension receives only these sandbox lists, so the names paths below the rw
        # directory are in their denyRead, which wins inside the wider allowRead of src/a.
        root = Path(os.path.realpath(self.root))
        for path in ("src/a/notes.txt", "src/a/generated"):
            self.assertIn(f"{root}/{path}", value["sandbox"]["denyRead"])
        self.assertIn(f"{root}/src/a", value["sandbox"]["allowRead"])


POLICY_PROBE = """
import { readDecision, writeDecision, searchDecision, resolveLikePi } from %(source)s;
const policy = %(policy)s;
const out = {};
for (const [name, path] of Object.entries(%(reads)s)) out["read:" + name] = readDecision(policy, path);
for (const [name, path] of Object.entries(%(writes)s)) out["write:" + name] = writeDecision(policy, path);
for (const [name, path] of Object.entries(%(searches)s)) out["search:" + name] = searchDecision(policy, path);
out["resolve"] = resolveLikePi("@~/notes.txt", "/work", "/home/run");
out["resolve-relative"] = resolveLikePi("src/../a.txt", "/work", "/home/run");
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(shutil.which("node"), "Node is needed to run pi_policy.ts")
class PiPolicyTests(unittest.TestCase):
    """The read, write and search tables of the pi run mechanics, run by Node."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        base = Path(os.path.realpath(directory.name))
        self.base = base
        self.worktree = base / "wt"
        for path in (
            "src/a/calc.py",
            "src/b/secret.py",
            "specs/a.md",
            "specs/b.md",
            ".git",
            "src/a/sub/.git",
        ):
            (self.worktree / path).parent.mkdir(parents=True, exist_ok=True)
            (self.worktree / path).write_text("x")
        # The primary worktree lies outside the user's home, its common Git directory with it.
        self.primary = base / "primary"
        for path in (".git/worktrees/wt/HEAD", ".git/config", "src/main.py"):
            (self.primary / path).parent.mkdir(parents=True, exist_ok=True)
            (self.primary / path).write_text("x")
        for name in ("work", "home", "tmp", "control", "config", "user/other"):
            (base / name).mkdir(parents=True)
        (self.worktree / "src/a/link.py").symlink_to(self.worktree / "src/b/secret.py")
        self.policy = {
            "worktree": self.worktree.as_posix(),
            "rw": ["src/a/", "src/new.py"],
            "ro": ["specs/a.md"],
            "names": ["specs/b.md"],
            "hidden": [(base / "control").as_posix(), (base / "config").as_posix()],
            "own": [(base / name).as_posix() for name in ("work", "home", "tmp")],
            "runtime": [],
            "git": [
                (self.primary / ".git").as_posix(),
                (self.worktree / ".git").as_posix(),
                (self.worktree / "src/a/sub/.git").as_posix(),
            ],
            "primary": self.primary.as_posix(),
            "userHome": (base / "user").as_posix(),
            "sandbox": {
                "denyRead": [],
                "allowRead": [],
                "allowWrite": [],
                "denyWrite": [],
            },
            "programs": {"rg": "rg", "fd": "fd"},
            "limits": {"maxTurns": 1, "maxBudgetUsd": None},
            "resultSchema": {},
        }

    def decide(self, reads=None, writes=None, searches=None) -> dict:
        probe = self.base / "probe.mts"
        probe.write_text(
            POLICY_PROBE
            % {
                "source": json.dumps(POLICY_SOURCE.as_posix()),
                "policy": json.dumps(self.policy),
                "reads": json.dumps(reads or {}),
                "writes": json.dumps(writes or {}),
                "searches": json.dumps(searches or {}),
            }
        )
        completed = subprocess.run(
            ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    @verifies("scenario.workers.pi-file-tools-denied")
    def test_the_read_table(self):
        w = self.worktree
        out = self.decide(
            reads={
                "rw": f"{w}/src/a/calc.py",
                "ro": f"{w}/specs/a.md",
                "names": f"{w}/specs/b.md",
                "ungranted": f"{w}/src/b/secret.py",
                "git": f"{w}/.git",
                "submodule-git": f"{w}/src/a/sub/.git",
                "common-git": f"{self.primary}/.git/worktrees/wt/HEAD",
                "primary": f"{self.primary}/src/main.py",
                "link-to-ungranted": f"{w}/src/a/link.py",
                "config": f"{self.base}/config/auth.json",
                "work": f"{self.base}/work/notes.txt",
                "other-project": f"{self.base}/user/other/x",
                "system": "/etc/hostname",
            }
        )
        self.assertIsNone(out["read:rw"])
        self.assertIsNone(out["read:ro"])
        self.assertIn("only the name of specs/b.md", out["read:names"])
        self.assertIn("not in this task's grant", out["read:ungranted"])
        self.assertIn("Git metadata", out["read:git"])
        self.assertIn("Git metadata", out["read:submodule-git"])
        self.assertIn("Git metadata", out["read:common-git"])
        self.assertIn("outside this task's boundary", out["read:primary"])
        self.assertIn(
            "src/b/secret.py is not in this task's grant", out["read:link-to-ungranted"]
        )
        self.assertIn("belongs to the host", out["read:config"])
        self.assertIsNone(out["read:work"])
        self.assertIn("outside this task's boundary", out["read:other-project"])
        self.assertIsNone(out["read:system"])
        self.assertEqual("/home/run/notes.txt", out["resolve"])
        self.assertEqual("/work/a.txt", out["resolve-relative"])

    @verifies("scenario.workers.pi-file-tools-denied")
    def test_the_write_and_search_tables(self):
        w = self.worktree
        out = self.decide(
            writes={
                "rw": f"{w}/src/a/calc.py",
                "rw-file": f"{w}/src/new.py",
                "ro": f"{w}/specs/a.md",
                "names": f"{w}/specs/b.md",
                "undeclared": f"{w}/src/a/../notes.txt",
                "outside": "/etc/passwd",
                "git": f"{w}/.git",
                "submodule-git": f"{w}/src/a/sub/.git",
            },
            searches={
                "src": f"{w}/src",
                "root": f"{w}",
                "b-only": f"{w}/src/b",
                "git": f"{w}/.git",
                "common-git": f"{self.primary}/.git",
            },
        )
        self.assertIsNone(out["write:rw"])
        self.assertIsNone(out["write:rw-file"])
        self.assertIn("read-only", out["write:ro"])
        self.assertIn("only the name", out["write:names"])
        self.assertIn(
            "src/notes.txt is not in this task's grant", out["write:undeclared"]
        )
        self.assertIn(
            "created and bound to a Module by the task level", out["write:undeclared"]
        )
        self.assertIn("another Module binds", out["write:undeclared"])
        self.assertEqual("Git metadata is not available to workers", out["write:git"])
        self.assertEqual(
            "Git metadata is not available to workers", out["write:submodule-git"]
        )
        self.assertIn("outside the task worktree", out["write:outside"])
        self.assertIsNone(out["search:src"])
        self.assertIsNone(out["search:root"])
        self.assertIn("holds nothing this task may read", out["search:b-only"])
        self.assertIn("Git metadata", out["search:git"])
        self.assertIn("Git metadata", out["search:common-git"])

    @verifies("scenario.workers.write-through-link")
    def test_a_write_through_a_link_is_judged_by_its_target(self):
        w = self.worktree
        (w / "src/a/to-spec.md").symlink_to(w / "specs/a.md")
        (w / "src/a/to-outside.py").symlink_to(self.base / "elsewhere.py")
        (w / "specs/to-calc.py").symlink_to(w / "src/a/calc.py")
        out = self.decide(
            writes={
                "to-secret": f"{w}/src/a/link.py",
                "to-spec": f"{w}/src/a/to-spec.md",
                "to-outside": f"{w}/src/a/to-outside.py",
                "to-rw": f"{w}/specs/to-calc.py",
            }
        )
        self.assertIn(
            f"src/b/secret.py (the target of the symbolic link {w}/src/a/link.py) is not "
            "in this task's grant",
            out["write:to-secret"],
        )
        self.assertIn(
            "specs/a.md (the target of the symbolic link", out["write:to-spec"]
        )
        self.assertIn("read-only", out["write:to-spec"])
        self.assertIn(
            f"is a symbolic link to {self.base}/elsewhere.py, outside the task worktree",
            out["write:to-outside"],
        )
        self.assertIsNone(out["write:to-rw"])

    @verifies("scenario.workers.most-specific-entry")
    def test_a_file_listed_apart_below_a_rw_directory_keeps_its_level(self):
        w = self.worktree
        self.policy["ro"].append("src/a/calc.py")
        self.policy["names"].append("src/a/sub/")
        out = self.decide(
            reads={"ro": f"{w}/src/a/calc.py"},
            writes={
                "ro": f"{w}/src/a/calc.py",
                "names": f"{w}/src/a/sub/x.py",
                "rw": f"{w}/src/a/other.py",
            },
        )
        self.assertIsNone(out["read:ro"])
        self.assertIn("src/a/calc.py is read-only", out["write:ro"])
        self.assertIn("only the name of src/a/sub/x.py", out["write:names"])
        self.assertIsNone(out["write:rw"])

    @verifies("scenario.workers.runtime-paths-readable")
    def test_a_runtime_path_inside_the_worktree_is_readable(self):
        w = self.worktree
        (w / ".venv/lib").mkdir(parents=True)
        (w / ".venv/lib/site.py").write_text("x")
        self.policy["runtime"] = [(w / ".venv").as_posix()]
        out = self.decide(
            reads={
                "runtime": f"{w}/.venv/lib/site.py",
                "beside": f"{w}/src/b/secret.py",
            },
            writes={"runtime": f"{w}/.venv/lib/site.py"},
            searches={"runtime": f"{w}/.venv"},
        )
        self.assertIsNone(out["read:runtime"])
        self.assertIsNone(out["search:runtime"])
        self.assertIn("not in this task's grant", out["read:beside"])
        self.assertIn("not in this task's grant", out["write:runtime"])


def pi_package() -> Path | None:
    """The installed pi package the ``pi`` command runs, or None."""
    command = os.environ.get("CONCORDE_PI") or shutil.which("pi")
    if not command:
        return None
    for parent in Path(os.path.realpath(command)).parents:
        manifest = parent / "package.json"
        if manifest.is_file():
            try:
                name = json.loads(manifest.read_text()).get("name")
            except ValueError:
                return None
            return parent if name == "@earendil-works/pi-coding-agent" else None
    return None


PI_PACKAGE = pi_package()
EXTENSION_PROBE = """
import extension from "./permission.ts";
import { validateToolArguments } from "@earendil-works/pi-ai";
const tools = {}, handlers = {}, entries = [], out = {};
extension({
  registerTool: (tool) => { tools[tool.name] = tool; },
  on: (event, handler) => { handlers[event] = handler; },
  appendEntry: (type, data) => entries.push({ type, data }),
});
let aborted = 0;
const ctx = { cwd: %(work)s, abort() { aborted++; } };
async function attempt(name, run) {
  try { out[name] = { ok: await run() }; } catch (error) { out[name] = { error: String(error.message ?? error) }; }
}
await attempt("read-granted", async () => (await tools.read.execute("1", { path: %(granted)s }, undefined, undefined, ctx)).content[0].text);
await attempt("read-variant", async () => (await tools.read.execute("2", { path: %(variant)s }, undefined, undefined, ctx)).content[0].text);
const result = tools.concorde_result;
const call = (args) => ({ type: "toolCall", id: "r", name: "concorde_result", arguments: args });
await attempt("result-invalid", async () => validateToolArguments(result, call({ status: "maybe" })));
await attempt("result-valid", async () => validateToolArguments(result, call(%(valid)s)));
await attempt("result-ends", async () => (await result.execute("r", %(valid)s)).terminate);
for (const total of [0.3, 0.3]) await handlers.message_end({ message: { role: "assistant", usage: { cost: { total } } } }, ctx);
await handlers.message_end({ message: { role: "user", usage: { cost: { total: 5 } } } }, ctx);
out.blocked = await handlers.tool_call({}, ctx);
out.entries = entries;
out.aborted = aborted;
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(
    shutil.which("node") and PI_PACKAGE is not None,
    "Node and an installed pi are needed to load the permission extension",
)
class PiExtensionTests(unittest.TestCase):
    """The generated permission extension, loaded by Node with pi's own tools and validation and
    a recording stand-in for pi's extension API."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.base = Path(os.path.realpath(directory.name))
        self.worktree = self.base / "wt"
        (self.worktree / "notes").mkdir(parents=True)
        # Only the NFC spelling is granted; only the NFD spelling exists.
        self.granted = self.worktree / "notes/caf\u00e9.txt"
        (self.worktree / "notes/cafe\u0301.txt").write_text("hidden")
        (self.worktree / "notes/open.txt").write_text("visible")
        (self.base / "work").mkdir()
        extension = self.base / "extension"
        modules = extension / "node_modules/@earendil-works"
        modules.mkdir(parents=True)
        (modules / "pi-coding-agent").symlink_to(PI_PACKAGE)
        dependencies = PI_PACKAGE / "node_modules"
        (modules / "pi-ai").symlink_to(dependencies / "@earendil-works/pi-ai")
        (extension / "node_modules/typebox").symlink_to(dependencies / "typebox")
        stub = self.base / "sandbox-runtime"
        (stub / "dist").mkdir(parents=True)
        (stub / "dist/index.js").write_text("export const SandboxManager = {};\n")
        shutil.copy2(POLICY_SOURCE, extension / "pi_policy.ts")
        policy = {
            "worktree": self.worktree.as_posix(),
            "rw": [],
            "ro": ["notes/caf\u00e9.txt", "notes/open.txt"],
            "names": [],
            "hidden": [],
            "own": [(self.base / "work").as_posix()],
            "runtime": [],
            "git": [],
            "primary": (self.base / "primary").as_posix(),
            "userHome": (self.base / "home").as_posix(),
            "sandbox": {
                "denyRead": [],
                "allowRead": [],
                "allowWrite": [],
                "denyWrite": [],
            },
            "programs": {"rg": "rg", "fd": "fd"},
            "limits": {"maxTurns": 10, "maxBudgetUsd": 0.5},
            "resultSchema": result_schema(None),
        }
        (extension / "permission.ts").write_text(
            pi_backend.extension_source(policy, stub)
        )
        self.extension = extension

    def probe(self) -> dict:
        valid = {
            "status": "ok",
            "summary": "done",
            "error": None,
            "proposed_deletions": [],
            "output": {},
        }
        probe = self.extension / "probe.mts"
        probe.write_text(
            EXTENSION_PROBE
            % {
                "work": json.dumps((self.base / "work").as_posix()),
                "granted": json.dumps((self.worktree / "notes/open.txt").as_posix()),
                "variant": json.dumps(self.granted.as_posix()),
                "valid": json.dumps(valid),
            }
        )
        completed = subprocess.run(
            ["node", "--experimental-strip-types", "--no-warnings", str(probe)],
            cwd=self.extension,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout.strip().splitlines()[-1])

    @verifies("scenario.workers.pi-file-tools-denied")
    def test_a_read_is_checked_on_the_file_pi_opens(self):
        out = self.probe()
        self.assertEqual({"ok": "visible"}, out["read-granted"])
        # pi falls back to the NFD spelling, which the grant does not name.
        self.assertIn("Concorde grant:", out["read-variant"]["error"])
        self.assertIn("is not in this task's grant", out["read-variant"]["error"])

    @verifies("scenario.workers.pi-invalid-result-retried")
    def test_pi_validates_the_result_before_it_ends_the_run(self):
        out = self.probe()
        self.assertIn("error", out["result-invalid"])
        self.assertIn("status", out["result-invalid"]["error"])
        self.assertEqual("ok", out["result-valid"]["ok"]["status"])
        self.assertEqual({"ok": True}, out["result-ends"])

    @verifies("scenario.workers.pi-budget-limit")
    def test_the_extension_stops_the_run_over_its_budget(self):
        out = self.probe()
        self.assertEqual(
            [
                {
                    "type": "concorde-limit",
                    "data": {"limit": "budget", "value": 0.6, "maximum": 0.5},
                }
            ],
            out["entries"],
        )
        self.assertEqual(1, out["aborted"])
        self.assertEqual(
            {
                "block": True,
                "reason": "Concorde grant: the run reached its budget limit",
            },
            out["blocked"],
        )


if __name__ == "__main__":
    unittest.main()
