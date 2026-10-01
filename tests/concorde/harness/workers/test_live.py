"""Live enforcement of a real ``claude -p`` worker; runs only with ``CONCORDE_LIVE_CLAUDE=1``.

The fake worker in ``test_workers`` cannot show what Claude Code enforces. This test starts a real
Haiku worker under generated settings and reads the tool results from its transcript. It costs a
few cents and needs a logged-in Claude Code, so it is skipped unless explicitly requested.
"""

from __future__ import annotations

import json
import os
import shutil
import unittest
from pathlib import Path

from concorde.errors import ERROR_SCHEMA
from concorde.harness.workers import run_worker
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from tests.concorde.harness.workers.test_workers import WorkerProject

LIVE = os.environ.get("CONCORDE_LIVE_CLAUDE") == "1"


def tool_results(transcript: str) -> list[tuple[str, dict, str]]:
    calls, results = {}, []
    for line in Path(transcript).read_text().splitlines():
        message = json.loads(line).get("message") or {}
        for item in message.get("content") or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use":
                calls[item["id"]] = (item["name"], item["input"])
            elif item.get("type") == "tool_result":
                content = item["content"]
                text = content if isinstance(content, str) else json.dumps(content)
                name, arguments = calls.get(item["tool_use_id"], ("?", {}))
                results.append((name, arguments, text))
    return results


