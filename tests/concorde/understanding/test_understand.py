"""The understand Operation end to end, with the fake ``claude`` of the worker tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from concorde.worker_harness.runs import read_record
from concorde.spec.verification import verifies
from concorde.method.understanding.operation import ASSESSMENT_SCHEMA
from tests.concorde.support.operation_project import (
    OperationProject,
    commit,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

GOAL = "let A answer two questions"


def assessment(**changes) -> dict:
    value = {
        "goal": GOAL,
        "modules": [{"module": "module.a", "promises": "A answers one question."}],
        "sufficient": True,
        "gaps": [],
        "plan": None,
    }
    value.update(changes)
    return value


PLAN = {
    "summary": "Create and bind the new file, then implement it.",
    "modules": ["module.a"],
    "new_files": [
        {
            "module": "module.a",
            "path": "src/a/second.py",
            "reason": "the second answer",
        }
    ],
    "steps": [
        {"run": "specify", "modules": ["module.a"], "purpose": "state it"},
        {"run": "implement", "modules": ["module.a"], "purpose": "build it"},
    ],
    "decisions": ["whether the second answer is optional"],
}
GAP = {
    "module": "module.a",
    "document": "specs/a/module.md",
    "missing": "what the second question is",
    "needed_for": "the goal names a second answer",
    "suggestion": "add a scenario for the second question",
}


class UnderstandTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.project.open_task()
        self.worktree = self.project.worktree()

    def understand(self, rounds, *extra):
        return self.project.run(
            "understand",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan(rounds),
            *extra,
        )

    def fake_round(self, envelope) -> dict:
        """The tool set the worker was given and its first prompt, the brief its run directory
        keeps."""
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
        brief = (Path(record["run_directory"]) / "brief.md").read_text()
        return {"tools": record["tools"], "prompt": brief}

    @verifies("scenario.understanding.sufficient")
    def test_a_sufficient_spec_is_confirmed_without_a_plan(self):
        status, envelope = self.understand([{"result": {"output": assessment()}}])
        self.assertEqual(0, status, envelope)
        self.assertEqual("ok", envelope["status"])
        output = envelope["output"]
        self.assertTrue(output["sufficient"])
        self.assertEqual([], output["gaps"])
        self.assertIsNone(output["plan"])
        # The goal is the host's argument, repeated verbatim.
        self.assertIn("FAKE-PLAN", output["goal"])
        seen = self.fake_round(envelope)
        self.assertEqual("Read,Glob,Grep", seen["tools"])
        brief = seen["prompt"]
        readable = brief.split("You may read these paths")[1].split("You may know")[0]
        names = brief.split("You may know that these files exist")[1]
        writable = brief.split("You may change only these paths")[1].split(
            "You may read"
        )[0]
        self.assertIn(f"{self.worktree}/specs/a/module.md", readable)
        self.assertIn(f"{self.worktree}/src/a/", names)
        self.assertNotIn("src/a/", readable)
        self.assertIn("(none)", writable)
        self.assertIn("Plan requested: no", brief)
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
        self.assertEqual(1, len(record["rounds"]))
        self.assertIsNone(record["rounds"][0].get("checks"))

    @verifies("scenario.understanding.plan")
    def test_a_plan_is_returned_on_request(self):
        status, envelope = self.understand(
            [{"result": {"output": assessment(plan=PLAN)}}], "--plan"
        )
        self.assertEqual(0, status, envelope)
        plan = envelope["output"]["plan"]
        self.assertEqual(["module.a"], plan["modules"])
        self.assertEqual(PLAN["new_files"], plan["new_files"])
        self.assertNotIn("pending", plan)
        self.assertEqual(
            ["specify", "implement"], [step["run"] for step in plan["steps"]]
        )
        self.assertIn("Plan requested: yes", self.fake_round(envelope)["prompt"])

    @verifies("scenario.understanding.gap")
    def test_a_missing_promise_is_reported_as_a_gap(self):
        status, envelope = self.understand(
            [{"result": {"output": assessment(sufficient=False, gaps=[GAP])}}],
            "--plan",
        )
        self.assertEqual(0, status, envelope)
        output = envelope["output"]
        self.assertFalse(output["sufficient"])
        self.assertEqual(GAP, output["gaps"][0])
        self.assertIsNone(output["plan"])

    @verifies("scenario.understanding.unassessable")
    def test_a_goal_that_cannot_be_assessed_escalates(self):
        status, envelope = self.understand(
            [
                {
                    "result": {
                        "status": "blocked",
                        "summary": "cannot assess",
                        "error": worker_error(
                            "the goal concerns module.b, which is not bound",
                            code="unbound_module",
                            reason="scope",
                            attempts=["read the A Spec"],
                            options=["bind module.b"],
                        ),
                        "output": assessment(sufficient=False),
                    }
                }
            ]
        )
        self.assertEqual(1, status)
        self.assertEqual("blocked", envelope["status"])
        worker = link_at(envelope["error"], "worker")
        self.assertIn("module.b", worker["detail"])
        self.assertEqual("scope", worker["unhandled"]["reason"])
        self.assertEqual(["read the A Spec"], worker["attempts"])
        self.assertEqual(["bind module.b"], worker["options"])
        self.assertIn("bind module.b", envelope["error"]["options"])
        self.assertIsNone(envelope["output"])

    @verifies("scenario.understanding.unknown-module")
    def test_an_unknown_module_fails_the_run(self):
        bad = assessment(sufficient=False, gaps=[{**GAP, "module": "module.zzz"}])
        status, envelope = self.understand([{"result": {"output": bad}}])
        self.assertEqual(1, status)
        self.assertEqual("failed", envelope["status"])
        unknown = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "unknown-module"
        ]
        self.assertEqual(["module.zzz"], [item["ref"] for item in unknown])
        self.assertIsNone(envelope["output"])
        self.assertEqual(
            "module.zzz", envelope["worker"]["output"]["gaps"][0]["module"]
        )

    def test_a_module_named_only_by_a_new_file_must_exist(self):
        plan = {
            **PLAN,
            "new_files": [{**PLAN["new_files"][0], "module": "module.zzz"}],
        }
        status, envelope = self.understand(
            [{"result": {"output": assessment(plan=plan)}}], "--plan"
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]), envelope)
        unknown = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "unknown-module"
        ]
        self.assertEqual(["module.zzz"], [item["ref"] for item in unknown])
        self.assertIsNone(envelope["output"])

    @verifies("scenario.understanding.inconsistent")
    def test_an_inconsistent_assessment_fails_the_run(self):
        for rounds, extra in (
            ([{"result": {"output": assessment(plan=PLAN)}}], ()),
            ([{"result": {"output": assessment(sufficient=False, gaps=[])}}], ()),
            ([{"result": {"output": assessment(gaps=[GAP])}}], ()),
            ([{"result": {"output": assessment()}}], ("--plan",)),
        ):
            status, envelope = self.understand(rounds, *extra)
            self.assertEqual("failed", envelope["status"], rounds)
            self.assertTrue(
                any(
                    item["kind"] == "inconsistent-assessment"
                    for item in envelope["host_evidence"]
                )
            )
            self.assertEqual(1, len(envelope["worker_runs"]))

    def test_a_module_named_only_by_a_new_file_must_exist(self):
        plan = {
            **PLAN,
            "new_files": [{**PLAN["new_files"][0], "module": "module.zzz"}],
        }
        status, envelope = self.understand(
            [{"result": {"output": assessment(plan=plan)}}], "--plan"
        )
        self.assertEqual((1, "failed"), (status, envelope["status"]), envelope)
        unknown = [
            item
            for item in envelope["host_evidence"]
            if item["kind"] == "unknown-module"
        ]
        self.assertEqual(["module.zzz"], [item["ref"] for item in unknown])
        self.assertIsNone(envelope["output"])

    @verifies("scenario.understanding.inconsistent")
    def test_extra_or_duplicate_module_entries_fail_the_run(self):
        entry = {"module": "module.a", "promises": "A answers one question."}
        other = {"module": "module.b", "promises": "B exists."}
        for modules, expected in (
            ([entry, other], "module.b, which are not bound"),
            (
                [entry, entry],
                "more than one assessment entry for the Module(s) module.a",
            ),
        ):
            status, envelope = self.understand(
                [{"result": {"output": assessment(modules=modules)}}]
            )
            self.assertEqual(1, status, envelope)
            self.assertEqual("failed", envelope["status"])
            self.assertEqual("inconsistent_assessment", envelope["error"]["code"])
            problems = [
                item["detail"]
                for item in envelope["host_evidence"]
                if item["kind"] == "inconsistent-assessment"
            ]
            self.assertTrue(any(expected in problem for problem in problems), problems)
            self.assertIsNone(envelope["output"])

    @verifies("scenario.understanding.change-detected")
    def test_a_change_to_the_worktree_fails_the_run(self):
        target = self.worktree / "specs/a/module.md"
        status, envelope = self.understand(
            [
                {
                    "writes": {str(target): "# A\n\nChanged.\n"},
                    "result": {"output": assessment()},
                },
                {"result": {"output": assessment()}},
            ]
        )
        self.assertEqual(1, status)
        self.assertEqual("failed", envelope["status"])
        error = envelope["error"]
        self.assertEqual("audit_violation", error["code"])
        self.assertEqual("permission", error["unhandled"]["reason"])
        self.assertIn("specs/a/module.md", error["detail"])
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
        self.assertEqual(1, len(record["rounds"]))


class UnboundUnderstandTests(unittest.TestCase):
    @verifies("scenario.understanding.unbound-committed-specs")
    def test_an_unbound_run_reads_the_committed_specs_of_its_checkout(self):
        from tests.concorde.support.spec_project import update_module

        project = OperationProject(self)
        root = project.root
        # An uncommitted Spec edit of the primary worktree, which an unbound run never sees.
        (root / "specs/a/draft.md").write_text("# Draft\n\nNot committed.\n")
        metadata = json.loads((root / "specs/a/obligations.md.json").read_text())
        metadata["document"]["id"] = "document.a.draft"
        metadata["defines"] = []
        (root / "specs/a/draft.md.json").write_text(json.dumps(metadata, indent=2))
        owns = json.loads((root / "specs/a/module.md.json").read_text())["module"][
            "owns"
        ]
        update_module(root, "module.a", owns=[*owns, "specs/a/draft.md"])
        status, envelope = project.run(
            "understand",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{"result": {"output": assessment()}}]),
            cwd=root,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertIsNone(envelope["workspace"])
        record = read_record(root / ".concorde", envelope["worker_runs"][-1])
        brief = (Path(record["run_directory"]) / "brief.md").read_text()
        readable = brief.split("You may read these paths")[1].split("You may know")[0]
        self.assertIn("/specs/a/module.md", readable)
        self.assertNotIn("draft.md", brief)
        self.assertNotIn(f"{root}/specs/a/module.md", readable)


class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_assessment_contract(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/method/understanding/contracts.md"
        ).read_text()
        fence = re.search(r"```concorde-contract\n(.*?)\n```", text, re.S).group(1)
        self.assertEqual(json.loads(fence)["schema"], ASSESSMENT_SCHEMA)


if __name__ == "__main__":
    unittest.main()


class InterpreterLaunchTests(unittest.TestCase):
    """A worker launches through Method and Workers, its runtime paths holding the project
    interpreter's directories, wherever the environment lies."""

    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        # An installation outside the home and every worktree, reached through a version link.
        installations = self.project.base / "python"
        self.release = installations / "cpython-3.9.25"
        (self.release / "bin").mkdir(parents=True)
        python = self.release / "bin/python3.9"
        python.write_text("#!/bin/sh\n")
        python.chmod(0o755)
        (installations / "cpython-3.9").symlink_to(self.release)
        self.installations = installations
        config = self.root / ".concorde/config.json"
        values = json.loads(config.read_text())
        values["python"] = ".venv/bin/python"
        config.write_text(json.dumps(values, indent=2))
        with (self.root / ".gitignore").open("a") as ignore:
            ignore.write(".venv/\n")
        commit(self.root, "name the project interpreter")

    def environment(self, worktree: Path) -> Path:
        """A ``.venv`` of ``worktree`` whose interpreter links to the installation."""
        environment = worktree / ".venv"
        (environment / "bin").mkdir(parents=True)
        (environment / "bin/python").symlink_to(
            self.installations / "cpython-3.9/bin/python3.9"
        )
        return environment

    def readable(self, envelope) -> list[Path]:
        """The paths the worker's Bash sandbox may read, from its kept settings."""
        record = read_record(self.root / ".concorde", envelope["worker_runs"][-1])
        settings = json.loads(
            (self.project.runtime(record) / "control/settings.json").read_text()
        )
        return [Path(path) for path in settings["sandbox"]["filesystem"]["allowRead"]]

    def assert_no_worktree_readable(self, readable, worktree):
        for path in readable:
            for protected in (worktree, self.root):
                self.assertFalse(
                    path == protected or path in protected.parents,
                    f"{path} is or holds {protected}",
                )

    @verifies("scenario.method.interpreter-linked-checkout")
    def test_a_worker_launches_in_a_checkout_whose_environment_is_a_link(self):
        environment = self.environment(self.root)
        status, envelope = self.project.run(
            "understand",
            "--modules",
            "module.a",
            "--goal",
            OperationProject.plan([{"result": {"output": assessment()}}]),
            cwd=self.root,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertIsNone(envelope["workspace"])
        # The checkout linked the primary worktree's environment, which the worker reads at its
        # real location.
        self.assertIn(
            ("environment", ".venv"),
            [(item["kind"], item["ref"]) for item in envelope["host_evidence"]],
        )
        readable = self.readable(envelope)
        for directory in (
            environment,
            environment / "bin",
            self.installations,
            self.release,
        ):
            self.assertIn(directory, readable)
        worktrees = self.root / ".claude/worktrees"
        [checkout] = {
            worktrees / path.relative_to(worktrees).parts[0]
            for path in readable
            if worktrees in path.parents
        }
        self.assertTrue(checkout.name.startswith("unbound-"), checkout)
        self.assert_no_worktree_readable(readable, checkout)

    @verifies("scenario.method.interpreter-own-environment")
    def test_a_worker_launches_in_a_task_worktree_with_its_own_environment(self):
        self.project.open_task()
        worktree = self.project.worktree()
        environment = self.environment(worktree)
        status, envelope = self.project.run(
            "understand",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{"result": {"output": assessment()}}]),
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        readable = self.readable(envelope)
        for directory in (
            environment,
            environment / "bin",
            self.installations,
            self.release,
        ):
            self.assertIn(directory, readable)
        self.assert_no_worktree_readable(readable, worktree)
