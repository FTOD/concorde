"""Distribution: the build, the Protocol manifest and copy, the command line and the installer."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import tarfile
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from concorde.distribution.build import (
    BuildError,
    check_build,
    verify_fresh,
    write_build,
)
from concorde.distribution.install import InstallError, install
from concorde.distribution.tools import platform_key
from concorde.distribution.project_defaults import write_protocol_copy
from concorde.spec.repository_base import SpecError
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

COPIED = ("prompts", "protocol", "concorde.json", "src", "scripts")


def strict_frontmatter(test, text: str) -> dict:
    """The skill's frontmatter fields, each a bare name or a JSON string.

    Both forms are valid YAML for every parser, strict ones such as pi's included; a bare value
    holding ": " is not, and pi drops a skill whose frontmatter it cannot parse.
    """
    test.assertTrue(text.startswith("---\n"), text[:80])
    header = text[4:].split("\n---\n", 1)[0]
    fields = {}
    for line in header.splitlines():
        key, value = line.split(": ", 1)
        if value.startswith('"'):
            fields[key] = json.loads(value)
        else:
            test.assertRegex(value, r"^[a-z0-9-]+$", line)
            fields[key] = value
    return fields


def package_copy(test) -> Path:
    """A built copy of this package in a temporary directory."""
    directory = tempfile.TemporaryDirectory()
    test.addCleanup(directory.cleanup)
    root = Path(directory.name) / "package"
    root.mkdir()
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for name in COPIED:
        source = REPOSITORY_ROOT / name
        if source.is_dir():
            shutil.copytree(source, root / name, ignore=ignore)
        else:
            shutil.copy2(source, root / name)
    write_build(root)
    return root


FAKE_D2 = b"#!/bin/sh\necho fake d2\n"


def fake_d2(test, package: Path, *, corrupt: bool = False):
    """Pin a small d2 archive in ``package`` and return a fetch that serves it."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as bundle:
        info = tarfile.TarInfo("d2-v0.9.0/bin/d2")
        info.size = len(FAKE_D2)
        bundle.addfile(info, io.BytesIO(FAKE_D2))
    archive = buffer.getvalue()
    descriptor = json.loads((package / "concorde.json").read_text())
    descriptor["tools"]["d2"]["sha256"][platform_key()] = hashlib.sha256(
        archive
    ).hexdigest()
    (package / "concorde.json").write_text(json.dumps(descriptor, indent=2) + "\n")
    write_build(package)
    urls: list[str] = []

    def fetch(url: str) -> bytes:
        urls.append(url)
        return archive + (b"x" if corrupt else b"")

    fetch.urls = urls
    return fetch


def command(*argv, cwd=REPOSITORY_ROOT):
    return subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / "scripts/concorde.py"), *argv],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


