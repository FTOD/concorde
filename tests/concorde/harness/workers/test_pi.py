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
from unittest.mock import patch

from concorde.harness import pi_backend
from concorde.harness.settings import RunPaths, sandbox_filesystem
from concorde.harness.workers import run_worker
from concorde.spec.verification import verifies
from tests.concorde.harness.workers.test_workers import WorkerProject

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
        super().__init__(test, **options)
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
        run = Path(record["run_directory"])
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
            json.loads((run / "config/settings.json").read_text()),
        )
        self.assertTrue((run / "config/auth.json").is_file())
        self.assertEqual(0o600, (run / "config/auth.json").stat().st_mode & 0o777)
        extension = (run / "control/permission.ts").read_text()
        self.assertNotIn("{} as Policy", extension)
        self.assertIn(
            json.dumps((self.project.runtime_package / "dist/index.js").as_posix()),
            extension,
        )
        self.assertIn('"rw": ["src/a/", "src/new.py"]', extension)
        self.assertTrue((run / "control/pi_policy.ts").is_file())
        self.assertTrue(record["transcript"].endswith(f"_{record['run_id']}.jsonl"))
        self.assertIn("concorde_result", first["prompt"])
        status = json.loads((run / "status.json").read_text())
        self.assertEqual(
            ("finished", "ok", "pi"),
            (status["phase"], status["status"], status["backend"]),
        )
        self.assertEqual("concorde_result", status["last_action"]["tool"])

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
        self.assertEqual(
            ["initial", "check_failures"], [r["prompt"] for r in record["rounds"]]
        )

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
        self.assertTrue((Path(record["run_directory"]) / "record.json").is_file())

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

    def test_an_error_of_pi_is_reported_with_its_cause(self):
        record = self.project.run([{"error": "429 rate limited", "exit": 1}])
        self.assertEqual("pi_failed", record["error"]["code"])
        [cause] = record["error"]["causes"]
        self.assertEqual(("component", "pi_error"), (cause["level"], cause["code"]))
        self.assertIn("429 rate limited", cause["detail"])
        self.assertIn("exit code 1", cause["detail"])

    def test_a_pi_worker_without_a_result_is_invalid(self):
        record = self.project.run([{"no_result": True, "text": "I forgot the tool."}])
        self.assertEqual("worker_result_invalid", record["error"]["code"])
        self.assertIn("I forgot the tool.", record["error"]["detail"])

    def test_the_extension_policy_uses_the_claude_sandbox_lists(self):
        run = RunPaths(self.root / ".concorde/runs/x", Path("/tmp/x"))
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
            ".git/HEAD",
        ):
            (self.worktree / path).parent.mkdir(parents=True, exist_ok=True)
            (self.worktree / path).write_text("x")
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
            "userHome": (base / "user").as_posix(),
            "sandbox": {"denyRead": [], "allowRead": [], "allowWrite": []},
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
                "git": f"{w}/.git/HEAD",
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
                "pending": f"{w}/src/new.py",
                "ro": f"{w}/specs/a.md",
                "names": f"{w}/specs/b.md",
                "undeclared": f"{w}/src/a/../notes.txt",
                "outside": "/etc/passwd",
                "git": f"{w}/.git/config",
            },
            searches={
                "src": f"{w}/src",
                "root": f"{w}",
                "b-only": f"{w}/src/b",
                "git": f"{w}/.git",
            },
        )
        self.assertIsNone(out["write:rw"])
        self.assertIsNone(out["write:pending"])
        self.assertIn("read-only", out["write:ro"])
        self.assertIn("only the name", out["write:names"])
        self.assertIn("src/notes.txt is undeclared", out["write:undeclared"])
        self.assertIn("specify task", out["write:undeclared"])
        self.assertIn("outside the task worktree", out["write:outside"])
        self.assertIn("Git metadata", out["write:git"])
        self.assertIsNone(out["search:src"])
        self.assertIsNone(out["search:root"])
        self.assertIn("holds nothing this task may read", out["search:b-only"])
        self.assertIn("Git metadata", out["search:git"])


if __name__ == "__main__":
    unittest.main()