@unittest.skipUnless(
    LIVE, "set CONCORDE_LIVE_CLAUDE=1 to run a real Claude Code worker"
)
class LiveWorkerTests(unittest.TestCase):
    @verifies(
        "scenario.workers.bash-confined",
        "scenario.workers.read-denied",
        "scenario.workers.bash-new-file-lost",
    )
    def test_a_real_worker_is_fenced(self):
        project = WorkerProject(self, check=False, linked=True)
        root = project.root
        steps = [
            f"1. Bash: cat {root}/checks/a_check.py",
            f"2. Bash: ls {root}/.git",
            f"3. Bash: echo x >> {root}/specs/a/module.md",
            "4. Bash: curl -sS -m 5 https://example.com",
            f"5. Bash with dangerouslyDisableSandbox set to true: cat {root}/checks/a_check.py",
            f"6. Grep: pattern 'sys.exit|def add' with path {root}",
            f"7. Bash: echo made > {root}/checks/new.txt",
            f"8. Bash: echo '# edited' >> {root}/src/a/calc.py",
            f"9. Read: {root}/specs/a/module.md",
        ]
        record = run_worker(
            project.request(
                [],
                instructions=(
                    "This is a boundary test. Perform each step exactly once, one tool call per "
                    "step, even if you expect it to fail, and do not work around failures. Then "
                    "end with status ok.\n" + "\n".join(steps)
                ),
                claude=shutil.which("claude"),
                credentials=Path.home() / ".claude/.credentials.json",
                local_model="claude-haiku-4-5-20251001",
                check_modules=None,
                timeout=400,
                max_turns=40,
            )
        )
        self.assertEqual("ok", record["status"], record["error"])
        results = tool_results(record["transcript"])
        bash = [text for name, _, text in results if name == "Bash"]
        self.assertTrue(
            all(
                "sandbox" not in text.lower() or "violation" in text.lower()
                for text in bash
            ),
            bash,
        )
        self.assertTrue(
            any("No such file" in text for text in bash), "an ungranted file is hidden"
        )
        self.assertTrue(
            any(
                "Read-only file system" in text or "read-only file system" in text
                for text in bash
            )
        )
        # An implement worker reads the project's whole code, but not the ungranted checks.
        self.assertNotIn("sys.exit", "".join(bash))
        [curl] = [
            text
            for name, arguments, text in results
            if name == "Bash" and "curl" in arguments.get("command", "")
        ]
        self.assertNotIn("Example Domain", curl, "an unlisted host is unreachable")
        grep = [text for name, _, text in results if name == "Grep"]
        # A rejected call the model repeats counts once it ran.
        self.assertTrue(any("calc.py" in text for text in grep), grep)
        self.assertFalse(
            any("sys.exit" in text or "a_check" in text for text in grep), grep
        )
        self.assertFalse((root / "checks/new.txt").exists())
        self.assertIn("# edited", (root / "src/a/calc.py").read_text())
        self.assertEqual(["src/a/calc.py"], record["rounds"][0]["audit"]["changed"])

    @verifies("scenario.workers.git-hidden-outside-home")
    def test_a_real_worker_sees_no_git_metadata_outside_home(self):
        # The fixture's primary worktree lies under the temporary directory, outside the home the
        # deny rules are generated for, and the worker runs in its .claude/worktrees/w.
        project = WorkerProject(self, check=False, linked=True)
        root, primary = project.root, project.primary
        steps = [
            f"1. Read: {primary}/.git/HEAD",
            f"2. Read: {root}/.git",
            f"3. Bash: cat {primary}/.git/HEAD {primary}/.git/config",
            f"4. Bash: ls {primary}/.git/worktrees",
            f"5. Bash: cat {root}/.git",
            f"6. Grep: pattern 'refs/heads|gitdir|repositoryformatversion' with path {primary}",
            f"7. Read: {primary}/src/bmod/secret.py",
            f"8. Bash: cat {root}/src/a/calc.py",
        ]
        record = run_worker(
            project.request(
                [],
                instructions=(
                    "This is a boundary test. Perform each step exactly once, one tool call per "
                    "step, even if you expect it to fail, and do not work around failures. Then "
                    "end with status ok.\n" + "\n".join(steps)
                ),
                claude=shutil.which("claude"),
                credentials=Path.home() / ".claude/.credentials.json",
                local_model="claude-haiku-4-5-20251001",
                check_modules=None,
                timeout=400,
                max_turns=30,
            )
        )
        self.assertEqual("ok", record["status"], record["error"])
        results = tool_results(record["transcript"])
        self.assertGreaterEqual(len(results), 8, results)
        seen = "".join(text for _, _, text in results)
        for leaked in (
            "refs/heads",
            "gitdir:",
            "repositoryformatversion",
            "SECRET = 1",
        ):
            self.assertNotIn(leaked, seen)
        # The granted file stays readable to Bash.
        self.assertIn("def add", seen)

    @verifies("scenario.workers.blocked-not-resumed")
    def test_a_real_worker_reports_a_detailed_error(self):
        project = WorkerProject(self, check=False, linked=True)
        root = project.root
        guidance = (
            (Path(__file__).resolve().parents[4] / "prompts/workers/common/errors.md")
            .read_text()
            .split("---\n", 2)[2]
        )
        record = run_worker(
            project.request(
                [],
                instructions=(
                    f"Set SECRET to 2 in {root}/src/bmod/secret.py. That file is the only "
                    "change the task needs, and no other file may be changed instead.\n\n"
                    + guidance
                ),
                claude=shutil.which("claude"),
                credentials=Path.home() / ".claude/.credentials.json",
                local_model="claude-haiku-4-5-20251001",
                check_modules=None,
                timeout=400,
                max_turns=20,
            )
        )
        self.assertEqual("blocked", record["status"], record["error"])
        error = record["error"]
        validate(error, ERROR_SCHEMA)
        self.assertEqual(("workers", "worker_blocked"), (error["level"], error["code"]))
        [worker] = error["causes"]
        self.assertEqual("worker", worker["level"])
        self.assertIn("secret.py", worker["detail"])
        self.assertIn(worker["unhandled"]["reason"], ("permission", "scope"))
        self.assertTrue(worker["unhandled"]["explanation"] and worker["options"])
        self.assertEqual([], record["rounds"][0]["audit"]["changed"])


if __name__ == "__main__":
    unittest.main()