class BuildTests(unittest.TestCase):
    @verifies("scenario.distribution.build-renders")
    def test_the_build_renders_every_prompt_root(self):
        root = package_copy(self)
        (root / "prompts/workers").mkdir(exist_ok=True)
        (root / "prompts/workers/common.md").write_text(
            "---\naudience: shared\n---\n\nShared rule.\n"
        )
        (root / "prompts/workers/probe.md").write_text(
            "---\naudience: worker\n---\n\nProbe.\n\n@prompts/workers/common.md\n"
        )
        (root / "prompts/workers/common.md").rename(root / "prompts/common.md")
        (root / "prompts/workers/probe.md").write_text(
            "---\naudience: worker\n---\n\nProbe.\n\nWrite {{python}}, "
            '{"a": {"b": 1}}.\n\n@prompts/common.md\n'
        )
        result = write_build(root)
        rendered = (root / "generated/workers/probe.md").read_text()
        self.assertIn("Probe.", rendered)
        # {{name}} is the literal {name}; other braces stay as they are.
        self.assertIn('Write {python}, {"a": {"b": 1}}.', rendered)
        self.assertIn("Shared rule.", rendered)
        manifest = json.loads((root / "generated/build-manifest.json").read_text())
        self.assertIn("prompts/common.md", manifest["sources"])
        self.assertIn("generated/workers/probe.md", manifest["outputs"])
        self.assertEqual(
            result.manifest, (root / "generated/build-manifest.json").read_bytes()
        )
        self.assertEqual((True, ()), check_build(root))

    @verifies("scenario.distribution.build-workflows")
    def test_the_build_renders_every_workflow_for_both_clients(self):
        root = package_copy(self)
        claude = (
            root / "generated/workflows/claude/concorde-brownfield.js"
        ).read_text()
        pi = (root / "generated/workflows/pi/brownfield.js").read_text()
        self.assertTrue(claude.startswith("export const meta = {"))
        self.assertIn('"name": "concorde-brownfield"', claude)
        procedure = (
            (root / "src/concorde/workflows/scripts/brownfield.js").read_text().strip()
        )
        self.assertIn(procedure, claude)
        self.assertIn(procedure, pi)
        self.assertIn("function step(key, argv)", pi)
        manifest = json.loads((root / "generated/build-manifest.json").read_text())
        for path in (
            "generated/workflows/claude/concorde-brownfield.js",
            "generated/workflows/pi/brownfield.js",
            "generated/workflows/pi/agents/concorde-step.md",
            "generated/workflows/pi/agents/concorde-report.md",
        ):
            self.assertIn(path, manifest["outputs"])
        self.assertIn(
            "src/concorde/workflows/scripts/brownfield.js", manifest["sources"]
        )
        script = root / "src/concorde/workflows/scripts/brownfield.js"
        script.write_text(script.read_text() + "\n// changed\n")
        ok, differences = check_build(root)
        self.assertFalse(ok)
        self.assertIn("generated/workflows/pi/brownfield.js", " ".join(differences))

    @verifies("scenario.distribution.build-check-stale")
    def test_a_stale_build_is_reported_without_writing(self):
        root = package_copy(self)
        path = root / "prompts/main-session/skill.md"
        path.write_text(path.read_text() + "\nOne more rule.\n")
        before = {
            item: item.read_bytes()
            for item in (root / "generated").rglob("*")
            if item.is_file()
        }
        current, differences = check_build(root)
        self.assertFalse(current)
        self.assertIn("generated/main-session/skill.md", differences)
        after = {
            item: item.read_bytes()
            for item in (root / "generated").rglob("*")
            if item.is_file()
        }
        self.assertEqual(before, after)
        with self.assertRaises(BuildError):
            verify_fresh(root)

    @verifies("scenario.distribution.build-refuses-unsafe")
    def test_an_unsafe_prompt_tree_is_refused(self):
        root = package_copy(self)
        orphan = root / "prompts/orphan.md"
        orphan.write_text("---\naudience: shared\n---\n\nNobody includes me.\n")
        before = (root / "generated/build-manifest.json").read_bytes()
        with self.assertRaises(BuildError) as raised:
            write_build(root)
        self.assertIn("unreachable", str(raised.exception))
        orphan.unlink()
        cycle = root / "prompts/main-session/skill.md"
        (root / "prompts/loop.md").write_text(
            "---\naudience: shared\n---\n\n@prompts/main-session/skill.md\n"
        )
        cycle.write_text(cycle.read_text() + "\n@prompts/loop.md\n")
        with self.assertRaises(BuildError):
            write_build(root)
        self.assertEqual(before, (root / "generated/build-manifest.json").read_bytes())

    @verifies("scenario.distribution.build-removes-own-leftover")
    def test_an_output_the_build_no_longer_produces_is_removed(self):
        root = package_copy(self)
        (root / "prompts/workers").mkdir(exist_ok=True)
        (root / "prompts/workers/gone.md").write_text(
            "---\naudience: worker\n---\n\nGone.\n"
        )
        write_build(root)
        self.assertTrue((root / "generated/workers/gone.md").exists())
        (root / "prompts/workers/gone.md").unlink()
        write_build(root)
        self.assertFalse((root / "generated/workers/gone.md").exists())
        (root / "prompts/workers/edited.md").write_text(
            "---\naudience: worker\n---\n\nEdited.\n"
        )
        write_build(root)
        (root / "prompts/workers/edited.md").unlink()
        (root / "generated/workers/edited.md").write_text("changed by hand\n")
        with self.assertRaises(BuildError):
            write_build(root)
        self.assertEqual(
            "changed by hand\n", (root / "generated/workers/edited.md").read_text()
        )


