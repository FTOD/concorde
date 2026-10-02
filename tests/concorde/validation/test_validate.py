"""The ``concorde task-validation`` execution command end to end on a fixture task."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.kernel.errors import codes
from concorde.execution.checks import checks as check_service
from concorde.execution.checks.check_executor import CheckSandboxError
from concorde.spec.repository import SpecRepository
from concorde.spec.verification import verifies
from concorde.method.validation.command import READINESS_SCHEMA, TASK_VALIDATION
from concorde.method.validation.measurement import measure
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import read_checks, write_checks
from tests.concorde.validation.project import (
    ValidationProject,
    evidence_of,
    git,
    run_folder,
    status_lines,
    workspace_run,
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
        self.assertNotIn("confirmations", readiness)
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
        # The run's node lies in the task's workspace folder; each check is a check node below
        # it, whose log the readiness names relative to the run's node.
        folder = workspace_run(self.project.root, envelope)
        self.assertEqual("checks/check.a/output.log", readiness["checks"][0]["log"])
        self.assertTrue((folder / readiness["checks"][0]["log"]).is_file())
        check_node = json.loads((folder / "checks/check.a/trace.json").read_text())
        self.assertEqual("check", check_node["kind"])
        saved = folder / "readiness.json"
        self.assertEqual(json.loads(saved.read_text()), readiness)
        self.assertEqual(snapshot(self.worktree), before)
        # An execution command of the bound workspace launches no worker.
        self.assertEqual(
            ("command", "task-validation", "t1", ["module.a"]),
            (
                envelope["kind"],
                envelope["name"],
                envelope["workspace"],
                envelope["modules"],
            ),
        )
        self.assertEqual(readiness["workspace"], "t1")
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
            ("command", "not_deliverable", "decision"),
            (error["level"], error["code"], error["unhandled"]["reason"]),
        )
        self.assertEqual(
            f"Command task-validation {envelope['run_id']} (workspace t1)",
            error["actor"],
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

    @verifies("scenario.validation.not-ready")
    def test_a_changed_glossary_is_accounted_like_a_spec_document(self):
        from tests.concorde.support.spec_project import upsert_concepts

        upsert_concepts(
            self.worktree,
            "specs/a/module.md",
            [
                {
                    "id": "concept.a.answer",
                    "title": "A answer",
                    "owner": "module.a",
                    "definition": "What A returns.",
                    "anchor": "realization.a.code",
                }
            ],
        )
        status, envelope = self.project.validate()
        unbound = [
            item["ref"]
            for item in envelope["output"]["blocking"]
            if item["kind"] == "unbound"
        ]
        self.assertNotIn("specs/glossary.json", unbound, envelope["output"])

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

    @verifies(
        "scenario.validation.submodule-content", "scenario.validation.submodule-commit"
    )
    def test_only_a_submodules_commit_is_measured(self):
        from concorde.method.validation.measurement import (
            changed_paths,
            has_uncommitted,
        )

        library = self.project.root.parent / "library"
        library.mkdir()

        def run(cwd, *argv):
            subprocess.run(
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

        run(library, "init", "-q")
        (library / "lib.py").write_text("VALUE = 1\n")
        run(library, "add", "lib.py")
        run(library, "commit", "-qm", "one")
        run(
            self.worktree,
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            "-q",
            str(library),
            "vendor/lib",
        )
        run(self.worktree, "commit", "-qm", "vendor")
        head = git(self.worktree, "rev-parse", "HEAD")
        submodule = self.worktree / "vendor/lib"
        (submodule / "lib.py").write_text("VALUE = 2\n")
        (submodule / "scratch.txt").write_text("x\n")
        self.assertEqual([], changed_paths(self.worktree, head))
        self.assertFalse(has_uncommitted(self.worktree))
        run(submodule, "commit", "-qam", "two")
        self.assertEqual(["vendor/lib"], changed_paths(self.worktree, head))
        self.assertTrue(has_uncommitted(self.worktree))

    @verifies("scenario.validation.sandbox-placeholder")
    def test_a_sandbox_placeholder_is_not_measured(self):
        from concorde.method.validation.measurement import (
            changed_paths,
            has_uncommitted,
            special_paths,
        )

        head = git(self.worktree, "rev-parse", "HEAD")
        placeholder = self.worktree / ".bashrc"
        placeholder.touch()
        placeholder.chmod(0o444)
        self.assertEqual([".bashrc"], special_paths(self.worktree))
        self.assertEqual([], changed_paths(self.worktree, head))
        self.assertFalse(has_uncommitted(self.worktree))

        (self.worktree / "src/a/calc.py").write_text(FIXED)
        notes = self.worktree / "notes"
        notes.mkdir()
        (notes / "empty.txt").touch()
        frozen = notes / "frozen.txt"
        frozen.write_text("kept\n")
        frozen.chmod(0o444)
        # A second link is not the sandbox's own placeholder either.
        linked = notes / "linked.txt"
        linked.touch()
        linked.chmod(0o444)
        (notes / "link.txt").hardlink_to(linked)
        readiness = self.project.validate()[1]["output"]
        self.assertEqual(
            [item["path"] for item in readiness["inputs"]["changed"]],
            [
                "notes/empty.txt",
                "notes/frozen.txt",
                "notes/link.txt",
                "notes/linked.txt",
                "src/a/calc.py",
            ],
        )
        unbound = [
            item["ref"] for item in readiness["blocking"] if item["kind"] == "unbound"
        ]
        self.assertNotIn(".bashrc", unbound)
        self.assertIn("notes/empty.txt", unbound)
        self.assertIn("notes/frozen.txt", unbound)

    @verifies("scenario.validation.mode-change")
    def test_a_changed_file_mode_changes_the_input_digest(self):
        calc = self.worktree / "src/a/calc.py"
        calc.write_text(FIXED)
        base = git(self.worktree, "rev-parse", "HEAD")
        before = measure(self.worktree, base)
        calc.chmod(calc.stat().st_mode | 0o100)
        after = measure(self.worktree, base)
        [was] = before["changed"]
        [now] = after["changed"]
        self.assertEqual(("100644", "100755"), (was["mode"], now["mode"]))
        self.assertEqual(was["digest"], now["digest"])
        self.assertNotEqual(before["digest"], after["digest"])

    @verifies("scenario.validation.checks-configuration")
    def test_a_changed_check_command_changes_the_configuration_digest(self):
        base = git(self.worktree, "rev-parse", "HEAD")
        before = measure(self.worktree, base)
        checks = read_checks(self.worktree)
        self.assertEqual(["module.a"], [check["module"] for check in checks])
        checks[0]["argv"] = [*checks[0]["argv"], "--again"]
        write_checks(self.worktree, checks)
        after = measure(self.worktree, base)
        self.assertNotEqual(before["config_digest"], after["config_digest"])
        self.assertNotEqual(before["digest"], after["digest"])

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

    @verifies("scenario.validation.inputs-changed")
    def test_a_worktree_changing_during_the_run_gets_no_readiness(self):
        original = check_service.run_checks

        def changing(*arguments, **options):
            (self.worktree / "src/a/calc.py").write_text("changed = True\n")
            return original(*arguments, **options)

        with patch("concorde.method.validation.command.run_checks", changing):
            status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "failed"))
        self.assertIsNone(envelope["output"])
        self.assertEqual(
            [item["ref"] for item in evidence_of(envelope, "readiness")][-1],
            "inputs_changed",
        )
        run_dir = workspace_run(self.project.root, envelope)
        self.assertTrue((run_dir / "trace.json").is_file())
        self.assertFalse((run_dir / "readiness.json").exists())
        self.assertEqual([], envelope["error"]["causes"])

        # A change while a check runs is noticed by Check execution, whose link is the cause.
        real = check_service.execute_check

        def racing(worktree, argv, **options):
            outcome = real(worktree, argv, **options)
            (self.worktree / "src/a/calc.py").write_text("raced = True\n")
            return outcome

        with patch.object(check_service, "execute_check", racing):
            status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "failed"))
        error = envelope["error"]
        self.assertEqual("inputs_changed", error["code"])
        [cause] = error["causes"]
        self.assertEqual(
            ("component", "Check execution", "stale_evidence", "environment"),
            (
                cause["level"],
                cause["actor"],
                cause["code"],
                cause["unhandled"]["reason"],
            ),
        )

    @verifies("scenario.validation.wrong-branch")
    def test_a_worktree_off_the_task_branch_fails_without_checks(self):
        git(self.worktree, "checkout", "-q", "--detach")
        status, envelope = self.project.validate()
        self.assertEqual((status, envelope["status"]), (1, "failed"))
        self.assertEqual(evidence_of(envelope, "git")[0]["ref"], "wrong_branch")
        self.assertEqual(evidence_of(envelope, "check"), [])
        run_dir = workspace_run(self.project.root, envelope)
        self.assertTrue((run_dir / "trace.json").is_file())
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
        [cause] = error["causes"]
        self.assertEqual(
            ("Check execution", "check_sandbox_unavailable"),
            (cause["actor"], cause["code"]),
        )
        self.assertIn("no namespaces here", cause["detail"])


class BindingTests(unittest.TestCase):
    @verifies("scenario.validation.unbound")
    def test_task_validation_needs_a_bound_workspace(self):
        project = ValidationProject(self)
        project.task()
        status, envelope = project.run("task-validation", cwd=project.root)
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertEqual((None, None), (envelope["workspace"], envelope["output"]))
        self.assertEqual(["refused", "binding_required"], codes(envelope["error"]))
        self.assertEqual("scope", envelope["error"]["unhandled"]["reason"])
        # A run whose binding was refused is kept with the unbound runs of the worktree it
        # started in.
        folder = run_folder(envelope)
        self.assertEqual(
            project.root / ".concorde/unbound" / envelope["run_id"], folder
        )
        self.assertTrue((folder / "result.json").is_file())

    def test_a_broken_binding_is_refused(self):
        project = ValidationProject(self)
        worktree = project.task()
        path = worktree / ".concorde/workspace.json"
        value = json.loads(path.read_text())
        path.write_text(json.dumps({**value, "root": str(project.root)}))
        status, envelope = project.validate()
        self.assertEqual((status, envelope["status"]), (1, "failed"), envelope)
        self.assertEqual(["refused", "binding_misplaced"], codes(envelope["error"]))
        path.write_text(json.dumps({**value, "modules": []}))
        status, envelope = project.validate()
        self.assertEqual(["refused", "binding_invalid"], codes(envelope["error"]))


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


class ContractTests(unittest.TestCase):
    def test_the_output_schema_is_the_readiness_contract(self):
        contract = SpecRepository(REPOSITORY_ROOT).contract_nodes[
            "contract.validation.readiness"
        ]
        self.assertEqual(contract["schema"], READINESS_SCHEMA)

    def test_task_validation_is_a_recorded_command_of_a_bound_workspace(self):
        self.assertIs(TASK_VALIDATION.output_schema, READINESS_SCHEMA)
        self.assertEqual(
            ("command", "required", None, ()),
            (
                TASK_VALIDATION.kind,
                TASK_VALIDATION.binding,
                TASK_VALIDATION.task_type,
                TASK_VALIDATION.workers,
            ),
        )
        self.assertFalse(TASK_VALIDATION.writes)


if __name__ == "__main__":
    unittest.main()
