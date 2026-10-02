"""The ``concorde scaffold`` execution command end to end on an existing codebase, after a survey
with the fake ``claude``."""

from __future__ import annotations

import json

from concorde.method.scaffold.command import SCAFFOLD_RECORD_SCHEMA
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.adoption_case import PROPOSAL, AdoptionCase, contract
from tests.concorde.support.brownfield_project import git


def sections(text: str) -> list[str]:
    """The titles of an entry's level-2 sections, in order."""
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


class ScaffoldTests(AdoptionCase):
    def test_the_schema_is_the_contract(self):
        self.assertEqual(
            contract(
                "specs/concorde/method/scaffold/contracts.md",
                "contract.scaffold.record",
            ),
            SCAFFOLD_RECORD_SCHEMA,
        )

    # --- scaffold --------------------------------------------------------------------------

    @verifies("scenario.scaffold.creates")
    def test_a_scaffold_creates_the_proposed_modules(self):
        worktree = self.open()
        _, survey = self.survey()
        config_before = (worktree / ".concorde/config.json").read_text()
        status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual(0, status, envelope)
        record = envelope["output"]
        self.assertEqual(
            ["module.checkout", "module.inventory"],
            [item["id"] for item in record["created"]],
        )
        checkout = worktree / "specs/project/checkout/module.md"
        text = checkout.read_text()
        self.assertIn("Checkout turns a basket into one order.", text)
        self.assertIn("not specified yet", text)
        self.assertIn('<a id="uses-inventory"></a>', text)
        self.assertEqual(
            ["Purpose", "Not yet specified", "Parts", "Collaborations"],
            sections(text),
        )
        self.assertTrue((worktree / "specs/project/inventory/module.md.json").is_file())
        root = json.loads((worktree / "specs/project/module.md.json").read_text())
        self.assertEqual(
            ["module.checkout", "module.inventory"],
            [item["target"] for item in root["module"]["contains"]],
        )
        entries = [
            e
            for r in root["defines"]
            if r["type"] == "realization"
            for e in r["entries"]
        ]
        self.assertIn("src/db.py", entries)
        self.assertFalse(
            any(
                e.startswith(("src/checkout", "src/inventory")) or e == "src/"
                for e in entries
            )
        )
        self.assertEqual(sorted(entries), sorted(record["parent_entries_after"]))
        parent = (worktree / "specs/project/module.md").read_text()
        self.assertEqual(["Purpose", "Not yet specified", "Parts"], sections(parent))
        parts = parent.split("## Parts\n", 1)[1]
        self.assertIn('<a id="contains-checkout"></a>', parts)
        self.assertIn("proposed by a survey of the code", parts)
        registry = json.loads((worktree / ".concorde/specs.json").read_text())
        self.assertEqual(
            {"module.shop", "module.checkout", "module.inventory"},
            {item["id"] for item in registry["modules"]},
        )
        self.assertEqual(
            config_before, (worktree / ".concorde/config.json").read_text()
        )
        report = validate_repository(worktree)
        self.assertEqual(
            [], [f.message for f in report.findings if f.strictness == "error"]
        )

    @verifies("scenario.scaffold.vendored-external")
    def test_vendored_code_becomes_external_material_of_its_user(self):
        worktree = self.open()
        vendored = json.loads(json.dumps(PROPOSAL))
        vendored["externals"] = [
            {
                "path": "src/db.py",
                "used_by": "module.checkout",
                "reason": "a copy of another project's connection helper",
            }
        ]
        status, survey = self.survey(vendored)
        self.assertEqual(0, status, survey)
        self.assertNotIn("src/db.py", survey["output"]["remaining_entries"])
        status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual(0, status, envelope)
        self.assertEqual(vendored["externals"], envelope["output"]["externals"])
        checkout = json.loads(
            (worktree / "specs/project/checkout/module.md.json").read_text()
        )
        self.assertEqual(
            [
                {
                    "kind": "external",
                    "target": "src/db.py",
                    "reason": "a copy of another project's connection helper",
                }
            ],
            checkout["module"]["includes"],
        )
        root = json.loads((worktree / "specs/project/module.md.json").read_text())
        entries = [
            e
            for r in root["defines"]
            if r["type"] == "realization"
            for e in r["entries"]
        ]
        self.assertNotIn("src/db.py", entries)
        report = validate_repository(worktree)
        self.assertEqual(
            [], [f.message for f in report.findings if f.strictness == "error"]
        )
        # Vendored code is never also a child's entry.
        overlapping = json.loads(json.dumps(PROPOSAL))
        overlapping["externals"] = [
            {"path": "src/checkout/", "used_by": "module.checkout", "reason": "r"}
        ]
        _, envelope = self.survey(overlapping)
        self.assertEqual("inconsistent_proposal", envelope["error"]["code"])
        self.assertIn("overlaps a child's entries", envelope["error"]["detail"])

    @verifies("scenario.scaffold.vendored-external")
    def test_vendored_code_inside_a_child_narrows_that_child(self):
        worktree = self.open()
        vendored = json.loads(json.dumps(PROPOSAL))
        vendored["externals"] = [
            {
                "path": "src/checkout/payment.py",
                "used_by": "module.checkout",
                "reason": "a copied payment client",
            }
        ]
        status, survey = self.survey(vendored)
        self.assertEqual(0, status, survey)
        status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual(0, status, envelope)
        checkout = json.loads(
            (worktree / "specs/project/checkout/module.md.json").read_text()
        )
        (code,) = [r for r in checkout["defines"] if r["type"] == "realization"]
        self.assertEqual(["src/checkout/api.py"], code["entries"])
        self.assertEqual(
            ["src/checkout/payment.py"],
            [item["target"] for item in checkout["module"]["includes"]],
        )
        report = validate_repository(worktree)
        self.assertEqual(
            [], [f.message for f in report.findings if f.strictness == "error"]
        )

    @verifies("scenario.scaffold.stale")
    def test_a_stale_proposal_writes_nothing(self):
        worktree = self.open()
        _, survey = self.survey()
        for path in (worktree / "src/checkout").iterdir():
            path.unlink()
        (worktree / "src/checkout").rmdir()
        before = git(worktree, "status", "--porcelain")
        _status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual("blocked", envelope["status"])
        self.assertEqual("stale_proposal", envelope["error"]["code"])
        self.assertIn("src/checkout/", envelope["error"]["detail"])
        self.assertEqual(before, git(worktree, "status", "--porcelain"))
        self.assertFalse((worktree / "specs/project/checkout").exists())

    @verifies("scenario.scaffold.target-exists")
    def test_an_existing_target_writes_nothing(self):
        worktree = self.open()
        _, survey = self.survey()
        existing = worktree / "specs/project/checkout/module.md"
        existing.parent.mkdir()
        existing.write_text("# Checkout\n")
        before = git(worktree, "status", "--porcelain", "--untracked-files=all")
        _status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual("blocked", envelope["status"])
        self.assertEqual("stale_proposal", envelope["error"]["code"])
        self.assertIn("specs/project/checkout/", envelope["error"]["detail"])
        self.assertEqual(
            before, git(worktree, "status", "--porcelain", "--untracked-files=all")
        )
        self.assertEqual("# Checkout\n", existing.read_text())
        self.assertFalse((worktree / "specs/project/inventory").exists())

    @verifies("scenario.scaffold.target-folder-exists")
    def test_an_existing_empty_child_folder_is_refused(self):
        worktree = self.open()
        _, survey = self.survey()
        folder = worktree / "specs/project/checkout"
        folder.mkdir()
        before = git(worktree, "status", "--porcelain", "--untracked-files=all")
        _status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual("blocked", envelope["status"])
        self.assertEqual("stale_proposal", envelope["error"]["code"])
        self.assertIn("specs/project/checkout/", envelope["error"]["detail"])
        self.assertEqual(
            before, git(worktree, "status", "--porcelain", "--untracked-files=all")
        )
        self.assertEqual([], list(folder.iterdir()))
        self.assertFalse((worktree / "specs/project/inventory").exists())

    @verifies("scenario.scaffold.invalid-not-kept")
    def test_a_scaffold_that_would_not_validate_keeps_nothing(self):
        worktree = self.open()
        broken = json.loads(json.dumps(PROPOSAL))
        broken["children"][0]["purpose"] = (
            "Checkout turns a basket into one order, as "
            "[the missing scenario](module.md#scenario.checkout.missing) says."
        )
        status, survey = self.survey(broken)
        self.assertEqual(0, status, survey)
        before = git(worktree, "status", "--porcelain", "--untracked-files=all")
        _status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual("failed", envelope["status"])
        error = envelope["error"]
        self.assertEqual("scaffold_invalid", error["code"])
        # One cause per new structural error: the dangling link in the child's entry and in
        # the paragraph that introduces the child in its parent's entry.
        self.assertEqual(
            [
                ("spec_finding", "specs/project/checkout/module.md"),
                ("spec_finding", "specs/project/module.md"),
            ],
            [
                (cause["code"], cause["evidence"][0]["ref"].split(":")[0])
                for cause in error["causes"]
            ],
        )
        self.assertTrue(
            all("CONCORDE-LINK-001" in cause["detail"] for cause in error["causes"])
        )
        self.assertEqual(
            before, git(worktree, "status", "--porcelain", "--untracked-files=all")
        )
        self.assertFalse((worktree / "specs/project/checkout").exists())
        self.assertFalse((worktree / "specs/project/inventory").exists())

    @verifies("scenario.scaffold.refused-input")
    def test_the_scaffold_needs_one_survey_of_its_task(self):
        worktree = self.open()
        _, survey = self.survey()
        _, second = self.survey()
        _, validate = self.project.run("task-validation", "--task", "adopt")
        self.assertEqual("ok", validate["status"], validate)
        for inputs in ([], [survey["run_id"], second["run_id"]], [validate["run_id"]]):
            with self.subTest(inputs=inputs):
                argv = [word for run in inputs for word in ("--input", run)]
                _, envelope = self.project.run("scaffold", "--task", "adopt", *argv)
                self.assertEqual("failed", envelope["status"])
                self.assertEqual("invalid_request", envelope["error"]["code"])
        self.assertFalse((worktree / "specs/project/checkout").exists())
        # A survey of another task is refused before the run begins.
        _, foreign = self.survey(task=False)
        _status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", foreign["run_id"]
        )
        self.assertEqual("failed", envelope["status"])
        self.assertIn(
            "input_not_admissible", [item["ref"] for item in envelope["host_evidence"]]
        )

    @verifies("scenario.scaffold.unbound")
    def test_the_scaffold_is_an_execution_command_of_a_bound_workspace(self):
        _, survey = self.survey(task=False)
        status, envelope = self.project.run("scaffold", "--input", survey["run_id"])
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual(("command", "scaffold"), (envelope["kind"], envelope["name"]))
        self.assertIsNone(envelope["workspace"])
        error = envelope["error"]
        self.assertEqual(("command", "refused"), (error["level"], error["code"]))
        self.assertIn("Command scaffold", error["actor"])
        self.assertEqual("binding_required", error["causes"][0]["code"])
        self.assertFalse((self.project.root / "specs/project/checkout").exists())
        self.open()
        _, survey = self.survey()
        status, envelope = self.project.run(
            "scaffold", "--task", "adopt", "--input", survey["run_id"]
        )
        self.assertEqual(0, status, envelope)
        self.assertEqual(
            ("command", "scaffold", "adopt", None, []),
            (
                envelope["kind"],
                envelope["name"],
                envelope["workspace"],
                envelope["worker"],
                envelope["worker_runs"],
            ),
        )
        # Its run's node lies in the task's workspace folder in the primary worktree, where a
        # later run may admit it.
        folder = (
            self.project.root
            / ".concorde/tasks/adopt/workspace/runs"
            / envelope["run_id"]
        )
        self.assertTrue((folder / "result.json").is_file())
        self.assertEqual(
            {"kind": "trace", "ref": envelope["run_id"], "detail": folder.as_posix()},
            envelope["host_evidence"][0],
        )
