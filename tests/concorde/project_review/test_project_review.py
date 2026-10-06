"""The ``project_review`` Operation: whole project reviews with fake workers."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.issues.store import list_issues, read_issue
from concorde.method import review_issues
from concorde.method.project_review import record
from concorde.method.project_review.operation import PAYLOAD_SCHEMA, code_digest
from concorde.worker_harness.runs import read_record
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate
from concorde.spec.verification import verifies
from tests.concorde.spec_review.test_panel import without_issues
from tests.concorde.support.operation_project import OperationProject, commit
from tests.concorde.support.paths import REPOSITORY_ROOT

FAKE_WORKER = Path(__file__).with_name("fake_worker.py")


def spec_finding(module="module.a", tier="obvious-fix", **extra):
    letter = module.split(".")[1]
    return {
        "module": module,
        "path": f"specs/{letter}/module.md",
        "dimension": "obligations",
        "severity": "high",
        "tier": tier,
        "title": f"A {tier} Spec problem of {module}",
        "problem": "A requirement holds two obligations.",
        "impact": "A reader could not rely on it.",
        "evidence": "Quoted text.",
        "suggestion": "Split it.",
        **extra,
    }


def merged(*sources, **extra):
    return {**spec_finding(**extra), "sources": list(sources), "note": "Verified."}


def architectural(**extra):
    return spec_finding(
        dimension="interfaces",
        tier="decision-needed",
        title="A relies on B's internals",
        problem="A relies on a promise B does not make.",
        related=["module.b"],
        **extra,
    )


def code_finding(tier="obvious-fix", **extra):
    return {
        "module": "module.a",
        "kind": "defect",
        "severity": "high",
        "tier": tier,
        "title": "add subtracts",
        "problem": "add returns a - b.",
        "impact": "Every sum is wrong.",
        "basis": "specs/a/module.md",
        "locations": ["src/a/calc.py:2"],
        "evidence": "return a - b",
        "suggestion": "Return a + b.",
        **extra,
    }


def worker(**output):
    return [{"result": {"output": output}}]


class ProjectReviewTests(unittest.TestCase):
    def setUp(self):
        self.project = OperationProject(self)
        self.root = self.project.root

    def review(self, plans=None, *arguments, cwd=None):
        """Run ``project_review``, unbound in the primary worktree unless ``cwd`` names another,
        with the fake workers' ``plans``; an unbound run has no goal to carry them, so the
        wrapper gives them."""
        wrapper = self.project.base / "claude-project"
        quoted = json.dumps(plans or {}).replace("'", "'\"'\"'")
        wrapper.write_text(
            f"#!/bin/sh\nFAKE_REVIEW_PLANS='{quoted}' "
            f'exec "{sys.executable}" "{FAKE_WORKER}" "$@"\n'
        )
        wrapper.chmod(0o755)
        self.project.fake = wrapper
        status, envelope = self.project.run(
            "project_review",
            "--reviewers",
            "2",
            "--architects",
            "1",
            *arguments,
            cwd=cwd,
        )
        self.envelope = envelope
        return status, envelope

    def workers(self, envelope=None) -> list[str]:
        """Each worker of the run as its worker id and the Module its brief names."""
        found = []
        for run_id in (envelope or self.envelope)["worker_runs"]:
            value = read_record(self.root / ".concorde", run_id)
            brief = (Path(value["run_directory"]) / "brief.md").read_text()
            module = re.search(r"Reviewed Modules?: `([^`]+)`", brief).group(1)
            found.append(f"{value['worker']} {module}")
        return sorted(found)

    def issues(self) -> dict:
        return {
            row["id"]: read_issue(self.root, row["id"])[0]
            for row in list_issues(self.root)
        }

    def head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def module(self, envelope, module="module.a") -> dict:
        return next(
            item for item in envelope["output"]["modules"] if item["module"] == module
        )

    @verifies("scenario.project-review.whole-project")
    def test_a_first_review_runs_every_part_and_records_what_it_judged(self):
        before = self.head()
        status, envelope = self.review(
            {
                "reviewer module.a 1": worker(findings=[spec_finding()]),
                "chair module.a 1": worker(findings=[merged("r1.1")], rejected=[]),
                "architect project 1": worker(findings=[architectural()]),
                "chair project 1": worker(
                    findings=[
                        {
                            **architectural(),
                            "sources": ["a1.1"],
                            "note": "B states no such promise.",
                        }
                    ],
                    rejected=[],
                ),
                "code module.a 1": worker(findings=[code_finding()]),
            }
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        validate(output, PAYLOAD_SCHEMA)
        self.assertEqual("changes_required", output["verdict"])
        # Every part ran: a panel and a code review per Module, the architecture review once.
        self.assertEqual(
            [
                "arch_chair project",
                "architect1 project",
                "chair module.a",
                "chair module.b",
                "code_reviewer module.a",
                "code_reviewer module.b",
                "reviewer1 module.a",
                "reviewer1 module.b",
                "reviewer2 module.a",
                "reviewer2 module.b",
            ],
            self.workers(),
        )
        a = self.module(envelope)
        self.assertEqual(
            ("changes_required", "reviewed", "reviewed"),
            (a["outcome"], a["panel"]["state"], a["code_review"]["state"]),
        )
        # Module B's only problem is its scenario no test verifies, a deterministic finding.
        b = self.module(envelope, "module.b")
        self.assertEqual(
            ("changes_required", ["Scenarios of module.b that no test verifies"]),
            (b["outcome"], [item["title"] for item in b["standing"]]),
        )
        # Each finding is an Issue of its Module, told apart by its provenance phase.
        phases = {}
        for record_value in self.issues().values():
            source = record_value["reports"][0]["source"]
            self.assertEqual("project_review", source["operation"])
            phases[record_value["reports"][0]["report"]["title"]] = source["phase"]
        self.assertEqual(
            {
                "A obvious-fix Spec problem of module.a": "spec-panel",
                "A relies on B's internals": "architecture",
                "add subtracts": "code-review",
                "Scenarios of module.a that no test verifies": "coverage",
                "Scenarios of module.b that no test verifies": "coverage",
                "Tracked files bound to no Module": "unowned",
            },
            phases,
        )
        # Every Issue of module.a stands for it, the unowned files' too, since A is the root.
        self.assertEqual(
            sorted(
                title
                for title in phases
                if title != "Scenarios of module.b that no test verifies"
            ),
            sorted(item["title"] for item in a["standing"]),
        )
        self.assertEqual(
            [".gitignore", "checks/a_check.py"], output["deterministic"]["unowned"]
        )
        self.assertEqual(
            {"issues": 6, "blocking": 6},
            {key: output["standing"][key] for key in ("issues", "blocking")},
        )
        # The record is one commit of its own on the primary branch, after the Issues.
        judged = record.read(self.root)
        self.assertEqual({"module.a", "module.b"}, set(judged["modules"]))
        self.assertEqual(envelope["run_id"], judged["architecture"]["run"])
        self.assertEqual(before, judged["modules"]["module.a"]["panel"]["commit"])
        self.assertEqual(
            [record.PATH],
            subprocess.run(
                ["git", "show", "--name-only", "--format=", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split(),
        )
        self.assertEqual(output["record"]["commit"], self.head())
        self.assertEqual(
            "",
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout,
        )

    def first(self):
        """A first review whose only worker findings are module.a's Spec and code problems."""
        status, envelope = self.review(
            {
                "reviewer module.a 1": worker(findings=[spec_finding()]),
                "chair module.a 1": worker(findings=[merged("r1.1")], rejected=[]),
                "code module.a 1": worker(findings=[code_finding()]),
            }
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        return envelope

    def issue_of(self, envelope, title: str) -> str:
        return next(
            item["issue"]
            for module in envelope["output"]["modules"]
            for item in module["standing"]
            if item["title"] == title
        )

    @verifies("scenario.project-review.skips-unchanged")
    def test_a_repeated_review_skips_what_is_unchanged(self):
        first = self.first()
        recorded = self.head()
        status, envelope = self.review()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        validate(output, PAYLOAD_SCHEMA)
        # No worker ran: every part is skipped, and the record does not change.
        self.assertEqual([], envelope["worker_runs"])
        self.assertEqual("skipped", output["architecture"]["state"])
        a = self.module(envelope)
        self.assertEqual(
            ("skipped", None, "skipped", None),
            (
                a["panel"]["state"],
                a["panel"]["review"],
                a["code_review"]["state"],
                a["code_review"]["review"],
            ),
        )
        # The skipped Module's outcome comes from the Issues that stand.
        self.assertEqual(
            ("changes_required", self.module(first)["standing"]),
            (a["outcome"], a["standing"]),
        )
        self.assertEqual(
            (False, None, recorded),
            (output["record"]["published"], output["record"]["commit"], self.head()),
        )
        skips = [item for item in envelope["host_evidence"] if item["kind"] == "skip"]
        self.assertEqual(5, len(skips), skips)
        # The checks still ran, and the unchanged deterministic problems were carried, not
        # reported again.
        self.assertEqual(["passed"], [item["outcome"] for item in output["checks"]])
        self.assertEqual(3, len(output["deterministic"]["earlier_issues"]["carried"]))
        self.assertTrue(
            all(len(item["reports"]) == 1 for item in self.issues().values())
        )

    @verifies("scenario.project-review.code-change")
    def test_a_code_change_reviews_only_that_modules_code(self):
        first = self.first()
        earlier = self.issue_of(first, "add subtracts")
        (self.root / "src/a/calc.py").write_text("def add(a, b):\n    return a + b\n")
        commit(self.root, "fix add")
        status, envelope = self.review(
            {
                "code module.a 1": worker(
                    findings=[],
                    resolved=[{"issue": earlier, "reason": "add returns a + b now."}],
                )
            }
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(["code_reviewer module.a"], self.workers())
        a = self.module(envelope)
        self.assertEqual(
            ("skipped", "reviewed"), (a["panel"]["state"], a["code_review"]["state"])
        )
        self.assertEqual(
            [{"issue": earlier, "reason": "add returns a + b now."}],
            a["code_review"]["review"]["earlier_issues"]["resolved"],
        )
        # A resolved Issue no longer stands, though only a task closes it.
        self.assertNotIn(earlier, [item["issue"] for item in a["standing"]])
        self.assertEqual("open", self.issues()[earlier]["status"])
        judged = record.read(self.root)["modules"]["module.a"]
        self.assertEqual(envelope["run_id"], judged["code_review"]["run"])
        self.assertEqual(first["run_id"], judged["panel"]["run"])

    @verifies("scenario.project-review.full")
    def test_full_reviews_everything_again(self):
        self.first()
        status, envelope = self.review(None, "--full")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual(10, len(envelope["worker_runs"]))
        self.assertTrue(envelope["output"]["full"])
        self.assertEqual("reviewed", envelope["output"]["architecture"]["state"])

    @verifies("scenario.project-review.failed-check")
    def test_a_failed_check_is_an_issue(self):
        (self.root / "src/a/flag").write_text("broken")
        commit(self.root, "break the check")
        status, envelope = self.review()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual(["failed"], [item["outcome"] for item in output["checks"]])
        (check,) = [
            item
            for item in output["deterministic"]["findings"]
            if item["phase"] == "check"
        ]
        self.assertEqual(
            ("module.a", "obvious-fix", "high", ["check.a"]),
            (check["module"], check["tier"], check["severity"], check["subjects"]),
        )
        report = self.issues()[check["issue"]]["reports"][0]
        self.assertEqual(
            ("project_review", "check"),
            (report["source"]["operation"], report["source"]["phase"]),
        )
        # The code reviewer reads the failed check's log.
        brief = next(
            (
                Path(read_record(self.root / ".concorde", run)["run_directory"])
                / "brief.md"
            ).read_text()
            for run in envelope["worker_runs"]
            if read_record(self.root / ".concorde", run)["worker"] == "code_reviewer"
            and "`module.a`"
            in (
                Path(read_record(self.root / ".concorde", run)["run_directory"])
                / "brief.md"
            ).read_text()
        )
        self.assertIn("check.a (module.a): failed", brief)
        self.check_issue = check["issue"]

    @verifies("scenario.project-review.check-repaired")
    def test_a_repaired_checks_issue_no_longer_stands(self):
        self.test_a_failed_check_is_an_issue()
        check = {"issue": self.check_issue}
        (self.root / "src/a/flag").write_text("ok")
        commit(self.root, "repair the check")
        status, envelope = self.review()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertIn(
            check["issue"],
            [
                item["issue"]
                for item in envelope["output"]["deterministic"]["earlier_issues"][
                    "resolved"
                ]
            ],
        )
        self.assertNotIn(
            check["issue"],
            [item["issue"] for item in self.module(envelope)["standing"]],
        )
        self.assertEqual("open", self.issues()[check["issue"]]["status"])

    @verifies("scenario.project-review.without-issues")
    def test_without_the_issues_part_nothing_is_skipped_or_recorded(self):
        with without_issues():
            self.first()
            before = self.head()
            status, envelope = self.review(
                {"code module.a 1": worker(findings=[code_finding()])}
            )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual(10, len(envelope["worker_runs"]))
        self.assertEqual(before, self.head())
        self.assertFalse(output["record"]["published"])
        self.assertEqual({}, self.issues())
        a = self.module(envelope)
        self.assertEqual(
            ("changes_required", [None]),
            (
                a["outcome"],
                [item["issue"] for item in a["code_review"]["review"]["findings"]],
            ),
        )
        self.assertIsNone(output["deterministic"]["earlier_issues"])
        self.assertIn(review_issues.NOT_RECORDED, envelope["summary"])

    @verifies("scenario.project-review.record-refused")
    def test_a_record_with_an_uncommitted_change_is_refused(self):
        self.first()
        path = self.root / record.PATH
        path.write_text(path.read_text() + "edited by hand\n")
        status, envelope = self.review(None, "--full")
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        error = envelope["error"]
        self.assertEqual("review_incomplete", error["code"])
        (cause,) = error["causes"]
        self.assertEqual("record_unpublished", cause["code"])
        self.assertIn("uncommitted_change", cause["detail"])
        # The reviews completed and their verdict stands; only the record was not written.
        self.assertEqual("changes_required", envelope["output"]["verdict"])
        self.assertFalse(envelope["output"]["record"]["published"])

    def test_a_run_with_nothing_new_still_refuses_a_changed_record(self):
        self.first()
        path = self.root / record.PATH
        path.write_text(path.read_text() + "edited by hand\n")
        status, envelope = self.review()
        self.assertEqual((1, "failed"), (status, envelope["status"]))
        self.assertEqual([], envelope["worker_runs"])
        (cause,) = envelope["error"]["causes"]
        self.assertIn("uncommitted_change", cause["detail"])

    def test_a_narrowed_review_without_issues_counts_only_its_modules(self):
        with without_issues():
            status, envelope = self.review(
                {
                    "reviewer module.a 1": worker(findings=[spec_finding()]),
                    "chair module.a 1": worker(findings=[merged("r1.1")], rejected=[]),
                },
                "--modules",
                "module.b",
            )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        # The architecture review and the unowned files concern module.a, which the run does
        # not cover; only module.b's uncovered scenario counts.
        self.assertEqual(1, envelope["output"]["standing"]["issues"])

    @verifies("scenario.project-review.record-leftover")
    def test_a_record_an_interrupted_write_left_is_put_back(self):
        self.first()
        path = self.root / record.PATH
        committed = path.read_text()
        # What a write interrupted between publishing and committing leaves: a valid record.
        value = json.loads(committed)
        value["modules"]["module.b"]["panel"]["run"] = "r-interrupted"
        path.write_text(json.dumps(value))
        status, envelope = self.review(None, "--full")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertTrue(envelope["output"]["record"]["published"])
        self.assertEqual(
            envelope["run_id"],
            record.read(self.root)["modules"]["module.b"]["panel"]["run"],
        )
        self.assertEqual(
            "",
            subprocess.run(
                ["git", "status", "--porcelain", "--", record.PATH],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout,
        )

    @verifies("scenario.project-review.skipped-resolutions")
    def test_a_skipped_part_keeps_what_its_last_judgment_resolved(self):
        first = self.first()
        earlier = self.issue_of(first, "add subtracts")
        (self.root / "src/a/calc.py").write_text("def add(a, b):\n    return a + b\n")
        commit(self.root, "fix add")
        self.review(
            {
                "code module.a 1": worker(
                    findings=[],
                    resolved=[{"issue": earlier, "reason": "add returns a + b now."}],
                )
            }
        )
        judged = record.read(self.root)["modules"]["module.a"]["code_review"]
        self.assertEqual([earlier], [item["issue"] for item in judged["resolved"]])
        # The Issue stays open until a task closes it, but a run that skips the code review
        # still counts it resolved.
        status, envelope = self.review()
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        a = self.module(envelope)
        self.assertEqual("skipped", a["code_review"]["state"])
        self.assertNotIn(earlier, [item["issue"] for item in a["standing"]])
        self.assertEqual("open", self.issues()[earlier]["status"])

    @verifies("scenario.project-review.narrowed")
    def test_a_narrowed_review_counts_only_its_modules(self):
        self.first()
        status, envelope = self.review(None, "--modules", "module.b", "--full")
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        output = envelope["output"]
        self.assertEqual(["module.b"], [item["module"] for item in output["modules"]])
        # module.a's Issues stand for module.a, which this run does not cover.
        self.assertEqual(
            {"issues": 1, "blocking": 1},
            {key: output["standing"][key] for key in ("issues", "blocking")},
        )
        status, envelope = self.review(None, "--modules", "module.b,module.a")
        self.assertEqual(
            ["module.a", "module.b"],
            [item["module"] for item in envelope["output"]["modules"]],
        )

    @verifies("scenario.project-review.shared-earlier")
    def test_spec_panel_offers_what_project_review_recorded(self):
        first = self.first()
        issue = self.issue_of(first, "A obvious-fix Spec problem of module.a")
        status, envelope = self.project.run(
            "spec_panel",
            "--modules",
            "module.a",
            "--reviewers",
            "2",
            "--architects",
            "0",
        )
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        (module,) = envelope["output"]["modules"]
        self.assertIn(
            issue, [item["issue"] for item in module["earlier_issues"]["carried"]]
        )
        self.assertEqual("changes_required", module["outcome"])

    @verifies("scenario.project-review.structural-error")
    def test_a_structurally_invalid_module_is_incomplete_alone(self):
        document = self.root / "specs/b/module.md"
        # A Mermaid block is a structural error (CHK.view.marked).
        document.write_text(
            document.read_text() + "\n```mermaid\ngraph TD\n  a --> b\n```\n"
        )
        commit(self.root, "break B")
        status, envelope = self.review()
        self.assertEqual((1, "blocked"), (status, envelope["status"]), envelope)
        b = self.module(envelope, "module.b")
        self.assertEqual(
            ("incomplete", "not_run", "not_run"),
            (b["outcome"], b["panel"]["state"], b["code_review"]["state"]),
        )
        self.assertEqual("reviewed", self.module(envelope)["panel"]["state"])
        self.assertNotIn("module.b", " ".join(self.workers()))
        self.assertEqual("incomplete", envelope["output"]["verdict"])
        self.assertNotIn("module.b", record.read(self.root)["modules"])

    @verifies("scenario.project-review.bound")
    def test_a_bound_run_reviews_the_whole_workspace(self):
        self.project.open_task("t1", modules=("module.a",), goal="Review.")
        worktree = self.project.worktree("t1")
        status, envelope = self.review(None, cwd=worktree)
        self.assertEqual((0, "ok"), (status, envelope["status"]), envelope)
        self.assertEqual("t1", envelope["workspace"])
        self.assertEqual(
            ["module.a", "module.b"],
            [item["module"] for item in envelope["output"]["modules"]],
        )
        # The record went to the primary branch, which keeps it, not to the task branch.
        self.assertEqual(
            {"module.a", "module.b"}, set(record.read(self.root)["modules"])
        )
        self.assertFalse((worktree / record.PATH).exists())


class ContractTests(unittest.TestCase):
    def test_the_code_digest_is_the_contracts_example(self):
        class Repository:
            root = Path(self.id()).parent

            def bound_files(self, module):
                return ["src/new.py"]

        with patch(
            "concorde.method.project_review.operation.read_file",
            return_value=b"VALUE = 0\n",
        ):
            self.assertEqual(
                "sha256:d3cd0b526c5ffd5461366f21cca18eee4ea7319ab82a0fcb02c1635f1720a9c3",
                code_digest(Repository(), "module.a"),
            )

        class Accented(Repository):
            def bound_files(self, module):
                return ["src/caf\u00e9.py"]

        with patch(
            "concorde.method.project_review.operation.read_file",
            return_value=b"VALUE = 0\n",
        ):
            self.assertEqual(
                "sha256:d67f0d5e66b3f32653a082cdf39b2541a13dbfeacbff198d9c42004307c715e1",
                code_digest(Accented(), "module.a"),
            )

    def test_the_output_schemas_are_the_contracts(self):
        contracts = {
            item["id"]: item
            for item in SpecRepository(REPOSITORY_ROOT).contracts(
                "module.project-review"
            )
        }
        report = contracts["contract.project-review.report"]
        self.assertEqual(report["schema"], PAYLOAD_SCHEMA)
        validate(report["example"], PAYLOAD_SCHEMA)
        stored = contracts["contract.project-review.record"]
        self.assertEqual(stored["schema"], record.SCHEMA)
        validate(stored["example"], record.SCHEMA)


if __name__ == "__main__":
    unittest.main()
