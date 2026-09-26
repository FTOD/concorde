"""Develop installs from a Concorde repository, their guidance and the repository's own rules."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

from concorde.distribution.install import InstallError, install, update
from concorde.distribution.prompt_resolver import resolve_role_prompt
from concorde.errors import link
from concorde.issues.shapes import REPORT
from concorde.issues.store import validate_report
from concorde.spec.verification import verifies
from tests.concorde.distribution.test_distribution import package_copy, write_build
from tests.concorde.support.paths import REPOSITORY_ROOT

SECTION = "## Developing Concorde while using it"


def git(root: Path, *argv: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def repository(test) -> Path:
    """A built package copy committed as the primary worktree of a Concorde repository."""
    package = package_copy(test)
    (package / ".gitignore").write_text("generated/\n__pycache__/\n")
    git(package, "init", "-q", "-b", "main")
    git(package, "add", "-A")
    git(package, "commit", "-qm", "concorde")
    return package


def new_project(package: Path, name: str = "project") -> Path:
    project = package.parent / name
    project.mkdir()
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    return project


def words(text: str) -> str:
    return " ".join(text.split())


class DevelopInstallTests(unittest.TestCase):
    @verifies("scenario.dogfooding.develop-install")
    def test_a_develop_install_records_its_source_and_carries_the_guidance(self):
        package = repository(self)
        project = new_project(package)
        receipt = install(project, package, d2=False, develop=True)
        self.assertEqual("develop", receipt["mode"])
        self.assertEqual(str(package), receipt["source"])
        self.assertEqual(git(package, "rev-parse", "HEAD"), receipt["source_commit"])
        skill = (project / ".claude/skills/concorde/SKILL.md").read_text()
        self.assertIn("# Concorde main agent", skill)
        self.assertIn(SECTION, skill)
        self.assertLess(skill.index("## Report"), skill.index(SECTION))
        claude = (project / "CLAUDE.md").read_text()
        block = claude.split("<!-- concorde:start -->")[1].split(
            "<!-- concorde:end -->"
        )[0]
        self.assertIn("This is a develop install", block)
        # The framework is still a copy, so task worktrees behave as in a normal install.
        self.assertTrue((project / ".concorde/framework/scripts/concorde.py").is_file())
        self.assertIn(".concorde/framework/", (project / ".gitignore").read_text())

    @verifies("scenario.dogfooding.normal-install")
    def test_a_normal_install_carries_no_develop_guidance(self):
        package = repository(self)
        project = new_project(package)
        receipt = install(project, package, d2=False)
        self.assertEqual("normal", receipt["mode"])
        self.assertEqual(git(package, "rev-parse", "HEAD"), receipt["source_commit"])
        self.assertNotIn(
            "Developing Concorde",
            (project / ".claude/skills/concorde/SKILL.md").read_text(),
        )
        self.assertNotIn("develop install", (project / "CLAUDE.md").read_text())

    @verifies("scenario.dogfooding.refused-source")
    def test_only_a_clean_primary_worktree_on_a_branch_is_installed_from(self):
        package = repository(self)
        linked = package.parent / "linked"
        git(package, "worktree", "add", "-q", "-b", "task", str(linked))
        write_build(linked)
        (package / "stray.txt").write_text("uncommitted\n")
        cases = [
            (linked, "develop_source_not_primary", [str(package)]),
            (package, "develop_source_dirty", ["stray.txt"]),
        ]
        detached = package.parent / "detached"
        git(package, "worktree", "add", "-q", "--detach", str(detached))
        write_build(detached)
        cases.append((detached, "develop_source_not_primary", [str(package)]))
        for index, (source, code, fragments) in enumerate(cases):
            with self.subTest(code=code, source=source.name):
                project = new_project(package, f"project-{index}")
                with self.assertRaises(InstallError) as raised:
                    install(project, source, d2=False, develop=True)
                self.assertEqual(code, raised.exception.code)
                for fragment in fragments:
                    self.assertIn(fragment, str(raised.exception))
                self.assertEqual([".git"], [p.name for p in project.iterdir()])
        (package / "stray.txt").unlink()
        git(package, "checkout", "-q", "--detach")
        project = new_project(package, "project-detached")
        with self.assertRaises(InstallError) as raised:
            install(project, package, d2=False, develop=True)
        self.assertEqual("develop_source_detached", raised.exception.code)
        self.assertEqual([".git"], [p.name for p in project.iterdir()])

    @verifies("scenario.dogfooding.update-keeps-develop")
    def test_an_update_installs_the_new_commit_in_develop_mode(self):
        package = repository(self)
        project = new_project(package)
        first = install(project, package, d2=False, develop=True)
        (package / "NOTE.md").write_text("A fix merged into the primary branch.\n")
        git(package, "add", "NOTE.md")
        git(package, "commit", "-qm", "fix")
        report = update(project, package)
        receipt = report["receipt"]
        self.assertEqual("develop", receipt["mode"])
        self.assertNotEqual(first["source_commit"], receipt["source_commit"])
        self.assertEqual(git(package, "rev-parse", "HEAD"), receipt["source_commit"])
        self.assertEqual(
            {"from": first["source_commit"], "to": receipt["source_commit"]},
            report["update"]["commits"],
        )
        self.assertIn(
            SECTION, (project / ".claude/skills/concorde/SKILL.md").read_text()
        )

    @verifies("scenario.dogfooding.update-dirty-source")
    def test_an_update_from_a_dirty_repository_changes_nothing(self):
        package = repository(self)
        project = new_project(package)
        install(project, package, d2=False, develop=True)
        receipt = (project / ".concorde/install.json").read_bytes()
        marker = project / ".concorde/framework/scripts/concorde.py"
        before = marker.stat().st_mtime_ns
        (package / "src/concorde/half_done.py").write_text("# not committed\n")
        with self.assertRaises(InstallError) as raised:
            update(project, package)
        self.assertEqual("develop_source_dirty", raised.exception.code)
        self.assertIn("src/", str(raised.exception))
        self.assertEqual(receipt, (project / ".concorde/install.json").read_bytes())
        self.assertEqual(before, marker.stat().st_mtime_ns)
        self.assertFalse((project / ".concorde/update.json").exists())


class GuidanceTests(unittest.TestCase):
    def setUp(self):
        self.skill = words(
            resolve_role_prompt(REPOSITORY_ROOT, "prompts/dogfooding/skill.md").body
        )

    @verifies("scenario.dogfooding.guidance")
    def test_the_guidance_says_how_to_watch_classify_and_report(self):
        for fragment in (
            "Observe every Operation, workflow and worker run closely",
            "can end `ok` and still be wrong",
            "Do not edit the Concorde repository, the framework copy under `.concorde/framework/`",
            "Do not work around a Concorde defect",
            "The boundary is right; the work overreaches",
            "This project's Specs draw the boundary wrongly",
            "Concorde implements the boundary wrongly",
            "Concorde's design blocks a correct boundary",
            "the Spec text and Protocol rule the boundary is derived from",
            "the grant actually computed",
            "the refused action with its message",
            "Never settle a blocked boundary by only loosening it",
            "`.concorde/runs/defects/<report_key>.json`",
            "`owner_target_id`: `null`",
            "`origin`:",
            "`error_chain`: the whole error chain of the failure, unchanged, with your own link on top",
            "concorde task escalate <task> --code concorde_defect",
            "`report_key`: a short kebab-case name of the defect",
            "`subtype`: `null` for a bug or a limitation",
            "concorde issues report --check --file <path>",
            "run `concorde update`",
        ):
            self.assertIn(words(fragment), self.skill)
        # The example is a complete Issue report: only its shortened chain stands in.
        body = resolve_role_prompt(REPOSITORY_ROOT, "prompts/dogfooding/skill.md").body
        example = json.loads(body.split("```json\n", 1)[1].split("```", 1)[0])
        self.assertEqual(
            set(REPORT["required"]) | {"origin", "error_chain"}, set(example)
        )
        example["error_chain"] = link(
            "main-agent",
            "main agent (task add-field)",
            "concorde_defect",
            "the write hook refused src/app/models.py",
            reason="scope",
            explanation="the fix lies in the Concorde repository",
        )
        validate_report(example)
        # The four cases form one table with where each goes and who decides.
        rows = [line for line in self.skill.split(" | ") if "type `" in line]
        self.assertTrue(any("`bug`" in row for row in rows))
        self.assertTrue(any("`limitation`" in row for row in rows))


class ConcordeRepositoryTests(unittest.TestCase):
    @verifies("scenario.dogfooding.concorde-instructions")
    def test_the_repository_instructions_take_reports_and_share_the_observation_rule(
        self,
    ):
        for entry in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(entry=entry):
                self.assertIn(
                    "Read [DEVELOPING.md](DEVELOPING.md) in full",
                    words((REPOSITORY_ROOT / entry).read_text()),
                )
        instructions = words((REPOSITORY_ROOT / "DEVELOPING.md").read_text())
        for fragment in (
            "## Defect reports from develop installs",
            "python3 scripts/issues.py report --file <report> --task <task>",
            "Fix a Concorde implementation bug",
            "ask the developer before changing Concorde's design or Protocol or loosening any boundary",
            "`--reason not-actionable`",
            "Fix the defect generally, never only for the reporting project",
        ):
            self.assertIn(words(fragment), instructions)
        rule = words(
            resolve_role_prompt(
                REPOSITORY_ROOT, "prompts/dogfooding/common/observe-runs.md"
            ).body
        )
        self.assertTrue(rule)
        self.assertIn(rule, instructions)
        self.assertIn(
            rule,
            words(
                resolve_role_prompt(REPOSITORY_ROOT, "prompts/dogfooding/skill.md").body
            ),
        )
        self.assertIsNone(re.search(r"\{\{|\}\}", rule))
