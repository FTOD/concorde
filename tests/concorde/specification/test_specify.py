"""The specify Operation end to end, with the fake ``claude`` of the worker tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from concorde.harness.runs import read_record
from concorde.spec.verification import verifies
from concorde.specification.operation import SPEC_CHANGE_SCHEMA, WORKER_OUTPUT_SCHEMA
from tests.concorde.support.operation_project import (
    OperationProject,
    commit,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT

CLAIMS = {
    "summary": "Stated a second answer.",
    "promise_changes": [
        {
            "module": "module.a",
            "kind": "explanation",
            "id": None,
            "change": "added",
            "description": "A also answers a second question",
        }
    ],
    "proposed_documents": [],
}


def break_meaning(text: str, realization: str) -> str:
    """Metadata text whose realization's meaning names an anchor the reading does not have."""
    return text.replace(f'"#{realization}"', f'"#missing-{realization}"')


class SpecifyTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        root = self.project.root
        # Bind the fixture's remaining files, so that the baseline validates cleanly.
        metadata = root / "specs/b/module.md.json"
        value = json.loads(metadata.read_text())
        value["defines"][0]["entries"] += ["checks/", ".gitignore"]
        metadata.write_text(json.dumps(value, indent=2) + "\n")
        commit(root, "bind every file")

    def open(self):
        self.project.open_task()
        self.worktree = self.project.worktree()
        return self.worktree

    def specify(self, rounds, *extra):
        return self.project.run(
            "specify",
            "--task",
            "t1",
            "--intent",
            OperationProject.plan(rounds),
            *extra,
        )

    def entry(self, suffix="") -> str:
        return (self.worktree / "specs/a/module.md").read_text() + suffix

    def kinds(self, envelope) -> set[str]:
        return {item["kind"] for item in envelope["host_evidence"]}

    @verifies("scenario.specification.change")
    def test_a_spec_change_is_made_and_validated(self):
        worktree = self.open()
        text = self.entry("\nA also answers a second question.\n")
        status, envelope = self.specify(
            [
                {
                    "writes": {str(worktree / "specs/a/module.md"): text},
                    "result": {"output": CLAIMS},
                }
            ]
        )
        self.assertEqual(0, status, envelope)
        output = envelope["output"]
        self.assertEqual(["specs/a/module.md"], output["changed_documents"])
        self.assertIn("module.a", output["affected_modules"])
        self.assertEqual([], output["validation"]["new_errors"])
        self.assertEqual([], output["validation"]["pre_existing_errors"])
        self.assertEqual(CLAIMS["promise_changes"], output["promise_changes"])
        self.assertEqual("Stated a second answer.", output["summary"])
        self.assertIn("FAKE-PLAN", output["intent"])
        self.assertTrue({"baseline", "registry", "validation"} <= self.kinds(envelope))
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        self.assertEqual("specify", record["task_type"])
        self.assertEqual(1, len(record["rounds"]))
        self.assertIsNone(record["rounds"][0].get("checks"))

    @verifies("scenario.specification.change")
    def test_the_registry_mirror_follows_an_edited_module_block(self):
        worktree = self.open()
        metadata = json.loads((worktree / "specs/a/module.md.json").read_text())
        metadata["module"]["title"] = "A2"
        status, envelope = self.specify(
            [
                {
                    "writes": {
                        str(worktree / "specs/a/module.md.json"): json.dumps(
                            metadata, indent=2
                        )
                        + "\n",
                        str(worktree / "specs/a/module.md"): self.entry().replace(
                            "# A\n", "# A2\n", 1
                        ),
                    },
                    "result": {"output": CLAIMS},
                }
            ]
        )
        registry = json.loads((worktree / ".concorde/specs.json").read_text())
        titles = {record["id"]: record["title"] for record in registry["modules"]}
        self.assertEqual("A2", titles["module.a"])
        self.assertEqual(0, status, envelope)
        self.assertEqual([], envelope["output"]["validation"]["new_errors"])

    @verifies("scenario.specification.declare-pending")
    def test_a_new_file_is_declared_not_created(self):
        worktree = self.open()
        metadata = json.loads((worktree / "specs/a/module.md.json").read_text())
        realization = metadata["defines"][1]
        realization["entries"].append("src/second.py")
        realization["pending"].append("src/second.py")
        status, envelope = self.specify(
            [
                {
                    "writes": {
                        str(worktree / "specs/a/module.md.json"): json.dumps(
                            metadata, indent=2
                        )
                        + "\n"
                    },
                    "result": {"output": CLAIMS},
                }
            ]
        )
        self.assertEqual(0, status, envelope)
        self.assertEqual(
            [
                {
                    "module": "module.a",
                    "realization": "realization.a.new",
                    "path": "src/second.py",
                }
            ],
            envelope["output"]["pending_declared"],
        )
        self.assertEqual(
            ["specs/a/module.md.json"], envelope["output"]["changed_documents"]
        )
        self.assertFalse((worktree / "src/second.py").exists())

    @verifies("scenario.specification.repair-broken")
    def test_a_run_repairs_specs_that_were_already_invalid(self):
        metadata = self.project.root / "specs/a/module.md.json"
        text = break_meaning(metadata.read_text(), "realization.a.code")
        metadata.write_text(break_meaning(text, "realization.a.new"))
        commit(self.project.root, "break A")
        worktree = self.open()
        repaired = (
            (worktree / "specs/a/module.md.json")
            .read_text()
            .replace('"#missing-realization.a.new"', '"#realization.a.new"')
        )
        status, envelope = self.specify(
            [
                {
                    "writes": {str(worktree / "specs/a/module.md.json"): repaired},
                    "result": {"output": CLAIMS},
                }
            ]
        )
        self.assertEqual(0, status, envelope)
        validation = envelope["output"]["validation"]
        self.assertEqual([], validation["new_errors"])
        remaining = validation["pre_existing_errors"]
        self.assertEqual(1, len(remaining), remaining)
        self.assertIn("realization.a.code", remaining[0]["message"])

    @verifies("scenario.specification.new-error")
    def test_a_change_that_breaks_the_specs_stops_the_run(self):
        worktree = self.open()
        path = worktree / "specs/a/module.md.json"
        broken = break_meaning(path.read_text(), "realization.a.new")
        status, envelope = self.specify(
            [
                {
                    "writes": {str(path): broken},
                    "result": {"output": CLAIMS},
                },
                {"result": {"output": CLAIMS}},
            ]
        )
        self.assertEqual(1, status)
        self.assertEqual("blocked", envelope["status"])
        error = envelope["error"]
        self.assertEqual(
            ("operation", "new_structural_errors"), (error["level"], error["code"])
        )
        self.assertIn("CHK.node.meaning", error["causes"][0]["detail"])
        new = envelope["output"]["validation"]["new_errors"]
        self.assertTrue(new)
        self.assertIn("new-error", self.kinds(envelope))
        self.assertEqual(broken, path.read_text())
        self.assertEqual("CHK.node.meaning", new[0]["rule_id"])
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        self.assertEqual(1, len(record["rounds"]))
        self.assertEqual(1, len(envelope["worker_runs"]))

    @verifies("scenario.specification.foreign-document")
    def test_a_needed_document_of_another_module_escalates(self):
        worktree = self.open()
        status, envelope = self.specify(
            [
                {
                    "writes": {
                        str(worktree / "specs/a/module.md"): self.entry(
                            "\nA needs B to answer too.\n"
                        )
                    },
                    "result": {
                        "status": "blocked",
                        "summary": "needs module.b",
                        "error": worker_error(
                            "the intent changes specs/b/module.md of module.b",
                            code="foreign_document",
                            reason="permission",
                            attempts=["edited A's part"],
                            options=["bind module.b as well"],
                        ),
                        "output": {**CLAIMS, "summary": "Edited A only."},
                    },
                }
            ]
        )
        self.assertEqual(1, status)
        self.assertEqual("blocked", envelope["status"])
        worker = link_at(envelope["error"], "worker")
        self.assertIn("module.b", worker["detail"])
        self.assertEqual("permission", worker["unhandled"]["reason"])
        self.assertEqual(["bind module.b as well"], worker["options"])
        # The state the worker left behind is still observed and validated.
        self.assertEqual(["specs/a/module.md"], envelope["output"]["changed_documents"])
        self.assertIn("validation", self.kinds(envelope))

    @verifies("scenario.specification.code-write")
    def test_a_write_to_code_fails_the_run(self):
        worktree = self.open()
        status, envelope = self.specify(
            [
                {
                    "writes": {str(worktree / "src/a/calc.py"): "BROKEN = 1\n"},
                    "result": {"output": CLAIMS},
                }
            ]
        )
        self.assertEqual(1, status)
        self.assertEqual("failed", envelope["status"])
        error = envelope["error"]
        self.assertEqual("audit_violation", error["code"])
        self.assertEqual("permission", error["unhandled"]["reason"])
        self.assertIn("src/a/calc.py", error["detail"])
        self.assertFalse({"validation", "registry"} & self.kinds(envelope))
        self.assertIsNone(envelope["output"])

    def test_admitted_inputs_reach_the_brief(self):
        self.open()
        assessment = {
            "goal": "g",
            "modules": [{"module": "module.a", "promises": "A answers one question."}],
            "sufficient": True,
            "gaps": [],
            "plan": None,
        }
        status, first = self.project.run(
            "understand",
            "--task",
            "t1",
            "--goal",
            OperationProject.plan([{"result": {"output": assessment}}]),
        )
        self.assertEqual(0, status, first)
        status, envelope = self.specify(
            [{"result": {"output": CLAIMS}}], "--input", first["run_id"]
        )
        self.assertEqual(0, status, envelope)
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        brief = (Path(record["run_directory"]) / "control/brief.md").read_text()
        self.assertIn(first["run_id"], brief)
        self.assertIn("A answers one question.", brief)
        self.assertIn("The task's own goal: Fix A.", brief)

    def test_proposed_deletions_of_owned_documents_are_reported(self):
        worktree = self.open()
        status, envelope = self.specify(
            [
                {
                    "result": {
                        "output": CLAIMS,
                        "proposed_deletions": [
                            str(worktree / "specs/b/module.md"),
                        ],
                    }
                }
            ]
        )
        self.assertEqual(0, status, envelope)
        self.assertEqual([], envelope["output"]["deleted_documents"])
        self.assertIn("deletion-refused", self.kinds(envelope))
        self.assertTrue((worktree / "specs/b/module.md").exists())


class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_spec_change_contract(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/operations/specification/contracts.md"
        ).read_text()
        fence = re.search(r"```concorde-contract\n(.*?)\n```", text, re.S).group(1)
        schema = json.loads(fence)["schema"]
        self.assertEqual(schema, SPEC_CHANGE_SCHEMA)
        for name in ("summary", "promise_changes", "proposed_documents"):
            self.assertEqual(
                schema["properties"][name], WORKER_OUTPUT_SCHEMA["properties"][name]
            )


if __name__ == "__main__":
    unittest.main()
