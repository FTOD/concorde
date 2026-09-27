"""The ``concorde delivery`` execution command end to end on a fixture task."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest

from concorde.delivery.bundle import BUNDLE_SCHEMA, OUTPUT_SCHEMA
from concorde.delivery.command import DELIVERY
from concorde.errors import codes
from concorde.spec.repository import SpecRepository
from concorde.spec.schema import validate as check_schema
from concorde.spec.verification import verifies
from concorde.validation.measurement import measure, sha256
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.validation.project import (
    ValidationProject,
    evidence_of,
    git,
    status_lines,
)

FIXED = "def add(a, b):\n    return a + b\n"


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.project = ValidationProject(self)
        self.worktree = self.project.task()
        self.base = git(self.worktree, "rev-parse", "HEAD")

    def validated(self) -> dict:
        status, envelope = self.project.validate()
        self.assertEqual(status, 0, envelope)
        self.assertTrue(envelope["output"]["ready"], envelope["output"]["blocking"])
        return envelope

    def head(self) -> str:
        return git(self.worktree, "rev-parse", "HEAD")

    def committed(self, path: str, commit: str = "HEAD") -> str:
        return git(self.worktree, "show", f"{commit}:{path}")

    def commit_step(self, message: str = "A verified step") -> str:
        git(self.worktree, "add", "-A")
        git(self.worktree, "commit", "-q", "-m", message)
        return self.head()

    def saved_readiness(self, envelope: dict) -> dict:
        path = (
            self.project.root / ".concorde/runs" / envelope["run_id"] / "readiness.json"
        )
        return json.loads(path.read_text())

    def assert_inert(self, envelope: dict, code: str, deliveries: int = 0):
        self.assertEqual(envelope["status"], "blocked", envelope)
        self.assertIsNone(envelope["output"])
        refs = [item["ref"] for item in envelope["host_evidence"]]
        self.assertIn(code, refs)
        self.assertEqual(
            (envelope["error"]["level"], envelope["error"]["code"]), ("command", code)
        )
        self.assertEqual(
            envelope["error"]["actor"],
            f"Command delivery {envelope['run_id']} (workspace t1)",
        )
        self.assertEqual(envelope["error"]["unhandled"]["reason"], "decision")
        self.assertEqual(len(self.project.deliveries()), deliveries)

    @verifies("scenario.delivery.sandbox-masks")
    def test_deliver_inside_a_sandbox_that_masks_a_path(self):
        bwrap = shutil.which("bwrap")
        sandbox = [bwrap, "--dev-bind", "/", "/"] if bwrap else []
        if not bwrap or subprocess.run([*sandbox, "true"], check=False).returncode != 0:
            self.skipTest("bubblewrap cannot create a sandbox here")
        # The check boundary would need a second sandbox inside this one; what is under test is
        # the measurement and the staging, so the task runs without configured checks.
        config = self.worktree / ".concorde/config.json"
        value = json.loads(config.read_text())
        value["checks"] = []
        config.write_text(json.dumps(value, indent=2) + "\n")
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        masked = self.worktree / ".bashrc"
        done = subprocess.run(
            [
                *sandbox,
                "--bind",
                "/dev/null",
                str(masked),
                sys.executable,
                str(REPOSITORY_ROOT / "scripts/concorde.py"),
                "delivery",
            ],
            cwd=self.worktree,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        envelope = json.loads(done.stdout.split("\n}\n", 1)[0] + "\n}")
        self.assertEqual("ok", envelope["status"], envelope)
        readiness = self.saved_readiness(envelope)
        changed = [item["path"] for item in readiness["inputs"]["changed"]]
        self.assertEqual([".concorde/config.json", "src/a/calc.py"], changed)
        committed = git(self.worktree, "show", "--name-only", "--format=", "HEAD")
        self.assertIn("src/a/calc.py", committed.splitlines())
        self.assertNotIn(".bashrc", committed.splitlines())

    @verifies("scenario.delivery.deliver")
    def test_deliver_a_validated_task(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        (self.worktree / "src/a/extra.py").write_text("EXTRA = 1\n")
        validation = self.validated()
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        output = envelope["output"]
        commit = self.head()
        self.assertEqual(
            output,
            {
                "commit": commit,
                "branch": "concorde/t1",
                "bundle": ".concorde/evidence/t1/1.json",
                "sequence": 1,
                "confirmed": [],
                "recovered": False,
            },
        )
        self.assertEqual(git(self.worktree, "rev-parse", "concorde/t1"), commit)
        self.assertEqual(
            git(self.worktree, "rev-list", "--parents", "-n1", commit).split()[1:],
            [self.base],
        )
        self.assertEqual(
            sorted(
                git(
                    self.worktree, "diff", "--name-only", self.base, commit
                ).splitlines()
            ),
            [".concorde/evidence/t1/1.json", "src/a/calc.py", "src/a/extra.py"],
        )
        self.assertEqual(self.committed("src/a/calc.py") + "\n", FIXED)
        message = git(self.worktree, "log", "-1", "--format=%B")
        self.assertEqual(
            message,
            "concorde: deliver t1\n\nFix A.\n\nConcorde-Workspace: t1\n"
            "Concorde-Evidence: .concorde/evidence/t1/1.json\n"
            f"Concorde-Readiness: {envelope['run_id']}",
        )
        self.assertEqual(
            git(self.worktree, "log", "-1", "--format=%an <%ae>"),
            "Delivery Test <delivery@test>",
        )
        bundle = json.loads(self.committed(".concorde/evidence/t1/1.json"))
        check_schema(bundle, BUNDLE_SCHEMA)
        self.assertEqual(bundle["parent_commit"], self.base)
        # Delivery decides the readiness itself; an earlier validate run is only listed.
        self.assertEqual(bundle["readiness"]["run_id"], envelope["run_id"])
        self.assertEqual(
            bundle["readiness"]["input_digest"],
            validation["output"]["inputs"]["digest"],
        )
        self.assertTrue(self.saved_readiness(envelope)["ready"])
        self.assertEqual(
            [run["run_id"] for run in bundle["runs"]], [validation["run_id"]]
        )
        saved = (
            self.project.root / ".concorde/runs" / validation["run_id"] / "result.json"
        )
        self.assertEqual(bundle["runs"][0]["result_digest"], sha256(saved.read_bytes()))
        # The delivery commit is the only record of the delivery: the task record is untouched
        # and the task level reads the delivery back from Git.
        self.assertEqual(self.project.record()["state"], "open")
        self.assertEqual(self.project.state(), "delivered")
        self.assertEqual(
            [
                (d["commit"], d["bundle"], d["readiness_run"])
                for d in self.project.deliveries()
            ],
            [(commit, ".concorde/evidence/t1/1.json", envelope["run_id"])],
        )
        self.assertEqual(status_lines(self.worktree), "")
        self.assertEqual(
            ("command", "delivery", "t1"),
            (envelope["kind"], envelope["name"], envelope["workspace"]),
        )
        self.assertIsNone(envelope["worker"])
        self.assertEqual(envelope["worker_runs"], [])

    @verifies("scenario.delivery.unverified-scenarios")
    def test_a_code_change_with_an_untested_new_scenario_is_refused(self):
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver()
        self.assert_inert(envelope, "unverified_scenarios")
        detail = envelope["error"]["detail"]
        self.assertIn("scenario.a.sum (specs/a/obligations.md)", detail)
        # A scenario the task did not touch is not its to verify.
        self.assertNotIn("scenario.a.answer", detail)
        (self.worktree / "src/a/test_calc.py").write_text(
            "def verifies(*scenarios):\n    return lambda test: test\n\n\n"
            '@verifies("scenario.a.sum")\ndef test_sum():\n    pass\n'
        )
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)

    @verifies("scenario.delivery.unverified-scenarios")
    def test_a_spec_only_change_needs_no_test(self):
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)

    @verifies("scenario.delivery.confirmations")
    def test_pending_markers_are_cleared_in_the_commit(self):
        (self.worktree / "src/new.py").write_text("NEW = 1\n")
        self.validated()
        status, envelope = self.project.deliver()
        self.assertEqual(status, 0, envelope)
        self.assertEqual(envelope["output"]["confirmed"], ["src/new.py"])
        metadata = json.loads(self.committed("specs/a/module.md.json"))
        pending = {
            item["id"]: item.get("pending", [])
            for item in metadata["defines"]
            if item["type"] == "realization"
        }
        self.assertEqual(pending["realization.a.new"], [])
        bundle = json.loads(self.committed(".concorde/evidence/t1/1.json"))
        self.assertEqual(
            bundle["confirmations"],
            [
                {
                    "module": "module.a",
                    "realization": "realization.a.new",
                    "entry": "src/new.py",
                }
            ],
        )
        self.assertEqual(status_lines(self.worktree), "")

    @verifies("scenario.delivery.second")
    def test_deliver_again_after_further_work(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        self.validated()
        first = self.project.deliver()[1]["output"]["commit"]
        (self.worktree / "src/a/more.py").write_text("MORE = 1\n")
        second_validation = self.validated()
        status, envelope = self.project.deliver()
        self.assertEqual(status, 0, envelope)
        output = envelope["output"]
        self.assertEqual(
            (output["sequence"], output["bundle"]), (2, ".concorde/evidence/t1/2.json")
        )
        self.assertEqual(
            git(
                self.worktree, "rev-list", "--parents", "-n1", output["commit"]
            ).split()[1:],
            [first],
        )
        bundle = json.loads(self.committed(".concorde/evidence/t1/2.json"))
        self.assertEqual(
            [run["run_id"] for run in bundle["runs"]], [second_validation["run_id"]]
        )
        self.assertEqual(
            [item["commit"] for item in self.project.deliveries()],
            [first, output["commit"]],
        )

    @verifies("scenario.delivery.committed")
    def test_deliver_a_task_whose_steps_are_committed(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        step = self.commit_step()
        self.assertEqual(status_lines(self.worktree), "")
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        commit = envelope["output"]["commit"]
        self.assertEqual(
            git(self.worktree, "rev-list", "--parents", "-n1", commit).split()[1:],
            [step],
        )
        self.assertEqual(
            git(self.worktree, "diff", "--name-only", step, commit).splitlines(),
            [".concorde/evidence/t1/1.json"],
        )
        readiness = self.saved_readiness(envelope)
        self.assertEqual(
            [item["path"] for item in readiness["inputs"]["changed"]], ["src/a/calc.py"]
        )
        bundle = json.loads(self.committed(".concorde/evidence/t1/1.json"))
        self.assertEqual(
            (bundle["parent_commit"], bundle["readiness"]["input_digest"]),
            (step, readiness["inputs"]["digest"]),
        )
        self.assertEqual(status_lines(self.worktree), "")
        self.assertEqual(self.project.state(), "delivered")

    @verifies("scenario.delivery.not-ready")
    def test_refuse_a_task_that_is_not_ready(self):
        (self.worktree / "stray.txt").write_text("unbound\n")
        step = self.commit_step()
        status, envelope = self.project.deliver()
        self.assertEqual(status, 1)
        self.assert_inert(envelope, "not_ready")
        # Delivery's own Validation link is the cause, down to the committed stray file.
        self.assertEqual(
            ["not_ready", "not_deliverable", "unbound_finding"],
            codes(envelope["error"]),
        )
        self.assertIn("stray.txt", envelope["error"]["detail"])
        self.assertIn("never repairs", envelope["error"]["unhandled"]["explanation"])
        self.assertFalse(self.saved_readiness(envelope)["ready"])
        self.assertEqual((self.head(), status_lines(self.worktree)), (step, ""))

    @verifies("scenario.delivery.nothing")
    def test_nothing_to_deliver(self):
        self.validated()
        status, envelope = self.project.deliver()
        self.assertEqual(status, 1)
        self.assert_inert(envelope, "nothing_to_deliver")
        self.assertIn("base commit", envelope["error"]["detail"])
        self.assertIn("new work only", envelope["error"]["unhandled"]["explanation"])

    @verifies("scenario.delivery.nothing")
    def test_nothing_new_after_a_delivery(self):
        # Delivering again what was delivered reports the delivery commit and commits nothing.
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        self.commit_step()
        first = self.project.deliver()[1]
        self.assertEqual(first["status"], "ok", first)
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        self.assertEqual(envelope["output"], {**first["output"], "recovered": True})
        self.assertIn("already delivered", envelope["summary"])
        self.assertEqual(self.head(), first["output"]["commit"])
        self.assertEqual(len(self.project.deliveries()), 1)

    @verifies("scenario.delivery.commit-refused")
    def test_git_refuses_the_commit(self):
        hook = self.project.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho 'hook says no' >&2\nexit 1\n")
        hook.chmod(0o755)
        (self.worktree / "src/new.py").write_text("NEW = 1\n")
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        metadata = (self.worktree / "specs/a/module.md.json").read_bytes()
        before = (status_lines(self.worktree), git(self.worktree, "ls-files", "-s"))
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertIn("hook says no", evidence_of(envelope, "git")[-1]["detail"])
        self.assertEqual(["commit_failed", "git_failed"], codes(envelope["error"]))
        self.assertIn("hook says no", envelope["error"]["causes"][0]["detail"])
        self.assertEqual(self.head(), self.base)
        self.assertEqual(
            (self.worktree / "specs/a/module.md.json").read_bytes(), metadata
        )
        self.assertFalse((self.worktree / ".concorde/evidence").exists())
        self.assertEqual(
            (status_lines(self.worktree), git(self.worktree, "ls-files", "-s")), before
        )
        digest = self.saved_readiness(envelope)["inputs"]["digest"]
        self.assertEqual(measure(self.worktree, self.base)["digest"], digest)
        self.assertEqual(self.project.deliveries(), [])
        self.assertEqual(self.project.state(), "active")

    @verifies("scenario.delivery.recover")
    def test_a_delivery_interrupted_after_its_commit_needs_no_repair(self):
        (self.worktree / "src/new.py").write_text("NEW = 1\n")
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        self.validated()
        _, first = self.project.deliver()
        delivered = first["output"]
        self.assertEqual(delivered["confirmed"], ["src/new.py"])
        # The run ended after its commit without leaving its result: the commit alone records
        # the delivery.
        (
            self.project.root / ".concorde/runs" / first["run_id"] / "result.json"
        ).unlink()
        self.assertEqual(self.project.state(), "delivered")
        status, envelope = self.project.deliver()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        self.assertEqual(self.head(), delivered["commit"])
        self.assertEqual(
            envelope["output"],
            {**delivered, "confirmed": [], "recovered": True},
        )
        self.assertEqual(
            [d["commit"] for d in self.project.deliveries()], [delivered["commit"]]
        )
        self.assertEqual(status_lines(self.worktree), "")

    @verifies("scenario.delivery.unbound")
    def test_a_delivery_needs_a_bound_workspace(self):
        (self.project.root / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.run("delivery", cwd=self.project.root)
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertIsNone(envelope["workspace"])
        self.assertEqual(["refused", "binding_required"], codes(envelope["error"]))
        self.assertEqual("command", envelope["error"]["level"])
        self.assertEqual(
            git(self.project.root, "rev-parse", "HEAD"), self.project.base_commit
        )

    @verifies("scenario.delivery.adoption")
    def test_an_adoption_delivery_needs_no_scenario_test(self):
        obligations = self.worktree / "specs/a/obligations.md"
        obligations.write_text(
            obligations.read_text()
            + "\n### scenario.a.sum — A sums\n\n- GIVEN two numbers\n- WHEN A adds them\n"
            "- THEN it returns their sum\n"
        )
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        status, envelope = self.project.deliver("t1", "--adoption")
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        self.assertIn(
            "exempt", [item["ref"] for item in evidence_of(envelope, "scenario-tests")]
        )


class ContractTests(unittest.TestCase):
    def test_the_schemas_are_the_delivery_contracts(self):
        contracts = SpecRepository(REPOSITORY_ROOT).contract_nodes
        self.assertEqual(
            contracts["contract.delivery.evidence-bundle"]["schema"], BUNDLE_SCHEMA
        )
        self.assertEqual(contracts["contract.delivery.output"]["schema"], OUTPUT_SCHEMA)

    def test_delivery_is_a_recorded_command_of_a_bound_workspace(self):
        self.assertIs(DELIVERY.output_schema, OUTPUT_SCHEMA)
        self.assertEqual(
            ("command", "required", None, ()),
            (DELIVERY.kind, DELIVERY.binding, DELIVERY.task_type, DELIVERY.workers),
        )
        self.assertTrue(DELIVERY.writes)


if __name__ == "__main__":
    unittest.main()
