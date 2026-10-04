"""Develop installs from a Concorde repository, their guidance and the repository's own rules."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from concorde.distribution.build import build
from concorde.distribution.install import InstallError, install, update
from concorde.distribution.prompt_resolver import resolve_role_prompt
from concorde.dogfooding.develop import DevelopError, develop_source
from concorde.issues.shapes import REPORT
from concorde.issues.store import validate_report
from concorde.kernel.errors import link
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
        receipt = install(
            project,
            package,
            pi_runtime=False,
            d2=False,
            develop=True,
            dependencies=False,
        )
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
        receipt = install(
            project, package, pi_runtime=False, d2=False, dependencies=False
        )
        self.assertEqual("normal", receipt["mode"])
        self.assertEqual(git(package, "rev-parse", "HEAD"), receipt["source_commit"])
        self.assertNotIn(
            "Developing Concorde",
            (project / ".claude/skills/concorde/SKILL.md").read_text(),
        )
        self.assertNotIn("develop install", (project / "CLAUDE.md").read_text())

    def assert_refused(self, source: Path, project: Path, code: str, *fragments: str):
        """A develop install from ``source`` is refused with ``code`` and writes nothing."""
        with self.assertRaises(InstallError) as raised:
            install(
                project,
                source,
                pi_runtime=False,
                d2=False,
                develop=True,
                dependencies=False,
            )
        self.assertEqual(code, raised.exception.code)
        for fragment in fragments:
            self.assertIn(fragment, str(raised.exception))
        self.assertEqual([".git"], [p.name for p in project.iterdir()])

    @verifies("scenario.dogfooding.refused-source")
    def test_a_linked_worktree_is_not_installed_from(self):
        package = repository(self)
        linked = package.parent / "linked"
        git(package, "worktree", "add", "-q", "-b", "task", str(linked))
        write_build(linked)
        self.assert_refused(
            linked,
            new_project(package),
            "develop_source_not_primary",
            str(package),
        )
        # A linked worktree that is also detached is refused by the first check it fails.
        detached = package.parent / "detached"
        git(package, "worktree", "add", "-q", "--detach", str(detached))
        write_build(detached)
        self.assert_refused(
            detached,
            new_project(package, "project-detached"),
            "develop_source_not_primary",
            str(package),
        )

    def test_a_source_path_with_spaces_is_read_whole(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory())) / "with  spaces"
        source = root / "concorde repo"
        source.mkdir(parents=True)
        git(source, "init", "-q", "-b", "main")
        git(source, "commit", "-q", "--allow-empty", "-m", "concorde")
        self.assertEqual(
            {
                "repository": str(source.resolve()),
                "branch": "main",
                "commit": git(source, "rev-parse", "HEAD"),
            },
            develop_source(source),
        )
        linked = root / "linked worktree"
        git(source, "worktree", "add", "-q", "-b", "task", str(linked))
        with self.assertRaises(DevelopError) as raised:
            develop_source(linked)
        self.assertEqual("develop_source_not_primary", raised.exception.code)
        self.assertIn(f"primary worktree is {source.resolve()};", str(raised.exception))

    @verifies("scenario.dogfooding.refused-source")
    def test_a_linked_worktree_refusal_of_a_separate_git_dir_names_what_git_records(
        self,
    ):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        work = root / "work"
        git(root, "init", "-q", "-b", "main", "--separate-git-dir", "meta.git", "work")
        git(work, "commit", "-q", "--allow-empty", "-m", "concorde")
        linked = root / "linked"
        git(work, "worktree", "add", "-q", "-b", "task", str(linked))
        with self.assertRaises(DevelopError) as raised:
            develop_source(linked)
        self.assertEqual("develop_source_not_primary", raised.exception.code)
        # Git records no path for the primary worktree here, so the refusal says where its
        # Git directory is instead of naming the directory around it.
        self.assertIn(
            f"Git directory is {(root / 'meta.git').resolve()}, which records no path",
            str(raised.exception),
        )
        git(work, "config", "core.worktree", "../work")
        with self.assertRaises(DevelopError) as raised:
            develop_source(linked)
        self.assertIn(f"primary worktree is {work.resolve()};", str(raised.exception))

    @verifies("scenario.dogfooding.refused-not-root")
    def test_a_checkout_that_is_no_worktree_root_is_not_installed_from(self):
        # A built package copy outside any Git repository.
        outside = package_copy(self)
        self.assert_refused(
            outside,
            new_project(outside),
            "develop_source_not_repository",
            "not in a Git worktree",
        )
        # A built package copy committed inside a larger repository's worktree.
        inside = package_copy(self)
        git(inside.parent, "init", "-q", "-b", "main")
        git(inside.parent, "add", "-A")
        git(inside.parent, "commit", "-qm", "outer")
        self.assert_refused(
            inside,
            new_project(inside),
            "develop_source_not_repository",
            f"inside the worktree {inside.parent}",
        )

    @verifies("scenario.dogfooding.refused-detached")
    def test_a_detached_primary_worktree_is_not_installed_from(self):
        package = repository(self)
        git(package, "checkout", "-q", "--detach")
        self.assert_refused(
            package, new_project(package), "develop_source_detached", "detached"
        )

    @verifies("scenario.dogfooding.refused-dirty")
    def test_a_primary_worktree_with_changes_is_not_installed_from(self):
        package = repository(self)
        (package / "stray.txt").write_text("uncommitted\n")
        self.assert_refused(
            package, new_project(package), "develop_source_dirty", "stray.txt"
        )

    @verifies("scenario.dogfooding.update-keeps-develop")
    def test_an_update_installs_the_new_commit_in_develop_mode(self):
        package = repository(self)
        project = new_project(package)
        first = install(
            project,
            package,
            pi_runtime=False,
            d2=False,
            develop=True,
            dependencies=False,
        )
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

    @verifies("scenario.dogfooding.develop-install-without-coordination")
    def test_a_develop_install_of_some_parts_keeps_them_on_update(self):
        package = repository(self)
        project = new_project(package)
        first = install(
            project,
            package,
            part_names=["issues"],
            pi_runtime=False,
            d2=False,
            develop=True,
            dependencies=False,
        )
        self.assertEqual({"distribution", "issues", "kernel"}, set(first["parts"]))
        self.assertEqual(git(package, "rev-parse", "HEAD"), first["source_commit"])
        # Without Coordination the develop section would name tasks the project cannot open.
        self.assertNotIn(
            SECTION, (project / ".claude/skills/concorde/SKILL.md").read_text()
        )
        self.assertNotIn(
            "This is a develop install", (project / "CLAUDE.md").read_text()
        )
        report = update(project, package)
        self.assertEqual("develop", report["receipt"]["mode"])
        self.assertEqual(first["parts"], report["receipt"]["parts"])
        self.assertNotIn(
            SECTION, (project / ".claude/skills/concorde/SKILL.md").read_text()
        )
        both = update(project, package, part_names=["coordination"])["receipt"]
        self.assertEqual("develop", both["mode"])
        self.assertIn(
            SECTION, (project / ".claude/skills/concorde/SKILL.md").read_text()
        )

    @verifies("scenario.dogfooding.update-dirty-source")
    def test_an_update_from_a_dirty_repository_changes_nothing(self):
        package = repository(self)
        project = new_project(package)
        install(
            project,
            package,
            pi_runtime=False,
            d2=False,
            develop=True,
            dependencies=False,
        )
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
            # Execution commands such as delivery are runs too, apart from Operations.
            "Observe every run of an Operation or execution command, every workflow and every "
            "worker run closely",
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
            "while no run of an Operation or execution command, workflow or task session is "
            "running, run `concorde update`: it refuses while such a run is still running",
            "Start nothing until the update ends",
            # A run that ended ok reported no error: the link alone is the whole chain, built by
            # task escalate naming no run in a task and written by hand outside one.
            "When the run ended `ok` and still did something wrong",
            "run the same command without `--run`, with a `--detail` that names the run",
            "your link, with no causes, is the whole chain",
            "Without a task, write your link by hand, in the shape of the error contract",
            "citing the run and what shows the fault",
            "and none when the run ended `ok`",
            # Outside a task the report stays in the run store and no task is opened.
            "A defect you saw outside a task",
            "opens no task: keep its report only under `.concorde/runs/defects/`",
            "name that file to the developer",
            # A defect of the Issue system travels as its error chain, never as an Issue report.
            "A defect of the Issue system itself** is never written as a defect report",
            "`concorde issues report --check` refusing a correct report among them",
            "A refusal whose reason is `environment`, such as `merge_busy`, is no defect",
            "Hand such a defect over as its error chain alone, with your own link on top",
            "`.concorde/runs/defects/<name>.error.json`",
            "never as a report to record as an Issue",
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
        # The checkout's instructions tell every session to load the development skill, which
        # the build renders.
        self.assertIn(
            "`concorde-development`", (REPOSITORY_ROOT / "CLAUDE.md").read_text()
        )
        outputs = {
            output.path: output.content for output in build(REPOSITORY_ROOT).outputs
        }
        instructions = words(
            outputs["generated/skills/concorde-development/SKILL.md"].decode()
        )
        for fragment in (
            "## Defect reports from develop installs",
            "python3 scripts/issues.py report --file <report>",
            "--resolves <issue>",
            "Fix a Concorde implementation bug",
            (
                "escalate to the developer before changing Concorde's design or Protocol or "
                "loosening any boundary"
            ),
            "`--reason not-actionable`",
            "Fix the defect generally, never only for the reporting project",
            "append a report to the recorded Issue naming the Module at fault as its "
            "`owner_target_id`",
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
