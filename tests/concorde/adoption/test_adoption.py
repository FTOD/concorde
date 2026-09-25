"""The Adoption Operations end to end on an existing codebase, with the fake ``claude``."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from concorde.adoption.records import (
    ANSWERS_SCHEMA,
    DECOMPOSITION_SCHEMA,
    SCAFFOLD_RECORD_SCHEMA,
    SPEC_DESCRIPTION_SCHEMA,
)
from concorde.harness.runs import read_record
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.brownfield_project import BrownfieldProject, git
from tests.concorde.support.paths import REPOSITORY_ROOT

DB_HELPER = {
    "id": "d.db-helper",
    "module": "module.shop",
    "question": "Does the shared database helper get a Module of its own?",
    "options": ["a Module of its own", "stay with the root"],
    "chosen": "stay with the root",
    "reason": "it is two lines of connection setup",
    "decided_by": "worker",
}
PROPOSAL = {
    "summary": "Checkout and inventory are separate responsibilities.",
    "children": [
        {
            "id": "module.checkout",
            "title": "Checkout",
            "purpose": "Checkout turns a basket into one order.",
            "entries": ["src/checkout/"],
            "uses": [
                {
                    "target": "module.inventory",
                    "reason": "submit holds stock through inventory.stock.hold.",
                }
            ],
        },
        {
            "id": "module.inventory",
            "title": "Inventory",
            "purpose": "Inventory holds stock for baskets.",
            "entries": ["src/inventory/"],
            "uses": [],
        },
    ],
    "checks": [
        {
            "id": "check.checkout.tests",
            "module": "module.checkout",
            "argv": ["python", "-m", "pytest", "tests"],
            "timeout_seconds": 300,
            "inputs": ["src/checkout", "tests"],
            "reason": "pyproject.toml configures pytest",
        }
    ],
    "decisions": [DB_HELPER],
    "open_questions": [],
}
RETRY_QUESTION = {
    "id": "q.payment-retry",
    "module": "module.checkout",
    "subject": "retrying a declined payment",
    "observed": "a declined payment is retried once; other errors are not",
    "evidence": ["src/checkout/payment.py"],
    "why_uncertain": "nothing says whether only declines should be retried",
    "options": ["retry declines once", "retry every failure once"],
    "recommendation": "ask whether other failures should be retried",
}


def contract(path: str, identity: str) -> dict:
    text = (REPOSITORY_ROOT / path).read_text()
    for fence in re.findall(r"```concorde-contract\n(.*?)\n```", text, re.DOTALL):
        body = json.loads(fence)
        if body["id"] == identity:
            return body["schema"]
    raise AssertionError(f"{identity} not in {path}")


class AdoptionTests(unittest.TestCase):
    def setUp(self):
        self.project = BrownfieldProject(self)

    def open(self) -> Path:
        self.project.open_task()
        self.worktree = self.project.worktree()
        return self.worktree

    def survey(self, output=PROPOSAL, *extra, task=True, status="ok", error=None):
        result = {"output": output}
        if status != "ok":
            result.update(status=status, error=error)
        return self.project.run(
            "survey",
            *(("--task", "adopt") if task else ()),
            "--modules",
            "module.shop",
            "--goal",
            BrownfieldProject.plan([{"result": result}]),
            *extra,
        )

    def fake_round(self, envelope) -> dict:
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        work = Path(record["run_directory"]) / "work"
        return json.loads((work / "fake-round-1.json").read_text())

    def scaffolded(self) -> str:
        self.open()
        status, envelope = self.survey()
        self.assertEqual(0, status, envelope)
        status, scaffold = self.project.run(
            "scaffold", "--task", "adopt", "--input", envelope["run_id"]
        )
        self.assertEqual(0, status, scaffold)
        return envelope["run_id"]

    def describe(self, rounds, *extra, modules="module.checkout"):
        return self.project.run(
            "code_to_spec",
            "--task",
            "adopt",
            "--modules",
            modules,
            "--goal",
            BrownfieldProject.plan(rounds),
            *extra,
        )

    def test_the_schemas_are_the_contracts(self):
        path = "specs/concorde/operations/adoption/contracts.md"
        for identity, schema in (
            ("contract.adoption.decomposition", DECOMPOSITION_SCHEMA),
            ("contract.adoption.scaffold-record", SCAFFOLD_RECORD_SCHEMA),
            ("contract.adoption.spec-description", SPEC_DESCRIPTION_SCHEMA),
            ("contract.adoption.answers", ANSWERS_SCHEMA),
        ):
            with self.subTest(identity=identity):
                self.assertEqual(contract(path, identity), schema)

    # --- survey ----------------------------------------------------------------------------

    @verifies("scenario.adoption.survey-proposes")
    def test_a_survey_proposes_children(self):
        worktree = self.open()
        status, envelope = self.survey()
        self.assertEqual(0, status, envelope)
        output = envelope["output"]
        self.assertEqual(
            ["module.checkout", "module.inventory"],
            [child["id"] for child in output["children"]],
        )
        self.assertIn("src/db.py", output["remaining_entries"])
        self.assertIn("README.md", output["remaining_entries"])
        self.assertNotIn("src/", output["remaining_entries"])
        self.assertFalse(
            any(
                entry.startswith(("src/checkout", "src/inventory"))
                for entry in output["remaining_entries"]
            )
        )
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        self.assertEqual("code-to-spec", record["task_type"])
        frozen = json.loads(
            (Path(record["run_directory"]) / "control/grant.json").read_text()
        )
        levels = {entry["path"]: entry["level"] for entry in frozen["entries"]}
        self.assertNotIn("rw", levels.values())
        self.assertEqual("ro", levels["src/"])
        self.assertEqual("ro", levels["specs/project/module.md"])
        fake = self.fake_round(envelope)
        tools = fake["argv"][fake["argv"].index("--tools") + 1]
        self.assertEqual("Read,Glob,Grep", tools)
        self.assertIn("src/checkout/api.py", fake["prompt"])
        self.assertRegex(fake["prompt"], r"\d+\s+src/inventory/stock\.py")
        self.assertIn(
            "grant-withheld", {item["kind"] for item in envelope["host_evidence"]}
        )
        self.assertEqual("", git(worktree, "status", "--porcelain"))

    @verifies("scenario.adoption.survey-no-task")
    def test_a_survey_runs_without_a_task(self):
        status, envelope = self.survey(task=False)
        self.assertEqual(0, status, envelope)
        self.assertIsNone(envelope["task"])
        self.assertEqual(
            [], list((self.project.root / ".concorde/tasks").glob("*.json"))
        )

    @verifies("scenario.adoption.survey-inconsistent")
    def test_a_proposal_that_does_not_fit_fails(self):
        self.open()
        bad = json.loads(json.dumps(PROPOSAL))
        bad["children"][0]["entries"] = ["lib/"]
        bad["children"][1]["title"] = "Shop"
        status, envelope = self.survey(bad)
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual("inconsistent_proposal", error["code"])
        self.assertEqual("capability", error["unhandled"]["reason"])
        self.assertIn("lib/", error["detail"])
        self.assertIn("'Shop'", error["detail"])
        self.assertIsNone(envelope["output"])
        self.assertEqual(bad["children"], envelope["worker"]["output"]["children"])

    @verifies("scenario.adoption.survey-answers")
    def test_a_survey_follows_the_answers(self):
        self.open()
        _, first = self.survey()
        answer = {
            "id": "d.db-helper",
            "question": DB_HELPER["question"],
            "answer": "a Module of its own",
        }
        answers = self.project.answers(answer)
        followed = json.loads(json.dumps(PROPOSAL))
        followed["children"].append(
            {
                "id": "module.db",
                "title": "Database",
                "purpose": "It connects.",
                "entries": ["src/db.py"],
                "uses": [],
            }
        )
        followed["decisions"] = [
            {**DB_HELPER, "chosen": "a Module of its own", "decided_by": "developer"}
        ]
        status, envelope = self.survey(
            followed, "--answers", answers, "--input", first["run_id"]
        )
        self.assertEqual(0, status, envelope)
        self.assertIn(
            "module.db", [child["id"] for child in envelope["output"]["children"]]
        )
        self.assertIn(first["run_id"], self.fake_round(envelope)["prompt"])
        # An answer the proposal ignores fails the run.
        status, envelope = self.survey(PROPOSAL, "--answers", answers)
        self.assertEqual("failed", envelope["status"])
        self.assertEqual("inconsistent_proposal", envelope["error"]["code"])
        self.assertIn("d.db-helper", envelope["error"]["detail"])

    def test_an_answered_survey_question_must_be_settled(self):
        self.open()
        asking = json.loads(json.dumps(PROPOSAL))
        asking["open_questions"] = [
            {**RETRY_QUESTION, "id": "q.split", "module": "module.shop"}
        ]
        _, first = self.survey(asking)
        answers = self.project.answers(
            {"id": "q.split", "question": "split?", "answer": "keep them together"}
        )
        _, still = self.survey(asking, "--answers", answers, "--input", first["run_id"])
        self.assertEqual("failed", still["status"])
        self.assertIn("q.split", still["error"]["detail"])
        status, settled = self.survey(
            PROPOSAL, "--answers", answers, "--input", first["run_id"]
        )
        self.assertEqual(0, status, settled)

    def test_children_whose_documents_share_a_folder_are_refused(self):
        self.open()
        clash = json.loads(json.dumps(PROPOSAL))
        clash["children"][0]["id"] = "module.api.client"
        clash["children"][0]["uses"] = []
        clash["children"][1]["id"] = "module.db.client"
        _, envelope = self.survey(clash)
        self.assertEqual("inconsistent_proposal", envelope["error"]["code"])
        self.assertIn("client/", envelope["error"]["detail"])

    def test_narrowing_binds_only_what_the_directory_bound(self):
        from concorde.adoption.records import narrowed_entries

        root = self.project.base / "tree"
        for path in ("src/a/x.py", "src/b/y.py", "src/cache/__pycache__/z.pyc"):
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text("x\n")
        (root / "src/empty").mkdir()
        (root / "src/a/link.py").symlink_to(root / "src/b/y.py")
        self.assertEqual(
            {"src/": ["src/b/"]},
            narrowed_entries(root, ["src/"], ["src/a/x.py"]),
        )

    def test_files_a_child_directory_does_not_bind_stay_with_the_parent(self):
        from concorde.adoption.records import narrowed_entries

        root = self.project.base / "site"
        for path in ("docs/index.rst", "docs/.nojekyll", "docs/_themes/.gitignore"):
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text("x\n")
        # Initialization binds the dot files exactly, since the directory entry skips them.
        self.assertEqual(
            {
                "docs/": [],
                "docs/.nojekyll": ["docs/.nojekyll"],
                "docs/_themes/.gitignore": ["docs/_themes/.gitignore"],
            },
            narrowed_entries(
                root, ["docs/", "docs/.nojekyll", "docs/_themes/.gitignore"], ["docs/"]
            ),
        )
        self.assertEqual(
            {"docs/.nojekyll": []},
            narrowed_entries(root, ["docs/.nojekyll"], ["docs/", "docs/.nojekyll"]),
        )

    @verifies("scenario.adoption.describe-stubs-cleaned")
    def test_stubs_are_removed_when_the_worker_step_raises(self):
        from unittest.mock import patch

        self.scaffolded()
        with patch(
            "concorde.adoption.code_to_spec.describe", side_effect=RuntimeError("boom")
        ):
            _, envelope = self.describe([{}])
        self.assertEqual("failed", envelope["status"])
        folder = self.worktree / "specs/project/checkout"
        self.assertEqual(
            ["module.md", "module.md.json"], sorted(p.name for p in folder.iterdir())
        )

    @verifies("scenario.adoption.invalid-answers")
    def test_unusable_answers_stop_before_anything_runs(self):
        worktree = self.open()
        broken = self.project.base / "broken.json"
        broken.write_text("{not json")
        missing = self.project.answers({"question": "x", "answer": "y"})
        for path in (str(broken), missing):
            for run in (
                lambda path=path: self.survey(PROPOSAL, "--answers", path),
                lambda path=path: self.describe(
                    [{}], "--answers", path, modules="module.shop"
                ),
            ):
                with self.subTest(path=path):
                    _status, envelope = run()
                    self.assertEqual("failed", envelope["status"])
                    self.assertEqual("invalid_answers", envelope["error"]["code"])
                    self.assertIn(path, envelope["error"]["detail"])
                    self.assertEqual([], envelope["worker_runs"])
        self.assertEqual("", git(worktree, "status", "--porcelain"))

    # --- scaffold --------------------------------------------------------------------------

    @verifies("scenario.adoption.scaffold-creates")
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
        self.assertIn(
            '<a id="contains-checkout"></a>',
            (worktree / "specs/project/module.md").read_text(),
        )
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
            [], [f.message for f in report.findings if f.severity == "error"]
        )

    @verifies("scenario.adoption.scaffold-stale")
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

    @verifies("scenario.adoption.scaffold-refused-input")
    def test_the_scaffold_needs_one_survey_of_its_task(self):
        worktree = self.open()
        _, survey = self.survey()
        _, second = self.survey()
        _, validate = self.project.run("validate", "--task", "adopt")
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
        self.assertEqual("input_not_admissible", envelope["host_evidence"][0]["ref"])

    # --- code_to_spec ----------------------------------------------------------------------

    def described_entry(self) -> str:
        text = (self.worktree / "specs/project/checkout/module.md").read_text()
        return text.replace(
            "How Checkout is used is not specified yet",
            "Checkout is used through submit(basket), which holds stock and returns one order. "
            "Whether other payment failures should be retried is not specified yet; how it is "
            "used otherwise is not specified yet",
        )

    SCENARIOS = (
        "# Checkout scenarios\n\n"
        "### scenario.checkout.submit — Submitting a basket\n\n"
        "- GIVEN a basket\n- WHEN it is submitted\n- THEN one order is returned\n"
    )

    @verifies("scenario.adoption.describe-module")
    @verifies("scenario.adoption.open-question")
    def test_code_to_spec_describes_a_module(self):
        self.scaffolded()
        entry = self.worktree / "specs/project/checkout/module.md"
        claims = {
            "summary": "Described submit.",
            "promises": [
                {
                    "module": "module.checkout",
                    "kind": "scenario",
                    "id": "scenario.checkout.submit",
                    "description": "a basket becomes one order",
                    "source": "code",
                    "question": None,
                }
            ],
            "decisions": [],
            "open_questions": [RETRY_QUESTION],
            "deviations": [],
        }
        status, envelope = self.describe(
            [
                {
                    "writes": {
                        str(entry): self.described_entry(),
                        str(
                            self.worktree / "specs/project/checkout/scenarios.md"
                        ): self.SCENARIOS,
                    },
                    "result": {"output": claims},
                }
            ]
        )
        self.assertEqual(0, status, envelope)
        output = envelope["output"]
        self.assertIn("specs/project/checkout/module.md", output["changed_documents"])
        self.assertEqual(
            ["specs/project/checkout/scenarios.md"], output["created_documents"]
        )
        self.assertEqual(
            [
                "specs/project/checkout/contracts.md",
                "specs/project/checkout/requirements.md",
            ],
            output["removed_stubs"],
        )
        self.assertFalse(
            (self.worktree / "specs/project/checkout/contracts.md").exists()
        )
        self.assertEqual([RETRY_QUESTION], output["open_questions"])
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        self.assertEqual("code-to-spec", record["task_type"])
        fake = self.fake_round(envelope)
        tools = fake["argv"][fake["argv"].index("--tools") + 1]
        self.assertIn("Edit", tools)
        self.assertNotIn("Bash", tools)
        self.assertIn("Describing the code you read", fake["prompt"])
        # Spec-writing workers see no Protocol file, so the brief carries the project's guide.
        self.assertIn("The Protocol's writing guide", fake["prompt"])
        self.assertIn("# Module specifications", fake["prompt"])
        self.assertIn("holds only `concept` and `realization` records", fake["prompt"])
        self.assertEqual("", git(self.worktree, "status", "--porcelain", "src"))
        owned = json.loads((entry.parent / "module.md.json").read_text())["module"][
            "owns"
        ]
        self.assertEqual(
            ["specs/project/checkout/module.md", "specs/project/checkout/scenarios.md"],
            owned,
        )

    @verifies("scenario.adoption.describe-stubs-cleaned")
    def test_a_run_that_stops_early_leaves_no_stubs(self):
        self.scaffolded()
        _status, envelope = self.describe(
            [{"result": {"status": "failed", "error": None, "output": {}}}]
        )
        self.assertEqual("failed", envelope["status"])
        folder = self.worktree / "specs/project/checkout"
        self.assertEqual(
            ["module.md", "module.md.json"], sorted(p.name for p in folder.iterdir())
        )
        owned = json.loads((folder / "module.md.json").read_text())["module"]["owns"]
        self.assertEqual(["specs/project/checkout/module.md"], owned)

    @verifies("scenario.adoption.answered-deviation")
    def test_an_answered_question_becomes_a_promise_and_a_deviation(self):
        self.scaffolded()
        _, first = self.describe(
            [
                {
                    "result": {
                        "output": {
                            "summary": "s",
                            "promises": [],
                            "decisions": [],
                            "open_questions": [RETRY_QUESTION],
                            "deviations": [],
                        }
                    }
                }
            ]
        )
        self.assertEqual("ok", first["status"], first)
        answers = self.project.answers(
            {
                "id": "q.payment-retry",
                "question": "retrying a declined payment",
                "answer": "retry every failure once",
            }
        )
        claims = {
            "summary": "Stated the retry rule.",
            "promises": [
                {
                    "module": "module.checkout",
                    "kind": "explanation",
                    "id": None,
                    "description": "every failed payment is retried once",
                    "source": "answer",
                    "question": "q.payment-retry",
                }
            ],
            "decisions": [],
            "open_questions": [],
            "deviations": [
                {
                    "module": "module.checkout",
                    "question": "q.payment-retry",
                    "intended": "every failure is retried once",
                    "observed": "only declines are retried",
                }
            ],
        }
        status, envelope = self.describe(
            [{"result": {"output": claims}}],
            "--answers",
            answers,
            "--input",
            first["run_id"],
        )
        self.assertEqual(0, status, envelope)
        self.assertEqual(claims["deviations"], envelope["output"]["deviations"])
        claims["promises"] = []
        claims["deviations"] = []
        status, envelope = self.describe(
            [{"result": {"output": claims}}], "--answers", answers
        )
        self.assertEqual("failed", envelope["status"])
        self.assertEqual("inconsistent_description", envelope["error"]["code"])

    @verifies("scenario.adoption.describe-invalid")
    def test_a_description_that_breaks_the_specs_is_blocked(self):
        self.scaffolded()
        broken = self.SCENARIOS.replace("- THEN one order is returned\n", "")
        _status, envelope = self.describe(
            [
                {
                    "writes": {
                        str(
                            self.worktree / "specs/project/checkout/scenarios.md"
                        ): broken
                    },
                    "result": {
                        "output": {
                            "summary": "s",
                            "promises": [],
                            "decisions": [],
                            "open_questions": [],
                            "deviations": [],
                        }
                    },
                }
            ]
        )
        self.assertEqual("blocked", envelope["status"])
        error = envelope["error"]
        self.assertEqual("new_structural_errors", error["code"])
        self.assertTrue(error["causes"])
        self.assertTrue(
            all(cause["code"] == "spec_finding" for cause in error["causes"])
        )
        record = read_record(self.project.root, envelope["worker_runs"][-1])
        self.assertEqual(1, len(record["rounds"]))
        self.assertEqual(
            broken, (self.worktree / "specs/project/checkout/scenarios.md").read_text()
        )


if __name__ == "__main__":
    unittest.main()
