"""The ``general`` Operation end to end, with a fake ``claude`` that plays both workers.

Each test writes the plans of the worker and the reviewer into a file the fake reads
(``fake_general.py``), so the instruction itself stays free text.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

from concorde.execution.operations.catalog import OPERATIONS
from concorde.method.general_work.operation import RESULT_SCHEMA
from concorde.method.workers import declared_workers
from concorde.spec.verification import verifies
from concorde.worker_harness.runs import read_record
from tests.concorde.support.operation_project import OperationProject, link_at
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE_GENERAL = Path(__file__).with_name("fake_general.py")
SPEC = "specs/a/module.md"


def finding(number, **values) -> dict:
    return {
        "id": f"F{number}",
        "severity": "blocking",
        "kind": "meaning",
        "locations": [f"{SPEC}: Purpose"],
        "description": "the rewrite drops a condition",
        "suggestion": "restore the condition",
        **values,
    }


class GeneralTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root
        self.plans = self.project.base / "general-plans.json"
        wrapper = self.project.base / "claude-general"
        wrapper.write_text(
            f"#!/bin/sh\nFAKE_GENERAL_PLANS='{self.plans}' "
            f'exec "{sys.executable}" "{FAKE_GENERAL}" "$@"\n'
        )
        wrapper.chmod(0o755)
        self.project.fake = wrapper

    def bound(self):
        self.project.open_task()
        self.worktree = self.project.worktree()

    def script(self, worker=None, reviewer=None):
        """The plans of both workers: ``worker`` and ``reviewer`` are one round each."""
        self.plans.write_text(
            json.dumps(
                {
                    "worker": [
                        worker
                        or {"result": {"summary": "done", "output": {"answer": "done"}}}
                    ],
                    "reviewer": [
                        reviewer
                        or {"result": {"summary": "fine", "output": {"findings": []}}}
                    ],
                }
            )
        )

    def run_general(self, *arguments, task=True):
        return self.project.run(
            "general", *(("--task", "t1") if task else ()), *arguments
        )

    def records(self, envelope) -> list[dict]:
        return [
            read_record(self.root / ".concorde", run) for run in envelope["worker_runs"]
        ]

    def brief(self, record) -> str:
        return (Path(record["run_directory"]) / "brief.md").read_text()

    @verifies("scenario.general-work.rewrite")
    def test_a_spec_rewrite_is_done_and_reviewed(self):
        self.bound()
        spec = self.worktree / SPEC
        earlier = spec.read_text()
        rewritten = earlier + "\nOne more sentence.\n"
        self.script(
            worker={
                "writes": {str(spec): rewritten},
                "result": {
                    "summary": "rewrote",
                    "output": {"answer": f"Rewrote {SPEC}."},
                },
            },
            reviewer={
                "result": {
                    "summary": "the meaning is kept",
                    "output": {
                        "findings": [finding(1, severity="advisory", kind="scope")]
                    },
                }
            },
        )
        status, envelope = self.run_general(
            "--type", "specify", "--instruction", "Restyle the module document."
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        result = envelope["output"]
        self.assertEqual(("specify", False), (result["type"], result["read_only"]))
        self.assertEqual(f"Rewrote {SPEC}.", result["answer"])
        change = result["change"]
        self.assertEqual([{"path": SPEC, "change": "modified"}], change["files"])
        self.assertEqual(earlier, (Path(change["before"]) / SPEC).read_text())
        self.assertIn("+One more sentence.", Path(change["diff"]).read_text())
        self.assertEqual(rewritten, spec.read_text())
        review = result["review"]
        self.assertEqual("the meaning is kept", review["summary"])
        self.assertEqual("accepted", review["verdict"])
        self.assertEqual(1, len(review["findings"]))
        worker, reviewer = self.records(envelope)
        self.assertEqual(("worker", "reviewer"), (worker["worker"], reviewer["worker"]))
        self.assertEqual(
            ("specify", "specify"), (worker["task_type"], reviewer["task_type"])
        )
        self.assertIn("Edit", worker["tools"])
        self.assertEqual("Read,Glob,Grep", reviewer["tools"])
        # The worker may change the Module's Spec and nothing else; the reviewer nothing.
        brief = self.brief(worker)
        writable = brief.split("You may change only these paths")[1].split(
            "You may read"
        )[0]
        self.assertIn(f"{self.worktree}/{SPEC}", writable)
        self.assertNotIn("src/a/", writable)
        review_brief = self.brief(reviewer)
        writable = review_brief.split("You may change only these paths")[1].split(
            "You may read"
        )[0]
        self.assertIn("(none)", writable)
        # The reviewer has the instruction, the change, the earlier content and the claim.
        self.assertIn("Restyle the module document.", review_brief)
        self.assertIn(f"- `{SPEC}`: modified", review_brief)
        self.assertIn("+One more sentence.", review_brief)
        self.assertIn(change["before"], review_brief)
        self.assertIn("This is the worker's claim", review_brief)
        self.assertIn(f"Rewrote {SPEC}.", review_brief)
        self.assertNotIn("## This review", brief)
        kinds = {item["kind"] for item in envelope["host_evidence"]}
        self.assertTrue({"instruction", "change", "verdict"} <= kinds, kinds)

    @verifies("scenario.general-work.instruction-file")
    def test_an_instruction_file_is_kept_as_it_was(self):
        self.bound()
        self.script()
        path = self.worktree / "restyle.md"
        path.write_text("# Restyle\n\nUse short sentences.\n")
        status, envelope = self.run_general(
            "--type", "understand", "--instruction-file", "restyle.md"
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        instruction = envelope["output"]["instruction"]
        data = path.read_bytes()
        self.assertEqual(path.as_posix(), instruction["file"])
        self.assertEqual(
            "sha256:" + hashlib.sha256(data).hexdigest(), instruction["digest"]
        )
        self.assertEqual("instruction.md", Path(instruction["copy"]).name)
        self.assertEqual(data, Path(instruction["copy"]).read_bytes())
        brief = self.brief(self.records(envelope)[0])
        self.assertLess(
            brief.index("You do one piece of work"), brief.index("Use short sentences.")
        )
        self.assertIn("The workspace's goal: Fix A.", brief)
        # The untracked instruction file was there before the worker: it is no change.
        self.assertEqual([], envelope["output"]["change"]["files"])

    @verifies("scenario.general-work.blocking-finding")
    def test_a_blocking_finding_requires_changes(self):
        self.bound()
        spec = self.worktree / SPEC
        self.script(
            worker={
                "writes": {str(spec): "# A\n\nChanged.\n"},
                "result": {"output": {"answer": "rewrote"}},
            },
            reviewer={"result": {"output": {"findings": [finding(1)]}}},
        )
        status, envelope = self.run_general(
            "--type", "specify", "--instruction", "Restyle; keep the meaning."
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual("changes_required", envelope["output"]["review"]["verdict"])
        self.assertEqual([finding(1)], envelope["output"]["review"]["findings"])
        self.assertEqual("# A\n\nChanged.\n", spec.read_text())

    @verifies("scenario.general-work.read-only-unbound")
    def test_a_read_only_run_works_unbound(self):
        self.script(
            worker={"result": {"output": {"answer": "add subtracts its arguments"}}}
        )
        status, envelope = self.run_general(
            "--modules",
            "module.a",
            "--type",
            "implement",
            "--read-only",
            "--instruction",
            "What does add do?",
            task=False,
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertIsNone(envelope["workspace"])
        result = envelope["output"]
        self.assertEqual(("implement", True), (result["type"], result["read_only"]))
        self.assertEqual("add subtracts its arguments", result["answer"])
        self.assertEqual([], result["change"]["files"])
        worker, _ = self.records(envelope)
        self.assertEqual("Read,Glob,Grep", worker["tools"])
        brief = self.brief(worker)
        readable = brief.split("You may read these paths")[1].split("You may know")[0]
        self.assertIn("/src/a/", readable)

    @verifies("scenario.general-work.unbound-write")
    def test_a_writing_run_needs_a_workspace(self):
        self.script()
        _, envelope = self.run_general(
            "--modules",
            "module.a",
            "--type",
            "specify",
            "--instruction",
            "Restyle.",
            task=False,
        )
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual("unbound_write", envelope["error"]["code"])
        self.assertEqual([], envelope["worker_runs"])

    @verifies("scenario.general-work.outside-grant")
    def test_a_write_outside_the_grant_fails_the_run(self):
        self.bound()
        self.script(
            worker={
                "writes": {str(self.worktree / "src/bmod/secret.py"): "SECRET = 2\n"},
                "result": {"output": {"answer": "changed B"}},
            }
        )
        _, envelope = self.run_general(
            "--type", "specify", "--instruction", "Change B."
        )
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual("audit_violation", envelope["error"]["code"])
        self.assertEqual(1, len(envelope["worker_runs"]))
        self.assertIsNone(envelope["output"])

    @verifies("scenario.general-work.worker-blocked")
    def test_a_blocked_worker_gets_no_review(self):
        self.bound()
        self.script(
            worker={"result": {"status": "blocked", "output": {"answer": "cannot"}}}
        )
        _, envelope = self.run_general(
            "--type", "specify", "--instruction", "Do the impossible."
        )
        self.assertEqual("blocked", envelope["status"], envelope)
        self.assertEqual(1, len(envelope["worker_runs"]))
        self.assertIsNotNone(link_at(envelope["error"], "worker"))

    @verifies("scenario.general-work.no-instruction")
    def test_an_empty_instruction_launches_nothing(self):
        self.bound()
        self.script()
        (self.worktree / "empty.md").write_text("\n")
        _, envelope = self.run_general(
            "--type", "specify", "--instruction-file", "empty.md"
        )
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual("instruction_unreadable", envelope["error"]["code"])
        self.assertEqual("input", envelope["error"]["unhandled"]["reason"])
        self.assertEqual([], envelope["worker_runs"])

    def test_a_missing_instruction_file_launches_nothing(self):
        self.bound()
        _, envelope = self.run_general(
            "--type", "understand", "--instruction-file", "missing.md"
        )
        self.assertEqual("instruction_unreadable", envelope["error"]["code"])
        self.assertEqual([], envelope["worker_runs"])

    def test_repeated_finding_ids_discard_the_review(self):
        self.bound()
        self.script(
            reviewer={"result": {"output": {"findings": [finding(1), finding(1)]}}}
        )
        _, envelope = self.run_general(
            "--type", "understand", "--instruction", "Explain A."
        )
        self.assertEqual("failed", envelope["status"], envelope)
        self.assertEqual("inconsistent_review", envelope["error"]["code"])
        self.assertIsNone(envelope["output"])

    def test_the_definition_and_its_workers(self):
        definition = OPERATIONS.get("general")
        self.assertEqual("module.general-work", OPERATIONS.module("general"))
        self.assertIsNone(definition.task_type)
        self.assertEqual("optional", definition.binding)
        self.assertEqual(("worker", "reviewer"), declared_workers()["general"])

    def test_the_output_schema_is_the_result_contract(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/method/general-work/contracts.md"
        ).read_text()
        block = text.split("```concorde-contract\n")[1].split("\n```")[0]
        contract = json.loads(block)
        self.assertEqual("contract.general-work.result", contract["id"])
        self.assertEqual(contract["schema"], RESULT_SCHEMA)


class WorkerConfigurationTests(unittest.TestCase):
    def test_the_checkout_runs_general_on_gpt_6_1_sol_medium(self):
        config = json.loads((REPOSITORY_ROOT / ".concorde/workers.json").read_text())
        self.assertEqual(
            {"model": "gpt-6.1-sol", "reasoning": "medium"},
            config["operations"]["general"]["default"],
        )


if __name__ == "__main__":
    unittest.main()
