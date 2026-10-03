"""Partial installations: each installs some of Concorde's parts from this checkout into a fresh
Git project and exercises them through the installed ``.concorde/bin/concorde``.

Each also checks that the Framework copy holds the code of the installed parts alone and that the
guidance composed for the project holds the sections of the installed parts alone.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from concorde.distribution import parts
from concorde.distribution.install import install, update
from concorde.kernel import binding
from concorde.spec.verification import verifies
from tests.concorde.distribution.test_distribution import (
    fake_d2,
    fake_npm,
    package_copy,
    which,
)
from tests.concorde.spec_review.test_operation import FAKE_REVIEWER, finding, reviewer
from tests.concorde.support.operation_project import claude_workers

# What Distribution's own directory adds to the Framework copy's package beside the parts.
PACKAGE_FILES = {"__init__.py", "__main__.py"}


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def committed(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)


class PartialInstall(unittest.TestCase):
    """A fresh project and a built package to install some of the parts from."""

    def project(self, *files: tuple[str, str]) -> Path:
        self.package = package_copy(self)
        root = self.package.parent / "project"
        root.mkdir()
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.name", "Test")
        git(root, "config", "user.email", "test@example.com")
        for path, content in files or (("README.md", "# Project\n"),):
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(content)
        committed(root, "start")
        return root

    def install(self, root: Path, names: list[str], **options) -> dict:
        options = {"pi_runtime": False, "dependencies": False, **options}
        with which(**options.pop("programs", {})):
            return install(root, self.package, part_names=names, **options)

    def concorde(self, root: Path, *argv: str, cwd: Path | None = None, env=None):
        return subprocess.run(
            [str(root / ".concorde/bin/concorde"), *argv],
            cwd=cwd or root,
            capture_output=True,
            text=True,
            env={**os.environ, **(env or {})},
            timeout=600,
        )

    def answer(self, root: Path, *argv: str, cwd: Path | None = None, env=None):
        done = self.concorde(root, *argv, cwd=cwd, env=env)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        return json.loads(done.stdout)

    def assert_missing(self, root: Path, argv: tuple[str, ...], part: str) -> None:
        refused = self.concorde(root, *argv)
        self.assertEqual(1, refused.returncode, refused.stdout + refused.stderr)
        link = json.loads(refused.stdout)["error"]
        self.assertEqual("part_missing", link["code"], link)
        self.assertIn(f"the {part} part", link["detail"])

    def assert_only(self, root: Path, receipt: dict, expected: set[str]) -> None:
        """The receipt names exactly ``expected`` (and Distribution), and the project holds the
        code and the guidance of those parts alone."""
        expected = expected | {"distribution"}
        everything = parts.package_parts(self.package)
        version = parts.version(self.package)
        self.assertEqual({name: version for name in expected}, receipt["parts"])
        recorded = json.loads((root / ".concorde/install.json").read_text())
        self.assertEqual(receipt["parts"], recorded["parts"])
        code = root / ".concorde/framework/src/concorde"
        self.assertEqual(
            {everything[name].directory for name in expected} | PACKAGE_FILES,
            {path.name for path in code.iterdir()} - {"__pycache__"},
        )
        skill = (root / ".claude/skills/concorde/SKILL.md").read_text()
        block = (
            (root / "CLAUDE.md")
            .read_text()
            .split("<!-- concorde:start -->", 1)[1]
            .split("<!-- concorde:end -->", 1)[0]
        )
        for name, registration in everything.items():
            sections = registration.data["guidance"] or {}
            for kind, text in (("skill", skill), ("claude_md", block)):
                if sections.get(kind) is None:
                    continue
                section = (self.package / sections[kind]).read_text().strip()
                with self.subTest(part=name, kind=kind):
                    self.assertEqual(name in expected, section in text)
        prompt = root / ".concorde/framework/generated/guidance/task-session.md"
        self.assertEqual("coordination" in expected, prompt.is_file())
        ignored = (root / ".gitignore").read_text().splitlines()
        for name, registration in everything.items():
            own = set(registration.data["install"]["gitignore"]) - {
                line
                for other in expected
                for line in everything[other].data["install"]["gitignore"]
            }
            with self.subTest(part=name, ignored=sorted(own)):
                self.assertFalse(own & set(ignored))


class SpecAloneTests(PartialInstall):
    @verifies(
        "scenario.concorde.spec-alone",
        "scenario.distribution.update-installed-parts",
    )
    def test_the_spec_part_alone_checks_serves_and_publishes_specs(self):
        root = self.project(("app.py", "print('app')\n"))
        fetch = fake_d2(self, self.package)
        # A machine without npm: the pi runtime is the worker harness part's, not installed.
        receipt = self.install(root, ["spec"], pi_runtime=True, fetch=fetch)
        self.assert_only(root, receipt, {"spec"})
        self.assertEqual({"d2"}, set(receipt["tools"]))
        # No installed part needs a Python dependency.
        self.assertIsNone(receipt["dependencies"])
        self.assertTrue((root / ".concorde/protocol/manifest.json").is_file())
        self.assertFalse((root / ".claude/workflows").exists())
        proposal = self.package.parent / "proposal.json"
        proposed = self.answer(root, "init", "--propose", "--name", "App")
        proposal.write_text(json.dumps(proposed["result"]))
        self.answer(root, "init", "--apply", "--proposal", str(proposal))
        self.assertEqual("success", self.answer(root, "spec-validation")["status"])
        self.assertEqual("success", self.answer(root, "registry", "--check")["status"])
        granted = self.answer(
            root, "grant", "--modules", "module.project", "--type", "specify"
        )
        self.assertEqual("success", granted["status"], granted)
        docsite = self.answer(root, "docsite", "--propose")
        self.assertEqual("proposal", docsite["status"], docsite)
        for argv, part in (
            (("task", "list"), "coordination"),
            (("run", "spec_review"), "execution"),
            (("issues", "list"), "issues"),
            (("trace", "list"), "kernel"),
            (("task-validation",), "method"),
        ):
            with self.subTest(argv=argv):
                self.assert_missing(root, argv, part)
        committed(root, "describe the project")
        # The update installs the receipt's parts again, and no other.
        with which():
            updated = update(root, self.package)
        self.assertEqual({"spec", "distribution"}, set(updated["receipt"]["parts"]))
        self.assertEqual("unvalidated", updated["update"]["state"])
        # An update asked for the issues part brings the kernel it depends on too.
        with which():
            added = update(root, self.package, part_names=["issues"])
        self.assert_only(root, added["receipt"], {"spec", "issues", "kernel"})
        self.assertEqual([], self.answer(root, "issues", "list")["issues"])


class CoordinationAloneTests(PartialInstall):
    @verifies(
        "scenario.concorde.coordination-without-method",
        "scenario.distribution.install-parts",
        "scenario.distribution.update-without-spec",
    )
    def test_tasks_open_deliver_merge_and_close_without_method(self):
        root = self.project(("app.py", "print('app')\n"))
        fetch = fake_d2(self, self.package)
        receipt = self.install(root, ["coordination"], fetch=fetch)
        self.assert_only(root, receipt, {"coordination", "kernel"})
        # Neither d2 nor anything else of the spec part is placed.
        self.assertEqual([], fetch.urls)
        self.assertEqual({}, receipt["tools"])
        self.assertFalse((root / ".concorde/protocol").exists())
        committed(root, "install Concorde")
        opened = self.answer(
            root,
            "task",
            "open",
            "fix",
            "--goal",
            "Fix the app",
            "--modules",
            "module.app",
        )
        worktree = Path(opened["record"]["worktree"])
        (worktree / "app.py").write_text("print('fixed')\n")
        check = f"{sys.executable} -c pass"
        delivered = self.answer(
            root, "task", "deliver", "fix", "--check", check, cwd=worktree
        )
        self.assertEqual("delivered", delivered["record"]["state"], delivered)
        merged = self.answer(root, "task", "merge", "fix", "--check", check)
        self.assertEqual("closed", merged["record"]["state"], merged)
        self.assertEqual("print('fixed')\n", (root / "app.py").read_text())
        self.answer(
            root,
            "task",
            "open",
            "drop",
            "--goal",
            "Try something",
            "--modules",
            "module.app",
        )
        closed = self.answer(
            root, "task", "close", "drop", "--completed", "--note", "Nothing to change"
        )
        self.assertEqual("closed", closed["record"]["state"], closed)
        for argv, part in (
            (("spec-validation",), "spec"),
            (("run", "spec_review"), "execution"),
            (("issues", "list"), "issues"),
            (("delivery",), "method"),
        ):
            with self.subTest(argv=argv):
                self.assert_missing(root, argv, part)
        # Without the spec part an update waits for no validation.
        with which():
            updated = update(root, self.package)
        self.assertIsNone(updated["update"])
        self.assertEqual(["commit the updated files"], updated["next"])
        self.assertFalse((root / ".concorde/update.json").exists())
        self.assertEqual(
            {"coordination", "kernel", "distribution"}, set(updated["receipt"]["parts"])
        )


class IssuesAloneTests(PartialInstall):
    def test_issues_are_reported_listed_shown_closed_and_reopened(self):
        root = self.project()
        receipt = self.install(root, ["issues"], d2=False)
        self.assert_only(root, receipt, {"issues", "kernel"})
        committed(root, "install Concorde")
        report = self.package.parent / "report.json"
        report.write_text(
            json.dumps(
                {
                    "report_key": "slow-start",
                    "tier": "obvious-fix",
                    "severity": "low",
                    "type": "bug",
                    "subtype": None,
                    "title": "The app starts slowly",
                    "description": "Starting the app takes ten seconds.",
                    "impact": "Every start waits.",
                    "basis": "Timed by hand.",
                    "owner_target_id": "module.app",
                    "evidence": [{"path": "README.md", "description": "The project"}],
                }
            )
        )
        reported = self.answer(root, "issues", "report", "--file", str(report))
        issue = reported["receipt"]["issue_id"]
        self.assertEqual(
            [issue],
            [row["id"] for row in self.answer(root, "issues", "list")["issues"]],
        )
        shown = self.answer(root, "issues", "show", issue)
        self.assertEqual("open", shown["issue"]["status"])
        disposition = ("--note", "Fixed by hand.", "--evidence", "README.md")
        self.answer(
            root, "issues", "close", issue, "--reason", "resolved", *disposition
        )
        self.assertEqual(
            "closed", self.answer(root, "issues", "show", issue)["issue"]["status"]
        )
        self.answer(root, "issues", "reopen", issue, *disposition)
        self.assertEqual(
            "open", self.answer(root, "issues", "show", issue)["issue"]["status"]
        )
        self.assert_missing(root, ("task", "list"), "coordination")


class ExecutionWithoutMethodTests(PartialInstall):
    def test_no_operation_and_no_workflow_is_registered_without_method(self):
        root = self.project()
        receipt = self.install(root, ["workflow"], d2=False)
        self.assert_only(root, receipt, {"workflow", "execution", "kernel"})
        # No workflow of an installed part, so no workflow and no rule for its step agents.
        self.assertFalse((root / ".claude/workflows").exists())
        self.assertEqual([], receipt["permissions"])
        refused = self.concorde(root, "run", "spec_review")
        self.assertNotEqual(0, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn(
            "unknown operation 'spec_review'", refused.stdout + refused.stderr
        )
        self.assertNotIn("part_missing", refused.stdout)
        # A workspace prepared by hand, as Coordination would, for the workflow to run in.
        folder = root / ".concorde/workspaces/w1"
        folder.mkdir(parents=True)
        binding.write(
            root,
            {
                "schema_version": 2,
                "workspace": "w1",
                "root": str(root),
                "branch": "main",
                "base_commit": git(root, "rev-parse", "HEAD"),
                "goal": "Try a workflow",
                "modules": ["module.app"],
                "traces": str(folder),
                "concorde": str(root / ".concorde"),
            },
        )
        step = self.concorde(
            root,
            "workflow",
            "step",
            "--workflow",
            "brownfield",
            "--mode",
            "no-ask",
            "--key",
            "survey",
            "--wait",
            "1",
            "survey",
        )
        # The step's Operation is registered by no installed part, so its run cannot start.
        self.assertEqual(1, step.returncode, step.stdout + step.stderr)
        refusal = json.loads(step.stdout)
        self.assertEqual("refused", refusal["state"])
        self.assertEqual("step_refused", refusal["error"]["code"])
        self.assertIn("run survey", refusal["error"]["detail"])


class WorkerHarnessAloneTests(PartialInstall):
    def test_the_worker_configuration_and_model_map_refuse_without_method(self):
        root = self.project()
        calls = []
        receipt = self.install(
            root,
            ["worker harness"],
            d2=False,
            pi_runtime=True,
            run=fake_npm(calls),
            programs={"npm": "/usr/bin/npm"},
        )
        self.assert_only(root, receipt, {"worker harness", "kernel"})
        self.assertEqual({"pi-runtime"}, set(receipt["tools"]))
        framework = root / ".concorde/framework"
        python = str(framework / "python/bin/python")
        listed = subprocess.run(
            [python, str(framework / "scripts/available_models.py"), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, listed.returncode, listed.stderr)
        # The Framework copy's own code alone, on its own interpreter.
        probe = (
            "import json, sys\n"
            f"sys.path.insert(0, {str(framework / 'src')!r})\n"
            "from concorde.worker_harness import models\n"
            "declared = {'review': ['reviewer']}\n"
            "found = []\n"
            "def attempt(call):\n"
            "    try:\n"
            "        call()\n"
            "    except models.ModelConfigError as error:\n"
            "        found.append(error.code)\n"
            f"root = {str(root)!r}\n"
            "attempt(lambda: models.load(root, declared))\n"
            "config = {'schema_version': 2, 'enabled_models': {'astra': {}},\n"
            "          'default': {'model': 'astra', 'backend': 'claude'}}\n"
            f"absent = {{'CONCORDE_MODEL_MAP': {str(root / 'absent.json')!r}}}\n"
            "attempt(lambda: models.check_mapped(config, declared, absent))\n"
            f"mapped = {{'CONCORDE_MODEL_MAP': {str(root / 'models.json')!r}}}\n"
            f"open({str(root / 'models.json')!r}, 'w').write(json.dumps(\n"
            "    {'schema_version': 1, 'models': {'astra': {'pi': 'local/astra'}}}))\n"
            "attempt(lambda: models.check_mapped(config, declared, mapped))\n"
            "print(json.dumps(found))\n"
        )
        done = subprocess.run(
            [python, "-E", "-s", "-c", probe], capture_output=True, text=True
        )
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual(
            ["config_missing", "model_map_missing", "model_unmapped"],
            json.loads(done.stdout),
        )


class MethodWithoutIssuesTests(PartialInstall):
    @verifies("scenario.concorde.method-without-issues")
    def test_a_review_keeps_its_findings_without_the_issues_part(self):
        root = self.project(("app.py", "print('app')\n"))
        receipt = self.install(root, ["method"], fetch=fake_d2(self, self.package))
        self.assert_only(
            root,
            receipt,
            {"method", "spec", "worker harness", "execution", "workflow", "kernel"},
        )
        # Method's workflow comes with it, and the rules its step agents need.
        self.assertTrue((root / ".claude/workflows/concorde-brownfield.js").is_file())
        self.assertIn("mcp__concorde__workflow_step", receipt["permissions"])
        proposal = self.package.parent / "proposal.json"
        proposed = self.answer(root, "init", "--propose", "--name", "App")
        proposal.write_text(json.dumps(proposed["result"]))
        self.answer(root, "init", "--apply", "--proposal", str(proposal))
        committed(root, "install and describe the project")
        claude_workers(root)
        plans = json.dumps(
            {
                "reviewer module.project": reviewer(
                    finding("specs/project/module.md", module="module.project")
                )
            }
        )
        fake = self.package.parent / "claude"
        fake.write_text(
            f"#!/bin/sh\nFAKE_REVIEW_PLANS='{plans}' "
            f'exec "{sys.executable}" "{FAKE_REVIEWER}" "$@"\n'
        )
        fake.chmod(0o755)
        home = self.package.parent / "home"
        (home / ".claude").mkdir(parents=True)
        done = self.concorde(
            root,
            "run",
            "spec_review",
            "--modules",
            "module.project",
            env={"CONCORDE_CLAUDE": str(fake), "HOME": str(home)},
        )
        result = json.loads(done.stdout)
        self.assertEqual("ok", result["status"], done.stdout + done.stderr)
        (module,) = result["output"]["modules"]
        (kept,) = module["findings"]
        self.assertIsNone(kept["issue"])
        self.assertIn("issues part is not installed", done.stdout)
        self.assertFalse((root / ".concorde/issues").exists())


if __name__ == "__main__":
    unittest.main()
