"""The ``validate`` Operation end to end on a fixture task, and the confirmation service."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness import checks as check_service
from concorde.harness.check_executor import CheckSandboxError
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from concorde.validation import confirmations
from concorde.validation.measurement import measure
from concorde.validation.operation import READINESS_SCHEMA, VALIDATE
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.validation.project import (
    ValidationProject,
    evidence_of,
    git,
    status_lines,
)

FIXED = "def add(a, b):\n    return a + b\n"
BROKEN_LINK = "\nSee [the missing scenario](module.md#scenario.a.missing).\n"


def snapshot(worktree: Path) -> tuple:
    files = {
        path.relative_to(worktree).as_posix(): path.read_bytes()
        for path in sorted(worktree.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(worktree).parts
    }
    return (
        files,
        git(worktree, "rev-parse", "HEAD"),
        git(worktree, "symbolic-ref", "HEAD"),
        status_lines(worktree),
        git(worktree, "ls-files", "-s"),
    )


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.project = ValidationProject(self)
        self.worktree = self.project.task()

    @verifies("scenario.validation.ready")
    def test_a_complete_task_is_ready(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        before = snapshot(self.worktree)
        status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (0, "ok"), envelope)
        readiness = envelope["output"]
        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["blocking"], [])
        self.assertEqual(
            readiness["inputs"], measure(self.worktree, readiness["inputs"]["base"])
        )
        self.assertEqual(
            [item["path"] for item in readiness["inputs"]["changed"]], ["src/a/calc.py"]
        )
        self.assertEqual(
            [(c["check"], c["module"], c["status"]) for c in readiness["checks"]],
            [("check.a", "module.a", "passed")],
        )
        log = self.project.root / readiness["checks"][0]["log"]
        self.assertTrue(log.is_file())
        saved = (
            self.project.root / ".concorde/runs" / envelope["run_id"] / "readiness.json"
        )
        self.assertEqual(json.loads(saved.read_text()), readiness)
        self.assertEqual(snapshot(self.worktree), before)
        # A deterministic Operation launches no worker (scenario.operations.deterministic).
        self.assertIsNone(envelope["worker"])
        self.assertEqual(envelope["worker_runs"], [])
        # Validating the unchanged worktree again gives the same readiness.
        again = self.project.validate()[1]["output"]
        self.assertEqual(again["inputs"]["digest"], readiness["inputs"]["digest"])
        self.assertEqual(again["ready"], True)

    @verifies("scenario.validation.not-ready")
    def test_every_blocker_is_reported_in_one_run(self):
        module = self.worktree / "specs/a/module.md"
        module.write_text(module.read_text() + BROKEN_LINK)
        (self.worktree / "stray.txt").write_text("unbound\n")
        (self.worktree / "src/a/flag").write_text("broken")
        status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "blocked"), envelope)
        readiness = envelope["output"]
        self.assertFalse(readiness["ready"])
        # Every blocking reason is named, with its location, as a cause of the error.
        error = envelope["error"]
        self.assertEqual(
            ("not_deliverable", "decision"),
            (error["code"], error["unhandled"]["reason"]),
        )
        self.assertEqual(len(readiness["blocking"]), len(error["causes"]))
        for item, cause in zip(readiness["blocking"], error["causes"]):
            self.assertIn(item["ref"], cause["detail"] + cause["actor"])
        check = next(cause for cause in error["causes"] if cause["level"] == "check")
        self.assertIn("exit code 1", check["detail"])
        self.assertIn("Not deliverable: 3 blocking finding(s)", envelope["summary"])
        kinds = {item["kind"] for item in readiness["blocking"]}
        self.assertEqual(
            kinds, {"structural", "unbound", "check"}, readiness["blocking"]
        )
        self.assertIn(
            {"kind": "unbound", "ref": "stray.txt"},
            [{"kind": i["kind"], "ref": i["ref"]} for i in readiness["blocking"]],
        )
        self.assertIn("check.a", [i["ref"] for i in readiness["blocking"]])
        self.assertEqual(readiness["checks"][0]["status"], "failed")

    @verifies("scenario.validation.submodule-reference")
    def test_a_submodule_a_module_includes_is_accounted(self):
        from tests.concorde.support.spec_project import include_external

        (self.worktree / "src/a/calc.py").write_text(FIXED)
        include_external(self.worktree, "module.a", "vendor/lib/docs/")
        for path in ("vendor/lib", "vendor/other"):
            subprocess.run(
                [
                    "git",
                    "update-index",
                    "--add",
                    "--cacheinfo",
                    f"160000,{'a' * 40},{path}",
                ],
                cwd=self.worktree,
                check=True,
            )
            (self.worktree / path).mkdir(parents=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=t",
                "-c",
                "user.email=t@t",
                "commit",
                "-qam",
                "vendor",
            ],
            cwd=self.worktree,
            check=True,
        )
        readiness = self.project.validate()[1]["output"]
        unbound = [
            item["ref"] for item in readiness["blocking"] if item["kind"] == "unbound"
        ]
        self.assertNotIn("vendor/lib", unbound)
        self.assertIn("vendor/other", unbound)

    @verifies("scenario.validation.warnings")
    def test_warnings_do_not_block(self):
        (self.worktree / "src/a/calc.py").write_text(FIXED)
        readiness = self.project.validate()[1]["output"]
        self.assertTrue(readiness["ready"])
        self.assertIn(
            "CONCORDE-COVERAGE-001",
            " ".join(item["ref"] for item in readiness["warnings"]),
        )
        self.assertEqual(
            {item["kind"] for item in readiness["warnings"]}, {"structural"}
        )

    @verifies("scenario.validation.unloadable")
    def test_specs_that_cannot_be_loaded_are_not_ready(self):
        (self.worktree / ".concorde/specs.json").write_text("{")
        status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "blocked"), envelope)
        readiness = envelope["output"]
        self.assertFalse(readiness["ready"])
        [load] = [item for item in readiness["blocking"] if item["kind"] == "load"]
        [cause] = envelope["error"]["causes"]
        # Spec tooling's own error arrives with its code, location, reason and remediation.
        self.assertEqual(
            ("component", "unsupported_profile"), (cause["level"], cause["code"])
        )
        self.assertIn("registry is not JSON", cause["detail"])
        self.assertIn(".concorde/specs.json", cause["detail"])
        self.assertIn("strict JSON", cause["unhandled"]["explanation"])
        self.assertIn("restore it from Git", cause["recommendation"])
        self.assertIn("why:", load["detail"])
        self.assertTrue(load["detail"])
        self.assertEqual(readiness["checks"], [])

    @verifies("scenario.validation.confirmation")
    def test_a_filled_pending_entry_becomes_a_confirmation(self):
        (self.worktree / "src/new.py").write_text("NEW = 1\n")
        readiness = self.project.validate()[1]["output"]
        self.assertTrue(readiness["ready"], readiness["blocking"])
        metadata = self.worktree / "specs/a/module.md.json"
        self.assertEqual(
            readiness["confirmations"],
            [
                {
                    "module": "module.a",
                    "realization": "realization.a.new",
                    "entry": "src/new.py",
                    "metadata": "specs/a/module.md.json",
                    "metadata_digest": SpecRepository(self.worktree)
                    .units["specs/a/module.md"]
                    .metadata.digest,
                }
            ],
        )
        self.assertIn('"src/new.py"', metadata.read_text())  # nothing was cleared yet

    @verifies("scenario.validation.inputs-changed")
    def test_a_worktree_changing_during_the_run_gets_no_readiness(self):
        original = check_service.run_checks

        def changing(*arguments, **options):
            (self.worktree / "src/a/calc.py").write_text("changed = True\n")
            return original(*arguments, **options)

        with patch("concorde.validation.operation.run_checks", changing):
            status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "failed"))
        self.assertIsNone(envelope["output"])
        self.assertEqual(
            [item["ref"] for item in evidence_of(envelope, "readiness")][-1],
            "inputs_changed",
        )
        run_dir = self.project.root / ".concorde/runs" / envelope["run_id"]
        self.assertFalse((run_dir / "readiness.json").exists())

    @verifies("scenario.validation.wrong-branch")
    def test_a_worktree_off_the_task_branch_fails_without_checks(self):
        git(self.worktree, "checkout", "-q", "--detach")
        status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "failed"))
        self.assertEqual(evidence_of(envelope, "git")[0]["ref"], "wrong_branch")
        self.assertEqual(evidence_of(envelope, "check"), [])
        run_dir = self.project.root / ".concorde/runs" / envelope["run_id"]
        self.assertFalse((run_dir / "checks").exists())

    @verifies("scenario.validation.sandbox-unavailable")
    def test_checks_that_cannot_be_bounded_fail_the_run(self):
        def unavailable(*arguments, **options):
            raise CheckSandboxError("no namespaces here")

        with patch.object(check_service, "execute_check", unavailable):
            status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "failed"))
        self.assertIsNone(envelope["output"])
        self.assertEqual(
            [item["ref"] for item in evidence_of(envelope, "checks_unavailable")],
            ["check_sandbox_unavailable"],
        )
        error = envelope["error"]
        self.assertEqual(
            ("checks_unavailable", "environment"),
            (error["code"], error["unhandled"]["reason"]),
        )
        self.assertIn("no namespaces here", error["causes"][0]["detail"])


class SharedFileTests(unittest.TestCase):
    @verifies("scenario.validation.shared-file")
    def test_a_shared_file_runs_every_binders_checks(self):
        project = ValidationProject(self, shared=True)
        worktree = project.task()
        (worktree / "src/shared.py").write_text("SHARED = 2\n")
        readiness = project.validate()[1]["output"]
        self.assertTrue(readiness["ready"], readiness["blocking"])
        self.assertEqual(readiness["modules"], ["module.a", "module.b"])
        self.assertEqual(
            sorted(item["check"] for item in readiness["checks"]),
            ["check.a", "check.b"],
        )


class ConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.project = ValidationProject(self)
        self.worktree = self.project.task()
        (self.worktree / "src/new.py").write_text("NEW = 1\n")
        self.readiness = self.project.validate()[1]["output"]
        self.metadata = self.worktree / "specs/a/module.md.json"

    def pending(self) -> dict:
        value = json.loads(self.metadata.read_text())
        return {
            item["id"]: item.get("pending", [])
            for item in value["defines"]
            if item["type"] == "realization"
        }

    @verifies("scenario.validation.confirm")
    def test_confirmations_are_applied_exactly(self):
        before = self.metadata.read_bytes()
        backups = confirmations.apply(self.worktree, self.readiness["confirmations"])
        self.assertEqual(backups, {"specs/a/module.md.json": before})
        self.assertEqual(
            self.pending(), {"realization.a.code": [], "realization.a.new": []}
        )
        from concorde.spec.validation import validate_repository

        errors = [
            f
            for f in validate_repository(self.worktree).findings
            if f.severity == "error"
        ]
        self.assertEqual(errors, [])
        self.assertEqual(
            sorted(line[3:] for line in status_lines(self.worktree).splitlines()),
            ["specs/a/module.md.json", "src/new.py"],
        )

    @verifies("scenario.validation.confirm-refused")
    def test_a_changed_document_stops_confirmation(self):
        value = json.loads(self.metadata.read_text())
        value["extensions"] = {"note": "changed"}
        self.metadata.write_text(json.dumps(value, indent=2) + "\n")
        changed = self.metadata.read_bytes()
        with self.assertRaises(confirmations.ConfirmationRefused) as refused:
            confirmations.apply(self.worktree, self.readiness["confirmations"])
        self.assertEqual(refused.exception.code, "stale_confirmation")
        self.assertEqual(self.metadata.read_bytes(), changed)

    @verifies("scenario.validation.confirm-refused")
    def test_a_structural_error_after_confirmation_rolls_back(self):
        other = self.worktree / "specs/b/module.md"
        other.write_text(other.read_text() + BROKEN_LINK)
        before = self.metadata.read_bytes()
        with self.assertRaises(confirmations.ConfirmationRefused) as refused:
            confirmations.apply(self.worktree, self.readiness["confirmations"])
        self.assertEqual(refused.exception.code, "invalid_after_confirmation")
        self.assertEqual(self.metadata.read_bytes(), before)


class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_readiness_contract(self):
        contract = SpecRepository(REPOSITORY_ROOT).contract_nodes[
            "contract.validation.readiness"
        ]
        self.assertEqual(contract["schema"], READINESS_SCHEMA)
        self.assertIs(VALIDATE.output_schema, READINESS_SCHEMA)
        self.assertIsNone(VALIDATE.task_type)
        self.assertFalse(VALIDATE.writes)


if __name__ == "__main__":
    unittest.main()