class ProtocolTests(unittest.TestCase):
    @verifies("scenario.distribution.protocol-manifest-bind")
    def test_a_changed_protocol_is_accepted_explicitly(self):
        root = package_copy(self)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        (root / ".concorde").mkdir()
        shutil.copy2(
            REPOSITORY_ROOT / ".concorde/config.json", root / ".concorde/config.json"
        )
        chapter = root / "protocol/views.md"
        chapter.write_text(chapter.read_text() + "\nAn added sentence.\n")
        write_build(root)
        report = command("--project-root", str(root), "protocol-manifest")
        self.assertEqual(1, report.returncode)
        self.assertIn("generated/protocol/principles.md", report.stdout)
        bound = command(
            "--project-root",
            str(root),
            "protocol-manifest",
            "--write",
            "--bind-project",
        )
        self.assertEqual(0, bound.returncode, bound.stdout)
        config = json.loads((root / ".concorde/config.json").read_text())
        manifest = (root / "protocol/manifest.json").read_bytes()
        import hashlib

        self.assertEqual(
            "sha256:" + hashlib.sha256(manifest).hexdigest(),
            config["protocol"]["digest"],
        )
        self.assertIn(
            "An added sentence.",
            (root / ".concorde/protocol/principles.md").read_text(),
        )

    @verifies("scenario.distribution.stale-copy-refused")
    def test_a_stale_build_is_never_copied(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        write_protocol_copy(project, package)
        before = (project / ".concorde/protocol/principles.md").read_bytes()
        chapter = package / "protocol/views.md"
        chapter.write_text(chapter.read_text() + "\nStale.\n")
        with self.assertRaises(SpecError):
            write_protocol_copy(project, package)
        self.assertEqual(
            before, (project / ".concorde/protocol/principles.md").read_bytes()
        )


class CommandLineTests(unittest.TestCase):
    @verifies("scenario.distribution.refused-command-line")
    def test_a_refused_command_line_answers_with_one_envelope(self):
        for argv in (
            ("validate", "--bogus"),
            ("grant", "--type", "test"),
            ("frobnicate",),
        ):
            with self.subTest(argv=argv):
                result = command(*argv)
                self.assertNotEqual(0, result.returncode)
                envelope = json.loads(result.stdout)
                self.assertEqual("failed", envelope["status"])


class RoutingTests(unittest.TestCase):
    def test_task_run_and_issues_are_routed_to_their_owners(self):
        listed = command("issues", "list")
        self.assertEqual(0, listed.returncode, listed.stdout)
        self.assertIn("issues", json.loads(listed.stdout))
        self.assertEqual(2, command("run", "frobnicate", "--task", "t").returncode)
        self.assertEqual(2, command("task", "frobnicate").returncode)


class InstallTests(unittest.TestCase):
    @verifies("scenario.distribution.install")
    def test_install_places_concorde_without_touching_specs(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        (project / "CLAUDE.md").write_text("# My project\n\nKeep this.\n")
        fetch = fake_d2(self, package)
        receipt = install(project, package, fetch=fetch)
        self.assertTrue((project / ".concorde/protocol/manifest.json").exists())
        self.assertTrue(
            (project / ".concorde/framework/src/concorde/spec/grants.py").exists()
        )
        self.assertTrue(
            (project / ".concorde/framework/generated/main-session/skill.md").exists()
        )
        # End-to-end testing serves Concorde's developers only.
        self.assertFalse((project / ".concorde/framework/scripts/e2e").exists())
        skill = (project / ".claude/skills/concorde/SKILL.md").read_text()
        fields = strict_frontmatter(self, skill)
        self.assertEqual("concorde", fields["name"])
        self.assertIn("Concorde's main agent", fields["description"])
        self.assertIn("Concorde main agent", skill)
        claude = (project / "CLAUDE.md").read_text()
        self.assertIn("Keep this.", claude)
        self.assertEqual(1, claude.count("<!-- concorde:start -->"))
        self.assertIn(".concorde/runs/", (project / ".gitignore").read_text())
        self.assertIn(".claude/worktrees/", (project / ".gitignore").read_text())
        self.assertIn(
            ".concorde/worker-models.json", (project / ".gitignore").read_text()
        )
        self.assertFalse((project / ".concorde/config.json").exists())
        self.assertFalse((project / ".concorde/specs.json").exists())
        self.assertFalse((project / "specs").exists())
        # The pinned d2 is placed, recorded in the receipt and kept out of version control.
        d2 = project / ".concorde/tools/d2"
        self.assertEqual(FAKE_D2, d2.read_bytes())
        self.assertTrue(d2.stat().st_mode & 0o111)
        self.assertEqual(".concorde/tools/d2", receipt["tools"]["d2"]["path"])
        self.assertIn(".concorde/tools/", (project / ".gitignore").read_text())
        self.assertIn(f"-{platform_key()}.tar.gz", fetch.urls[0])
        install(project, package, fetch=fetch)
        # The same pin is not downloaded again.
        self.assertEqual(1, len(fetch.urls))
        self.assertEqual(
            1, (project / "CLAUDE.md").read_text().count("<!-- concorde:start -->")
        )
        self.assertIn(".claude/skills/concorde/SKILL.md", receipt["files"])
        proposed = subprocess.run(
            [
                str(project / ".concorde/bin/concorde"),
                "init",
                "--propose",
                "--name",
                "Demo",
            ],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proposed.returncode, proposed.stdout + proposed.stderr)
        # Outside the project: a file written into it would change what was proposed.
        proposal = package.parent / "proposal.json"
        proposal.write_text(json.dumps(json.loads(proposed.stdout)["result"]))
        applied = subprocess.run(
            [
                str(project / ".concorde/bin/concorde"),
                "init",
                "--apply",
                "--proposal",
                str(proposal),
            ],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, applied.returncode, applied.stdout)
        valid = subprocess.run(
            [str(project / ".concorde/bin/concorde"), "validate"],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual("success", json.loads(valid.stdout)["status"], valid.stdout)

    @verifies("scenario.distribution.own-python")
    def test_concorde_runs_in_its_own_python_whatever_the_caller_uses(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        receipt = install(project, package, d2=False)
        self.assertEqual(".concorde/framework/python", receipt["python"]["environment"])
        self.assertEqual(sys.executable, receipt["python"]["base"])
        self.assertTrue((project / ".concorde/framework/python/bin/python").exists())
        caller = package.parent / "caller"
        (caller / "bin").mkdir(parents=True)
        (caller / "bin/python3").write_text("#!/bin/sh\nexit 42\n")
        (caller / "bin/python3").chmod(0o755)
        (caller / "shadow/concorde").mkdir(parents=True)
        (caller / "shadow/concorde/__init__.py").write_text("raise SystemExit(43)\n")
        environment = {
            **os.environ,
            "PATH": f"{caller / 'bin'}{os.pathsep}{os.environ['PATH']}",
            "PYTHONPATH": str(caller / "shadow"),
        }
        listed = subprocess.run(
            [str(project / ".concorde/bin/concorde"), "task", "list"],
            cwd=project,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, listed.returncode, listed.stdout + listed.stderr)
        self.assertEqual([], json.loads(listed.stdout))
        old = caller / "old-python"
        old.write_text('#!/bin/sh\necho "3 9 1"\n')
        old.chmod(0o755)
        with self.assertRaises(InstallError) as raised:
            install(project, package, d2=False, python=old)
        self.assertEqual("python_too_old", raised.exception.code)

    @verifies("scenario.distribution.task-worktree-command")
    def test_the_command_of_a_task_worktree_runs_the_primary_framework(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, d2=False)

        def git(*argv):
            subprocess.run(
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv],
                cwd=project,
                check=True,
                capture_output=True,
            )

        git("add", "-A")
        git("commit", "-qm", "install")
        worktree = project / ".claude/worktrees/t1"
        git("worktree", "add", "-q", "-b", "concorde/t1", str(worktree))
        self.assertFalse((worktree / ".concorde/framework").exists())
        listed = subprocess.run(
            [str(worktree / ".concorde/bin/concorde"), "task", "list"],
            cwd=worktree,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, listed.returncode, listed.stdout + listed.stderr)
        self.assertEqual([], json.loads(listed.stdout))

    @verifies("scenario.distribution.install")
    @verifies("scenario.distribution.install-pi")
    def test_install_with_pi_places_the_locked_runtime_extension_and_skill(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        calls = []

        def fake_npm(command, cwd, **options):
            calls.append((command, Path(cwd)))
            entry = (
                Path(cwd) / "node_modules/@anthropic-ai/sandbox-runtime/dist/index.js"
            )
            entry.parent.mkdir(parents=True)
            entry.write_text("export {};\n")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch(
            "concorde.distribution.tools.shutil.which", return_value="/usr/bin/npm"
        ):
            receipt = install(project, package, d2=False, pi=True, run=fake_npm)
            install(project, package, d2=False, pi=True, run=fake_npm)
        [(command, cwd)] = calls
        self.assertEqual(["/usr/bin/npm", "ci", "--ignore-scripts"], command[:3])
        self.assertEqual(project / ".concorde/tools/pi-runtime", cwd)
        self.assertEqual(
            (
                package / "src/concorde/distribution/pi_runtime/package-lock.json"
            ).read_bytes(),
            (cwd / "package-lock.json").read_bytes(),
        )
        placed = receipt["tools"]["pi-runtime"]
        self.assertEqual(
            ("@anthropic-ai/sandbox-runtime", "0.0.77"),
            (placed["package"], placed["version"]),
        )
        extension = project / ".pi/extensions/concorde"
        self.assertIn("concorde_run", (extension / "index.ts").read_text())
        self.assertTrue((extension / "pi_runs.ts").is_file())
        self.assertTrue((extension / "pi_models.ts").is_file())
        self.assertIn(
            "concorde_configure_workers", (extension / "index.ts").read_text()
        )
        skill = (project / ".pi/skills/concorde/SKILL.md").read_text()
        self.assertEqual({"name", "description"}, set(strict_frontmatter(self, skill)))
        self.assertIn(".pi/extensions/concorde/index.ts", receipt["files"])

    @verifies("scenario.distribution.install")
    @verifies("scenario.distribution.install-settings-kept")
    def test_install_places_workflows_and_only_its_own_permission_rules(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        settings = project / ".claude/settings.json"
        settings.parent.mkdir(parents=True)
        mine = "Bash(.concorde/bin/concorde workflow report:*)"
        settings.write_text(
            json.dumps({"model": "x", "permissions": {"allow": ["Bash(ls:*)", mine]}})
        )
        receipt = install(project, package, d2=False)
        workflow = project / ".claude/workflows/concorde-brownfield.js"
        self.assertTrue(workflow.read_text().startswith("export const meta = {"))
        self.assertIn(".claude/workflows/concorde-brownfield.js", receipt["files"])
        self.assertFalse((project / ".pi/agents").exists())
        value = json.loads(settings.read_text())
        self.assertEqual("x", value["model"])
        allow = value["permissions"]["allow"]
        self.assertEqual(["Bash(ls:*)", mine], allow[:2])
        self.assertIn("Workflow(concorde-brownfield)", allow)
        self.assertIn("Bash(.concorde/bin/concorde workflow step:*)", allow)
        self.assertEqual(1, allow.count(mine))
        # The developer's own rule was there first, so Concorde does not own it.
        self.assertNotIn(mine, receipt["permissions"])
        # A rule Concorde recorded and no longer ships is removed; the developer's rules stay.
        recorded = json.loads((project / ".concorde/install.json").read_text())
        recorded["permissions"].append("Workflow(concorde-retired)")
        (project / ".concorde/install.json").write_text(json.dumps(recorded))
        value["permissions"]["allow"].append("Workflow(concorde-retired)")
        settings.write_text(json.dumps(value))
        install(project, package, d2=False)
        # A later install still records the defaults the first one wrote, and the files it
        # only amends apart from the ones it owns.
        again = json.loads((project / ".concorde/install.json").read_text())
        self.assertIn(".concorde/issues/.gitignore", again["files"])
        self.assertIn("CLAUDE.md", again["amended"])
        self.assertNotIn("CLAUDE.md", again["files"])
        allow = json.loads(settings.read_text())["permissions"]["allow"]
        self.assertNotIn("Workflow(concorde-retired)", allow)
        self.assertIn("Bash(ls:*)", allow)
        self.assertIn(mine, allow)
        # Settings that are not a JSON object are refused before anything is written.
        settings.write_text("[1, 2]")
        (project / ".claude/workflows/concorde-brownfield.js").unlink()
        with self.assertRaises(InstallError) as raised:
            install(project, package, d2=False)
        self.assertEqual("settings_invalid", raised.exception.code)
        self.assertFalse(
            (project / ".claude/workflows/concorde-brownfield.js").exists()
        )

    @verifies("scenario.distribution.install-pi")
    def test_install_with_pi_places_workflow_scripts_and_agents(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)

        def fake_npm(command, cwd, **options):
            entry = (
                Path(cwd) / "node_modules/@anthropic-ai/sandbox-runtime/dist/index.js"
            )
            entry.parent.mkdir(parents=True)
            entry.write_text("export {};\n")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch(
            "concorde.distribution.tools.shutil.which", return_value="/usr/bin/npm"
        ):
            receipt = install(project, package, d2=False, pi=True, run=fake_npm)
        self.assertIn(
            "runs.run", (project / ".concorde/workflows/pi/brownfield.js").read_text()
        )
        for name in ("concorde-step", "concorde-report"):
            agent = (project / f".pi/agents/{name}.md").read_text()
            self.assertIn("type: external-cli", agent)
            self.assertIn(f".pi/agents/{name}.md", receipt["files"])

    def test_install_with_pi_without_npm_installs_nothing(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        with patch("concorde.distribution.tools.shutil.which", return_value=None):
            with self.assertRaises(InstallError) as raised:
                install(project, package, d2=False, pi=True)
        self.assertEqual("npm_missing", raised.exception.code)
        self.assertFalse((project / ".concorde/framework").exists())

    def test_install_refuses_stale_guidance(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        (package / "prompts/main-session/skill.md").write_text(
            (package / "prompts/main-session/skill.md").read_text() + "\nNew.\n"
        )
        with self.assertRaises(InstallError) as raised:
            install(project, package)
        self.assertEqual("stale_build", raised.exception.code)
        self.assertFalse((project / ".claude").exists())


class D2InstallTests(unittest.TestCase):
    @verifies("scenario.distribution.install-d2-refused")
    def test_a_d2_archive_that_does_not_match_its_pin_installs_nothing(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        with self.assertRaises(InstallError) as raised:
            install(project, package, fetch=fake_d2(self, package, corrupt=True))
        self.assertEqual("d2_digest_mismatch", raised.exception.code)
        self.assertIn("but concorde.json pins", str(raised.exception))
        self.assertEqual([], list(project.iterdir()))

    @verifies("scenario.distribution.install-d2-refused")
    def test_an_unreachable_d2_release_is_reported_with_its_url(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()

        def offline(url: str) -> bytes:
            raise OSError("network is unreachable")

        with self.assertRaises(InstallError) as raised:
            install(project, package, fetch=offline)
        self.assertEqual("d2_unavailable", raised.exception.code)
        self.assertIn(
            "github.com/d2lang/d2/releases/download/v0.9.0", str(raised.exception)
        )
        self.assertIn("network is unreachable", str(raised.exception))
        self.assertEqual([], list(project.iterdir()))

    @verifies("scenario.distribution.install-d2-refused")
    def test_install_without_d2_leaves_the_program_to_the_developer(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        receipt = install(project, package, d2=False)
        self.assertEqual({}, receipt["tools"])
        self.assertFalse((project / ".concorde/tools").exists())

    def test_every_supported_platform_has_a_pinned_archive(self):
        descriptor = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        self.assertEqual(
            {
                f"{system}-{machine}"
                for system in ("linux", "macos", "windows")
                for machine in ("amd64", "arm64")
            },
            set(descriptor["tools"]["d2"]["sha256"]),
        )
        self.assertEqual("linux-arm64", platform_key("Linux", "aarch64"))
        self.assertEqual("macos-amd64", platform_key("Darwin", "x86_64"))


if __name__ == "__main__":
    unittest.main()
