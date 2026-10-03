"""The specify Operation end to end, with the fake ``claude`` of the worker tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from concorde.worker_harness.runs import read_record
from concorde.spec.verification import verifies
from concorde.method.specification.operation import (
    SPEC_CHANGE_SCHEMA,
    WORKER_OUTPUT_SCHEMA,
)
from tests.concorde.support.operation_project import (
    OperationProject,
    commit,
    link_at,
    worker_error,
)
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import GLOSSARY, read_glossary, upsert_concepts

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
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
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

    @verifies("scenario.specification.missing-entry")
    def test_binding_a_file_that_does_not_exist_is_a_new_error(self):
        # A new file is created and bound by the task level; specify only binds what exists.
        worktree = self.open()
        path = worktree / "specs/a/module.md.json"
        metadata = json.loads(path.read_text())
        metadata["defines"][1]["entries"].append("src/second.py")
        bound = json.dumps(metadata, indent=2) + "\n"
        status, envelope = self.specify(
            [
                {"writes": {str(path): bound}, "result": {"output": CLAIMS}},
                {"result": {"output": CLAIMS}},
            ]
        )
        self.assertEqual((1, "blocked"), (status, envelope["status"]), envelope)
        self.assertEqual("new_structural_errors", envelope["error"]["code"])
        new = envelope["output"]["validation"]["new_errors"]
        self.assertEqual(["CHK.binds.exists"], [item["rule_id"] for item in new])
        self.assertIn("src/second.py", new[0]["message"])
        self.assertNotIn("pending_declared", envelope["output"])
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
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
        # Two resume rounds with the host's validation, which the worker did not use.
        self.assertEqual(3, len(record["rounds"]))
        self.assertIn("CHK.node.meaning", record["rounds"][0]["validation"])
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

    def needs(self, path: str, module: str = "module.a") -> dict:
        """A first round that ends blocked because it needs a new document at ``path``."""
        return {
            "result": {
                "status": "blocked",
                "summary": "needs a new document",
                "error": worker_error(
                    f"the intent's obligations belong in a new document {path}",
                    code="needs_new_document",
                    reason="permission",
                    options=["create the document"],
                ),
                "output": {
                    **CLAIMS,
                    "proposed_documents": [
                        {
                            "module": module,
                            "path": path,
                            "role": "implementation",
                            "reason": "the precise obligations need an implementation document",
                        }
                    ],
                },
            }
        }

    @verifies("scenario.specification.new-document")
    def test_a_needed_document_is_created_and_the_worker_fills_it(self):
        worktree = self.open()
        filled = "# Rules\n\nThe precise rules of [A](module.md).\n"
        status, envelope = self.specify(
            {
                "first": [self.needs("specs/a/rules.md")],
                "relaunch": [
                    {
                        "writes": {str(worktree / "specs/a/rules.md"): filled},
                        "result": {"output": CLAIMS},
                    }
                ],
            }
        )
        self.assertEqual(0, status, envelope)
        output = envelope["output"]
        self.assertEqual(["specs/a/rules.md"], output["created_documents"])
        self.assertIn("specs/a/rules.md", output["changed_documents"])
        self.assertEqual([], output["validation"]["new_errors"])
        self.assertEqual(filled, (worktree / "specs/a/rules.md").read_text())
        metadata = json.loads((worktree / "specs/a/rules.md.json").read_text())
        self.assertEqual(
            {"id": "document.a.rules", "owner": "module.a", "role": "implementation"},
            metadata["document"],
        )
        owns = json.loads((worktree / "specs/a/module.md.json").read_text())["module"][
            "owns"
        ]
        self.assertIn("specs/a/rules.md", owns)
        registry = json.loads((worktree / ".concorde/specs.json").read_text())
        [record] = [m for m in registry["modules"] if m["id"] == "module.a"]
        self.assertIn("specs/a/rules.md", record["owns"])
        self.assertEqual(2, len(envelope["worker_runs"]))
        self.assertIn("document-created", self.kinds(envelope))
        second = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][1]
        )
        brief = (Path(second["run_directory"]) / "brief.md").read_text()
        self.assertIn("Documents the host created for you", brief)

    @verifies("scenario.specification.document-refused")
    def test_a_document_outside_the_bound_modules_is_not_created(self):
        worktree = self.open()
        for path, module in (
            ("specs/b/rules.md", "module.b"),
            ("docs/rules.md", "module.a"),
        ):
            with self.subTest(path=path):
                status, envelope = self.specify(
                    {
                        "first": [self.needs(path, module)],
                        "relaunch": [{"result": {"output": CLAIMS}}],
                    }
                )
                self.assertEqual(1, status)
                self.assertEqual("blocked", envelope["status"])
                self.assertEqual([], envelope["output"]["created_documents"])
                self.assertIn("document-refused", self.kinds(envelope))
                self.assertFalse((worktree / path).exists())
                self.assertEqual(1, len(envelope["worker_runs"]))

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
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
        brief = (Path(record["run_directory"]) / "brief.md").read_text()
        self.assertIn(first["run_id"], brief)
        self.assertIn("A answers one question.", brief)
        self.assertIn("The workspace's goal: Fix A.", brief)
        self.assertNotIn("task's own goal", brief)

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


class GlossaryAfterRunTests(unittest.TestCase):
    """Method audits the glossary by entry once more after the worker run, whatever its status,
    since the round validation sees only clean rounds and runs before proposed deletions."""

    def setUp(self):
        self.project = OperationProject(self)
        root = self.project.root
        for module in ("a", "b"):
            upsert_concepts(
                root,
                f"specs/{module}/module.md",
                [
                    {
                        "id": f"concept.{module}.answer",
                        "title": f"{module.upper()} answer",
                        "owner": f"module.{module}",
                        "definition": f"What {module.upper()} returns for one question.",
                        "anchor": f"realization.{module}.code",
                    }
                ],
            )
        commit(root, "terms")
        self.project.open_task()
        self.worktree = self.project.worktree()

    def foreign_edit(self) -> str:
        value = read_glossary(self.worktree)
        for entry in value["concepts"]:
            if entry["id"] == "concept.b.answer":
                entry["definition"] = "What B returns."
        return json.dumps(value, indent=2) + "\n"

    def assert_violation(self, envelope):
        self.assertEqual("failed", envelope["status"])
        error = envelope["error"]
        self.assertEqual(
            ("audit_violation", "permission"),
            (error["code"], error["unhandled"]["reason"]),
        )
        self.assertIn(f"{GLOSSARY}#concept.b.answer", error["detail"])
        self.assertIn(
            "glossary-ownership", {e["kind"] for e in envelope["host_evidence"]}
        )
        record = read_record(
            self.project.root / ".concorde", envelope["worker_runs"][-1]
        )
        self.assertEqual(1, len(record["rounds"]))
        return error

    @verifies("scenario.method.glossary-after-run")
    def test_a_blocked_worker_that_changed_a_foreign_entry_fails(self):
        status, envelope = self.project.run(
            "specify",
            "--task",
            "t1",
            "--intent",
            OperationProject.plan(
                [
                    {
                        "writes": {str(self.worktree / GLOSSARY): self.foreign_edit()},
                        "result": {
                            "status": "blocked",
                            "summary": "needs module.b",
                            "error": worker_error(
                                "the intent changes module.b's term",
                                code="foreign_term",
                                reason="permission",
                            ),
                            "output": CLAIMS,
                        },
                    }
                ]
            ),
        )
        self.assertEqual(1, status)
        error = self.assert_violation(envelope)
        self.assertIn("module.b's term", link_at(error, "worker")["detail"])
        self.assertEqual("needs module.b", envelope["worker"]["summary"])

    @verifies("scenario.method.glossary-deletion-proposed")
    def test_a_proposed_deletion_of_the_glossary_fails(self):
        status, envelope = self.project.run(
            "specify",
            "--task",
            "t1",
            "--intent",
            OperationProject.plan(
                [
                    {
                        "result": {
                            "output": CLAIMS,
                            "proposed_deletions": [str(self.worktree / GLOSSARY)],
                        }
                    }
                ]
            ),
        )
        self.assertEqual(1, status)
        self.assert_violation(envelope)


class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_spec_change_contract(self):
        text = (
            REPOSITORY_ROOT / "specs/concorde/method/specification/contracts.md"
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
