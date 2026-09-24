"""End-to-end flows of the Framework through the ``concorde`` command and the installer.

Workers are the fake ``claude`` of the worker tests, so these flows exercise every host step,
record and Git effect deterministically; what Claude Code itself enforces is covered by the live
worker test.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from concorde.distribution.install import install
from concorde.spec.verification import verifies
from tests.concorde.distribution.test_distribution import package_copy
from tests.concorde.support.operation_project import OperationProject
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.validation.project import ValidationProject, evidence_of, git

COMMAND = [sys.executable, str(REPOSITORY_ROOT / "scripts/concorde.py")]


def implement_plan(writes: dict) -> str:
    """A fake implement worker that writes ``writes`` and addresses one scenario."""
    return OperationProject.plan(
        [{"writes": writes, "result": {"output": {"addresses": ["scenario.a.answer"]}}}]
    )


def fixed(worktree: Path, content: str = "def add(a, b):\n    return a + b\n") -> str:
    return implement_plan({f"{worktree}/src/a/calc.py": content})


class AdoptionTests(unittest.TestCase):
    @verifies("scenario.concorde.adopt-initialize")
    def test_install_and_initialize_a_new_project(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        git(project, "init", "-q")
        (project / "app.py").write_text("print('app')\n")
        install(project, package)
        concorde = str(project / ".concorde/bin/concorde")
        proposed = subprocess.run(
            [concorde, "init", "--propose", "--name", "App"],
            cwd=project,
            capture_output=True,
            text=True,
        )
        proposal = package.parent / "proposal.json"
        proposal.write_text(json.dumps(json.loads(proposed.stdout)["result"]))
        applied = subprocess.run(
            [concorde, "init", "--apply", "--proposal", str(proposal)],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, applied.returncode, applied.stdout)
        config = json.loads((project / ".concorde/config.json").read_text())
        manifest = (project / ".concorde/protocol/manifest.json").read_bytes()
        import hashlib

        self.assertEqual(
            "sha256:" + hashlib.sha256(manifest).hexdigest(),
            config["protocol"]["digest"],
        )
        valid = subprocess.run(
            [concorde, "validate"], cwd=project, capture_output=True, text=True
        )
        self.assertEqual("success", json.loads(valid.stdout)["status"], valid.stdout)
        entry = (project / "specs/project/module.md").read_text()
        self.assertIn("not specified yet", entry)


class TaskFlowTests(unittest.TestCase):
    def setUp(self):
        self.project = ValidationProject(self)
        self.root = self.project.root

    @verifies("scenario.concorde.task-to-merge")
    def test_a_task_from_opening_to_merge(self):
        def project_status():
            # Task records under .concorde/ are the host's; every other path is the project's.
            return [
                line
                for line in git(self.root, "status", "--porcelain").splitlines()
                if not line[3:].startswith(".concorde/")
            ]

        primary_before = project_status()
        worktree = self.project.task("t1")
        status, implemented = self.project.run(
            "implement", "--task", "t1", "--goal", fixed(worktree)
        )
        self.assertEqual((0, "ok"), (status, implemented["status"]), implemented)
        status, validated = self.project.validate()
        self.assertEqual((0, "ok"), (status, validated["status"]), validated)
        status, delivered = self.project.deliver()
        self.assertEqual((0, "ok"), (status, delivered["status"]), delivered)
        head = git(self.root, "rev-parse", "concorde/t1")
        self.assertIn(
            "Concorde-Task: t1", git(self.root, "log", "-1", "--format=%B", head)
        )
        changed = git(
            self.root, "diff", "--name-only", f"{self.project.base_commit}..{head}"
        )
        self.assertIn("src/a/calc.py", changed.splitlines())
        self.assertTrue(
            any(
                line.startswith(".concorde/evidence/t1/")
                for line in changed.splitlines()
            )
        )
        self.assertEqual(primary_before, project_status())
        git(self.root, "merge", "--ff-only", "concorde/t1")
        closed = subprocess.run(
            [*COMMAND, "task", "close", "t1", "--merged"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, closed.returncode, closed.stdout)
        self.assertIn("a + b", (self.root / "src/a/calc.py").read_text())

    @verifies("scenario.concorde.worker-escalates")
    def test_a_worker_that_needs_more_than_its_grant(self):
        worktree = self.project.task("t1")
        plan = implement_plan({f"{worktree}/src/bmod/secret.py": "SECRET = 2\n"})
        status, envelope = self.project.run("implement", "--task", "t1", "--goal", plan)
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual(
            ("operation", "audit_violation"), (error["level"], error["code"])
        )
        self.assertEqual("permission", error["unhandled"]["reason"])
        self.assertIn("src/bmod/secret.py", error["detail"])
        self.assertEqual("harness", error["causes"][0]["level"])
        self.assertTrue(evidence_of(envelope, "audit"))
        self.assertEqual(1, len(envelope["worker_runs"]))
        self.assertIn("1 round(s)", json.dumps(envelope["host_evidence"]))

    @verifies("scenario.concorde.error-chain-to-developer")
    def test_an_error_reaches_the_developer_as_one_chain(self):
        worktree = self.project.task("t1")
        worker = {
            "code": "spec_gap",
            "detail": "specs/a/module.md does not say whether add rounds its result",
            "evidence": [
                {"kind": "spec", "ref": f"{worktree}/specs/a/module.md", "detail": ""}
            ],
            "attempts": ["read every document of module.a"],
            "unhandled": {
                "reason": "decision",
                "explanation": "what module.a promises is the Spec's to state",
            },
            "options": ["specify rounding in module.a"],
            "recommendation": "specify rounding in module.a",
        }
        plan = OperationProject.plan(
            [
                {
                    "result": {
                        "status": "blocked",
                        "error": worker,
                        "output": {"addresses": []},
                    }
                }
            ]
        )
        status, envelope = self.project.run("implement", "--task", "t1", "--goal", plan)
        self.assertEqual((1, "blocked"), (status, envelope["status"]))
        escalated = subprocess.run(
            [
                *COMMAND,
                "task",
                "escalate",
                "t1",
                "--run",
                envelope["run_id"],
                "--code",
                "spec_decision",
                "--detail",
                "module.a must say whether add rounds before it can be implemented",
                "--reason",
                "decision",
                "--explanation",
                "changing what module.a promises is the developer's decision",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, escalated.returncode, escalated.stdout)
        value = json.loads(escalated.stdout)
        chain, levels = value["escalated"], []
        link = chain
        while True:
            levels.append(link["level"])
            self.assertTrue(link["detail"] and link["unhandled"]["explanation"])
            if not link["causes"]:
                break
            [link] = link["causes"]
        self.assertEqual(["main-agent", "operation", "harness", "worker"], levels)
        self.assertEqual(
            {key: link[key] for key in worker if key != "evidence"},
            {key: worker[key] for key in worker if key != "evidence"},
        )
        self.assertEqual(worker["evidence"], link["evidence"])
        record = json.loads((self.root / ".concorde/tasks/t1.json").read_text())
        self.assertEqual(chain, record["escalations"][-1]["error"])
        log = (self.root / ".concorde/tasks/t1.decisions.md").read_text()
        self.assertIn("does not say whether add rounds", log)
        self.assertIn("does not say whether add rounds", value["rendered"])

    @verifies("scenario.concorde.parallel-tasks")
    def test_two_tasks_in_parallel(self):
        first = self.project.task("t1", ("module.a",))
        second = self.project.task("t2", ("module.b",))
        environment = {
            **os.environ,
            "CONCORDE_CLAUDE": str(self.project.fake),
            "HOME": str(self.project.home),
        }
        runs = [
            subprocess.Popen(
                [*COMMAND, "run", "implement", "--task", task, "--goal", goal],
                cwd=self.root,
                env=environment,
                stdout=subprocess.PIPE,
                text=True,
            )
            for task, goal in (
                ("t1", fixed(first)),
                (
                    "t2",
                    implement_plan({f"{second}/src/bmod/secret.py": "SECRET = 3\n"}),
                ),
            )
        ]
        results = [json.loads(run.communicate()[0]) for run in runs]
        self.assertEqual(["ok", "ok"], [item["status"] for item in results], results)
        grants = [
            item["ref"]
            for result in results
            for item in evidence_of(result, "context-identity")
        ]
        self.assertEqual(2, len(grants))
        self.assertEqual("SECRET = 1\n", (first / "src/bmod/secret.py").read_text())
        self.assertIn("return a - b", (second / "src/a/calc.py").read_text())
        for task in ("t1", "t2"):
            self.assertEqual("ok", self.project.validate(task)[1]["status"])
            self.assertEqual("ok", self.project.deliver(task)[1]["status"])
        git(self.root, "merge", "--no-edit", "concorde/t1")
        git(self.root, "merge", "--no-edit", "concorde/t2")
        self.assertIn("a + b", (self.root / "src/a/calc.py").read_text())
        self.assertEqual("SECRET = 3\n", (self.root / "src/bmod/secret.py").read_text())


if __name__ == "__main__":
    unittest.main()
