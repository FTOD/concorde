"""Distribution: the build, the Protocol manifest and copy, the command line and the installer."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import tarfile
import subprocess
import sys
import tempfile
import unittest
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
            "---\naudience: worker\n---\n\nProbe.\n\n@prompts/common.md\n"
        )
        result = write_build(root)
        rendered = (root / "generated/workers/probe.md").read_text()
        self.assertIn("Probe.", rendered)
        self.assertIn("Shared rule.", rendered)
        manifest = json.loads((root / "generated/build-manifest.json").read_text())
        self.assertIn("prompts/common.md", manifest["sources"])
        self.assertIn("generated/workers/probe.md", manifest["outputs"])
        self.assertEqual(
            result.manifest, (root / "generated/build-manifest.json").read_bytes()
        )
        self.assertEqual((True, ()), check_build(root))

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
        skill = (project / ".claude/skills/concorde/SKILL.md").read_text()
        self.assertTrue(skill.startswith("---\nname: concorde\n"))
        self.assertIn("Concorde main agent", skill)
        claude = (project / "CLAUDE.md").read_text()
        self.assertIn("Keep this.", claude)
        self.assertEqual(1, claude.count("<!-- concorde:start -->"))
        self.assertIn(".concorde/runs/", (project / ".gitignore").read_text())
        self.assertIn(".claude/worktrees/", (project / ".gitignore").read_text())
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
