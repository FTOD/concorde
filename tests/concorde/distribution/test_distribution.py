"""Distribution: the build, the Protocol manifest and copy, the command line and the installer."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.distribution.build import (
    BuildError,
    check_build,
    verify_fresh,
    write_build,
)
from concorde.distribution import guidance, parts
from concorde.distribution.install import InstallError, install, refusal, update
from concorde.distribution.project_defaults import CopyError, write_protocol_copy
from concorde.spec.views.docsite_template import DocsiteTemplateError
from concorde.distribution.tools import platform_key
from concorde.kernel.errors import ERROR_SCHEMA
from concorde.execution.runs import Store, run_lock
from concorde.spec.initialize import apply_project_proposal, project_proposal
from concorde.spec.repository_base import SpecError
from concorde.spec.schema import ContractError, validate
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from concorde.spec.views.docsite_template import adapter_files, template_files
from tests.concorde.support.paths import REPOSITORY_ROOT

COPIED = (
    "prompts",
    "protocol",
    "concorde.json",
    "src",
    "scripts",
    "pyproject.toml",
    "uv.lock",
)


def strict_frontmatter(test, text: str) -> dict:
    """The skill's frontmatter fields, each a bare name or a JSON string.

    Both forms are valid YAML for every parser, strict ones included; a bare value holding ": "
    is not, and a skill reader drops a skill whose frontmatter it cannot parse.
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


# The real uv, which creates Concorde's own environment in every install these tests make.
UV = shutil.which("uv")


def contract_schema(identity: str) -> dict:
    """The schema of one of Distribution's contracts, read from its Spec."""
    text = (REPOSITORY_ROOT / "specs/concorde/distribution/contracts.md").read_text()
    for fence in re.findall(r"```concorde-contract\n(.*?)\n```", text, re.DOTALL):
        body = json.loads(fence)
        if body["id"] == identity:
            return body["schema"]
    raise AssertionError(f"{identity} is not in Distribution's contracts")


def which(**found):
    """A stand-in for ``shutil.which`` that finds the real uv and the programs named here."""
    programs = {"uv": UV, **found}
    return patch("shutil.which", side_effect=lambda name: programs.get(name))


def fake_npm(calls: list):
    """A stand-in for ``npm ci`` that places the runtime's entry and records each call."""

    def run(command, cwd, **options):
        calls.append((command, Path(cwd)))
        entry = Path(cwd) / "node_modules/@anthropic-ai/sandbox-runtime/dist/index.js"
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("export {};\n")
        return subprocess.CompletedProcess(command, 0, "", "")

    return run


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
    # The docsite template exactly as Views inventories it, without a working site's installs.
    for path, content in template_files(REPOSITORY_ROOT).items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(content)
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

    class Fetch:
        def __init__(self):
            self.urls: list[str] = []

        def __call__(self, url: str) -> bytes:
            self.urls.append(url)
            return archive + (b"x" if corrupt else b"")

    return Fetch()


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

    @verifies("scenario.distribution.build-skills")
    def test_the_build_renders_every_skill_with_its_front_matter(self):
        root = package_copy(self)
        write_build(root)
        manifest = json.loads((root / "generated/build-manifest.json").read_text())
        everything = parts.package_parts(root)

        def composed(kind):
            return (
                "\n\n".join(
                    (root / path).read_text().strip("\n")
                    for path in guidance.sections(everything, kind)
                )
                + "\n"
            )

        # Coordination's working method first, then the other parts in the parts table's order.
        self.assertEqual(
            [
                "generated/main-session/skill.md",
                "generated/guidance/spec/skill.md",
                "generated/guidance/kernel/skill.md",
                "generated/guidance/worker_harness/skill.md",
                "generated/guidance/execution/skill.md",
                "generated/guidance/workflows/skill.md",
                "generated/guidance/issues/skill.md",
                "generated/guidance/method/skill.md",
                "generated/guidance/distribution/skill.md",
            ],
            guidance.sections(everything, "skill"),
        )
        for name, body in (
            ("concorde", composed("skill")),
            (
                "concorde-development",
                (root / "generated/development/skill.md").read_text(),
            ),
        ):
            with self.subTest(skill=name):
                skill = (root / f"generated/skills/{name}/SKILL.md").read_text()
                fields = strict_frontmatter(self, skill)
                self.assertEqual(name, fields["name"])
                self.assertTrue(fields["description"])
                self.assertIn('description: "', skill)
                self.assertTrue(skill.endswith("---\n\n" + body))
                self.assertIn(f"generated/skills/{name}/SKILL.md", manifest["outputs"])
        self.assertEqual(
            composed("task_session"),
            (root / guidance.TASK_SESSION).read_text(),
        )
        self.assertTrue(
            (root / guidance.TASK_SESSION)
            .read_text()
            .startswith("# Concorde task session")
        )
        self.assertIn(guidance.TASK_SESSION, manifest["outputs"])

    @verifies("scenario.distribution.composed-guidance")
    def test_the_guidance_is_composed_of_the_given_parts_alone(self):
        everything = parts.package_parts(REPOSITORY_ROOT)
        # Each section stands for itself, so the composition's order and content show.
        read = lambda path: f"<{path}>\n"  # noqa: E731

        def of(names):
            chosen = {name: everything[name] for name in names}
            return {
                kind: guidance.compose(chosen, kind, read)
                for kind in parts.GUIDANCE_FIELDS
            }

        three = of(["distribution", "spec", "coordination"])
        self.assertTrue(
            three["skill"].endswith(
                "<generated/main-session/skill.md>\n\n<generated/guidance/spec/skill.md>"
                "\n\n<generated/guidance/distribution/skill.md>\n"
            )
        )
        self.assertIn(
            "Concorde's main agent",
            strict_frontmatter(self, three["skill"])["description"],
        )
        self.assertEqual(
            "<generated/main-session/task-session.md>\n\n"
            "<generated/guidance/spec/task-session.md>\n",
            three["task_session"],
        )
        self.assertEqual(
            "<generated/main-session/claude-md.md>\n\n<generated/guidance/spec/claude-md.md>"
            "\n\n<generated/guidance/distribution/claude-md.md>\n",
            three["claude_md"],
        )
        self.assertNotIn("issues", "".join(three.values()))

    @verifies("scenario.distribution.composed-guidance-without-coordination")
    def test_the_guidance_without_coordination_is_the_given_sections_alone(self):
        everything = parts.package_parts(REPOSITORY_ROOT)
        read = lambda path: f"<{path}>\n"  # noqa: E731
        chosen = {name: everything[name] for name in ("spec", "distribution")}
        alone = {
            kind: guidance.compose(chosen, kind, read) for kind in parts.GUIDANCE_FIELDS
        }
        fields = strict_frontmatter(self, alone["skill"])
        self.assertEqual("concorde", fields["name"])
        self.assertNotIn("main agent", fields["description"])
        self.assertTrue(
            alone["skill"].endswith(
                "---\n\n<generated/guidance/spec/skill.md>\n\n"
                "<generated/guidance/distribution/skill.md>\n"
            )
        )
        self.assertEqual(
            "<generated/guidance/spec/claude-md.md>\n\n"
            "<generated/guidance/distribution/claude-md.md>\n",
            alone["claude_md"],
        )
        self.assertIsNone(alone["task_session"])

    @verifies("scenario.distribution.build-workflows")
    def test_the_build_renders_every_workflow_for_claude_code(self):
        root = package_copy(self)
        claude = (
            root / "generated/workflows/claude/concorde-brownfield.js"
        ).read_text()
        self.assertTrue(claude.startswith("export const meta = {"))
        self.assertIn('"name": "concorde-brownfield"', claude)
        procedure = (
            (root / "src/concorde/method/brownfield/brownfield.js").read_text().strip()
        )
        self.assertIn(procedure, claude)
        self.assertIn("function step(key, argv)", claude)
        manifest = json.loads((root / "generated/build-manifest.json").read_text())
        workflows = sorted(
            path
            for path in manifest["outputs"]
            if path.startswith("generated/workflows/")
        )
        self.assertEqual(
            ["generated/workflows/claude/concorde-brownfield.js"], workflows
        )
        self.assertFalse((root / "generated/workflows/pi").exists())
        self.assertIn(
            "src/concorde/method/brownfield/brownfield.js", manifest["sources"]
        )
        script = root / "src/concorde/method/brownfield/brownfield.js"
        script.write_text(script.read_text() + "\n// changed\n")
        ok, differences = check_build(root)
        self.assertFalse(ok)
        self.assertIn(
            "generated/workflows/claude/concorde-brownfield.js", " ".join(differences)
        )

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

    @verifies("scenario.distribution.build-refuses-repeated-include")
    def test_a_prompt_reached_twice_is_refused(self):
        root = package_copy(self)
        before = (root / "generated/build-manifest.json").read_bytes()
        prompts = root / "prompts"
        for name, body in (
            ("left.md", "@prompts/shared-part.md SIDE=left\n"),
            ("right.md", "@prompts/shared-part.md SIDE=right\n"),
            ("shared-part.md", "The {SIDE} side.\n"),
        ):
            (prompts / name).write_text("---\naudience: shared\n---\n\n" + body)
        skill = prompts / "main-session/skill.md"
        skill.write_text(
            skill.read_text() + "\n@prompts/left.md\n\n@prompts/right.md\n"
        )
        with self.assertRaises(BuildError) as raised:
            write_build(root)
        message = str(raised.exception)
        self.assertIn("prompts/shared-part.md is reached twice", message)
        self.assertIn(
            "prompts/main-session/skill.md -> prompts/left.md -> prompts/shared-part.md",
            message,
        )
        self.assertIn(
            "prompts/main-session/skill.md -> prompts/right.md -> prompts/shared-part.md",
            message,
        )
        self.assertEqual(before, (root / "generated/build-manifest.json").read_bytes())

    @verifies(
        "scenario.distribution.build-removes-own-leftover",
        "scenario.distribution.build-keeps-edited-leftover",
    )
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
        with self.assertRaises(BuildError) as raised:
            write_build(root)
        self.assertIn("generated/workers/edited.md", str(raised.exception))
        self.assertEqual(
            "changed by hand\n", (root / "generated/workers/edited.md").read_text()
        )


class ProtocolTests(unittest.TestCase):
    @verifies(
        "scenario.distribution.protocol-manifest-bind",
        "scenario.distribution.protocol-manifest-report",
        "scenario.distribution.protocol-manifest-single-flag",
    )
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
        tracked = (root / "protocol/manifest.json").read_bytes()
        # Binding alone binds the tracked manifest, whose digests no longer match the build, so
        # refreshing the Protocol copy fails and leaves the copy as it was.
        alone = command(
            "--project-root", str(root), "protocol-manifest", "--bind-project"
        )
        self.assertNotEqual(0, alone.returncode, alone.stdout)
        refused = json.loads(alone.stdout)
        self.assertEqual("failed", refused["status"])
        self.assertEqual("protocol_mismatch", refused["error"]["code"])
        self.assertEqual(
            "sha256:" + hashlib.sha256(tracked).hexdigest(),
            json.loads((root / ".concorde/config.json").read_text())["protocol"][
                "digest"
            ],
        )
        self.assertFalse((root / ".concorde/protocol").exists())
        # Writing alone accepts the digests and binds nothing.
        written = command("--project-root", str(root), "protocol-manifest", "--write")
        self.assertEqual(0, written.returncode, written.stdout)
        self.assertEqual(
            ["generated/protocol/principles.md"],
            json.loads(written.stdout)["result"]["differences"],
        )
        self.assertNotEqual(tracked, (root / "protocol/manifest.json").read_bytes())
        self.assertEqual(
            "sha256:" + hashlib.sha256(tracked).hexdigest(),
            json.loads((root / ".concorde/config.json").read_text())["protocol"][
                "digest"
            ],
        )
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
        with self.assertRaises(CopyError):
            write_protocol_copy(project, package)
        self.assertEqual(
            before, (project / ".concorde/protocol/principles.md").read_bytes()
        )


class CommandLineTests(unittest.TestCase):
    @verifies("scenario.distribution.refused-command-line")
    def test_a_refused_command_line_answers_with_one_envelope(self):
        for argv in (
            ("spec-validation", "--bogus"),
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
        self.assertEqual(2, command("run", "frobnicate").returncode)
        self.assertEqual(2, command("task", "frobnicate").returncode)


def framework(test, parts: list[str] | None) -> Path:
    """A project whose Framework copy is this package, with a receipt naming ``parts``, or no
    parts at all when None; the project's root."""
    directory = tempfile.TemporaryDirectory()
    test.addCleanup(directory.cleanup)
    project = Path(directory.name) / "project"
    copy = project / ".concorde/framework"
    shutil.copytree(
        REPOSITORY_ROOT / "src",
        copy / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (copy / "generated").mkdir(parents=True)
    shutil.copy2(
        REPOSITORY_ROOT / "generated/parts.json", copy / "generated/parts.json"
    )
    shutil.copy2(REPOSITORY_ROOT / "concorde.json", copy / "concorde.json")
    receipt = {"version": "9.0.0"}
    if parts is not None:
        receipt["parts"] = {name: "9.0.0" for name in parts}
    (project / ".concorde/install.json").write_text(json.dumps(receipt))
    subprocess.run(["git", "init", "-q", str(project)], check=True)
    return project


def framework_command(project: Path, *argv, stdin: str | None = None):
    environment = {**os.environ, "PYTHONPATH": str(project / ".concorde/framework/src")}
    return subprocess.run(
        [sys.executable, "-m", "concorde", *argv],
        cwd=project,
        env=environment,
        input=stdin,
        capture_output=True,
        text=True,
    )


class PartsTests(unittest.TestCase):
    """The command and the project MCP server composed from the installed parts' registrations."""

    EVERY_PART_BUT = ("issues", "execution")

    def installed(self) -> list[str]:
        index = json.loads((REPOSITORY_ROOT / "generated/parts.json").read_text())
        return [name for name in index["parts"] if name not in self.EVERY_PART_BUT]

    @verifies(
        "scenario.distribution.part-missing",
        "scenario.distribution.composed-from-installed-parts",
    )
    def test_a_command_or_tool_of_a_part_not_installed_names_the_part(self):
        project = framework(self, self.installed())
        usage = framework_command(project, "--help")
        self.assertEqual(0, usage.returncode, usage.stderr)
        offered = set(usage.stdout.split("\n", 3)[3].split())
        self.assertIn("task", offered)
        self.assertNotIn("issues", offered)
        self.assertNotIn("run", offered)
        for argv, part in (
            (("issues", "list"), "issues"),
            (("run", "spec_review"), "execution"),
        ):
            with self.subTest(argv=argv):
                refused = framework_command(project, *argv)
                self.assertEqual(1, refused.returncode, refused.stderr)
                link = json.loads(refused.stdout)["error"]
                validate(link, ERROR_SCHEMA)
                self.assertEqual("part_missing", link["code"])
                self.assertIn(f"the {part} part", link["detail"])
                self.assertTrue(
                    any(f"--parts {part}" in item for item in link["options"])
                )
        listed = framework_command(project, "project-mcp", "--tools")
        self.assertEqual(0, listed.returncode, listed.stderr)
        names = {tool["name"] for tool in json.loads(listed.stdout)["tools"]}
        self.assertIn("task_list", names)
        # Neither the issues part's tools nor the coordination part's run_result and
        # task_resolve, which require the execution and issues parts.
        self.assertFalse(
            {"issue_list", "issue_report", "run_result", "task_resolve"} & names
        )
        self.assertIn("register_wait", names)
        call = {"arguments": {}, "primary": str(project), "where": str(project)}
        answered = framework_command(
            project, "project-mcp", "--call", "issue_list", stdin=json.dumps(call)
        )
        link = json.loads(answered.stdout)["error"]
        self.assertEqual("part_missing", link["code"])
        self.assertIn("the issues part", link["detail"])
        # run_result is the coordination part's, but needs the execution part.
        answered = framework_command(
            project, "project-mcp", "--call", "run_result", stdin=json.dumps(call)
        )
        link = json.loads(answered.stdout)["error"]
        self.assertEqual("part_missing", link["code"])
        self.assertIn("the execution part", link["detail"])
        # A wait for a run is refused as `concorde task wait --run` is.
        waited = framework_command(
            project,
            "project-mcp",
            "--call",
            "register_wait",
            stdin=json.dumps({**call, "arguments": {"run": "r-1"}}),
        )
        link = json.loads(waited.stdout)["error"]
        self.assertEqual("part_missing", link["code"])
        self.assertIn("the execution part", link["detail"])

    @verifies("scenario.distribution.composed-from-installed-parts")
    def test_a_receipt_naming_no_parts_installs_every_part(self):
        project = framework(self, None)
        usage = framework_command(project, "--help")
        offered = set(usage.stdout.split("\n", 3)[3].split())
        index = json.loads((REPOSITORY_ROOT / "generated/parts.json").read_text())
        self.assertEqual(
            {name for entry in index["parts"].values() for name in entry["commands"]},
            offered,
        )

    @verifies("scenario.distribution.build-refuses-name-conflict")
    def test_two_parts_registering_one_name_fail_the_build(self):
        package = package_copy(self)
        path = package / "src/concorde/issues/registration.json"
        registration = json.loads(path.read_text())
        registration["commands"].append(
            {"name": "task", "entry": "cli:main", "output": "own"}
        )
        path.write_text(json.dumps(registration))
        with self.assertRaises(BuildError) as raised:
            write_build(package)
        self.assertIn(
            "command task is registered by coordination and issues",
            str(raised.exception),
        )

    def test_every_registration_satisfies_the_registration_contract(self):
        schema = contract_schema("contract.distribution.part-registration")
        for path in sorted(
            (REPOSITORY_ROOT / "src/concorde").glob("*/registration.json")
        ):
            with self.subTest(path=path.parent.name):
                validate(json.loads(path.read_text()), schema)

    def test_the_build_refuses_what_the_registration_contract_refuses(self):
        schema = contract_schema("contract.distribution.part-registration")
        data = json.loads(
            (REPOSITORY_ROOT / "src/concorde/issues/registration.json").read_text()
        )
        cases = {
            "a one-letter part": {**data, "part": "x"},
            "a dependency of one letter": {**data, "depends_on": ["k"]},
            "a repeated ignore rule": {
                **data,
                "install": {**data["install"], "gitignore": ["a/", "a/"]},
            },
            "a repeated permission rule": {
                **data,
                "install": {**data["install"], "permissions": ["X", "X"]},
            },
        }
        for case, registration in cases.items():
            with self.subTest(case=case):
                with self.assertRaises(ContractError):
                    validate(registration, schema)
                with self.assertRaises(parts.RegistrationError):
                    parts.check(registration, "registration.json")


class InstallTests(unittest.TestCase):
    @verifies(
        "scenario.distribution.install",
        "scenario.distribution.install-repeat",
        "scenario.distribution.glossary-import",
        "scenario.distribution.glossary-import-none",
        "scenario.main-session.project-terms",
        "scenario.main-session.project-terms-missing",
    )
    def test_install_places_concorde_without_touching_specs(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        (project / "CLAUDE.md").write_text("# My project\n\nKeep this.\n")
        (project / "AGENTS.md").write_text("# Agents\n\nKeep this too.\n")
        fetch = fake_d2(self, package)
        receipt = install(
            project, package, pi_runtime=False, fetch=fetch, dependencies=False
        )
        self.assertEqual(str(package), receipt["source"])
        self.assertEqual("normal", receipt["mode"])
        # The package copy is no Git checkout, so no commit names it.
        self.assertIsNone(receipt["source_commit"])
        self.assertTrue((project / ".concorde/protocol/manifest.json").exists())
        self.assertTrue(
            (project / ".concorde/framework/src/concorde/spec/grants.py").exists()
        )
        # The Framework copy is the installed parts' runtime: no prompt source, no guidance
        # section the installer already composed, no development tooling.
        copy = project / ".concorde/framework"
        self.assertEqual(
            {
                "concorde.json",
                "generated",
                "protocol",
                "scripts",
                "src",
                "docsite",
                "python",
            },
            {path.name for path in copy.iterdir()} - {"requirements.txt"},
        )
        self.assertFalse((copy / "prompts").exists())
        self.assertFalse((copy / "scripts/development").exists())
        # The task-session prompt of the installed parts, all of them, which Coordination reads.
        self.assertEqual(
            (package / "generated/guidance/task-session.md").read_text(),
            (
                project / ".concorde/framework/generated/guidance/task-session.md"
            ).read_text(),
        )
        # Standalone discovery ships with the runtime and runs from outside Git.
        discovery = project / ".concorde/framework/scripts/available_models.py"
        self.assertTrue(discovery.is_file())
        discovered = subprocess.run(
            [
                str(project / ".concorde/framework/python/bin/python"),
                str(discovery),
                "--help",
            ],
            cwd=package.parent,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, discovered.returncode, discovered.stderr)
        self.assertIn("--backend", discovered.stdout)
        # The worker configuration is the project's to write and track; none is installed.
        self.assertFalse((project / ".concorde/workers.json").exists())
        # End-to-end testing serves Concorde's developers only.
        self.assertFalse((project / ".concorde/framework/scripts/e2e").exists())
        skill = (project / ".claude/skills/concorde/SKILL.md").read_text()
        fields = strict_frontmatter(self, skill)
        self.assertEqual("concorde", fields["name"])
        self.assertIn("Concorde's main agent", fields["description"])
        self.assertIn("Concorde main agent", skill)
        # The installed skill is the build's rendered skill, front matter included.
        self.assertEqual(
            (package / "generated/skills/concorde/SKILL.md").read_text(), skill
        )
        # The project's own AGENTS.md is left as it is.
        self.assertEqual(
            "# Agents\n\nKeep this too.\n", (project / "AGENTS.md").read_text()
        )
        self.assertNotIn("AGENTS.md", receipt["amended"])
        claude = (project / "CLAUDE.md").read_text()
        self.assertIn("Keep this.", claude)
        self.assertEqual(1, claude.count("<!-- concorde:start -->"))
        # No glossary is declared before initialization, so nothing is imported yet.
        self.assertNotIn("<!-- concorde:glossary -->", claude)
        ignored = (project / ".gitignore").read_text().splitlines()
        # The folders Tracing keeps, and the one where defect reports and session logs stay.
        for folder in (
            ".concorde/tasks/",
            ".concorde/history/",
            ".concorde/unbound/",
            ".concorde/locks/",
            ".concorde/runs/",
        ):
            self.assertIn(folder, ignored)
        self.assertIn(".concorde/workspace.json", (project / ".gitignore").read_text())
        self.assertIn(".claude/worktrees/", (project / ".gitignore").read_text())
        self.assertNotIn(".concorde/workers.json", (project / ".gitignore").read_text())
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
        install(project, package, pi_runtime=False, fetch=fetch, dependencies=False)
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
            [str(project / ".concorde/bin/concorde"), "spec-validation"],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual("success", json.loads(valid.stdout)["status"], valid.stdout)
        # The glossary initialization created is imported by the CLAUDE.md block, once.
        claude = (project / "CLAUDE.md").read_text()
        block = claude.split("<!-- concorde:start -->", 1)[1].split(
            "<!-- concorde:end -->"
        )[0]
        self.assertIn("@specs/project/glossary.json", block)
        self.assertIn("Keep this.", claude)
        install(project, package, pi_runtime=False, fetch=fetch, dependencies=False)
        self.assertEqual(
            1, (project / "CLAUDE.md").read_text().count("@specs/project/glossary.json")
        )

    @verifies("scenario.distribution.glossary-import-failed")
    def test_a_glossary_import_that_cannot_be_written_after_init_is_reported(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, d2=False, pi_runtime=False, dependencies=False)
        concorde = str(project / ".concorde/bin/concorde")
        proposed = subprocess.run(
            [concorde, "init", "--propose", "--name", "Demo"],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proposed.returncode, proposed.stdout + proposed.stderr)
        proposal = package.parent / "proposal.json"
        proposal.write_text(json.dumps(json.loads(proposed.stdout)["result"]))
        claude = project / "CLAUDE.md"
        claude.chmod(0o444)
        self.addCleanup(claude.chmod, 0o644)
        applied = subprocess.run(
            [concorde, "init", "--apply", "--proposal", str(proposal)],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, applied.returncode, applied.stdout)
        refused = json.loads(applied.stdout)
        self.assertEqual("failed", refused["status"])
        self.assertEqual("guidance_failed", refused["error"]["code"])
        self.assertEqual("system_error", refused["error"]["causes"][0]["code"])
        self.assertIn("concorde update", refused["error"]["remediation"])
        self.assertTrue(refused["result"])
        self.assertTrue((project / "specs/project/glossary.json").is_file())
        self.assertNotIn("@specs/project/glossary.json", claude.read_text())
        claude.chmod(0o644)
        with which():
            update(project, package)
        self.assertEqual(1, claude.read_text().count("@specs/project/glossary.json"))

    @verifies(
        "scenario.distribution.install-idle-check-failed",
        "scenario.distribution.update-open-tasks-failed",
    )
    def test_a_failing_idle_check_or_open_task_report_is_refused(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, pi_runtime=False, d2=False, dependencies=False)
        receipt = (project / ".concorde/install.json").read_bytes()
        entry = parts.Registration.entry

        def failing(field, answer):
            """The part's ``field`` entry raising ``answer`` or answering it."""

            def patched(registration, name):
                if name != registration.data[field]:
                    return entry(registration, name)

                def broken(root):
                    if isinstance(answer, Exception):
                        raise answer
                    return answer

                return broken

            return patch.object(parts.Registration, "entry", patched)

        for answer in (RuntimeError("the run store cannot be read"), "busy", [3]):
            with self.subTest(answer=answer), failing("idle_check", answer):
                with self.assertRaises(InstallError) as raised:
                    install(
                        project, package, pi_runtime=False, d2=False, dependencies=False
                    )
                self.assertEqual("part_failed", raised.exception.code)
                self.assertIn(
                    "execution part's idle_check entry", str(raised.exception)
                )
                link = refusal(
                    "part_failed", str(raised.exception), causes=raised.exception.causes
                )
                validate(link, ERROR_SCHEMA)
                self.assertEqual("environment", link["unhandled"]["reason"])
                self.assertEqual(
                    isinstance(answer, Exception), bool(raised.exception.causes)
                )
                self.assertEqual(
                    receipt, (project / ".concorde/install.json").read_bytes()
                )
        with failing("after_update", RuntimeError("no task records")), which():
            with self.assertRaises(InstallError) as raised:
                update(project, package)
        self.assertEqual("part_failed", raised.exception.code)
        self.assertIn("coordination part's after_update entry", str(raised.exception))
        self.assertIn("only the list of open tasks is lost", str(raised.exception))
        self.assertEqual("unexpected_error", raised.exception.causes[0]["code"])
        # The update installed and marked before it asked for the open tasks.
        mark = json.loads((project / ".concorde/update.json").read_text())
        self.assertEqual("unvalidated", mark["state"])

    @verifies(
        "scenario.distribution.install-busy",
        "scenario.distribution.install-after-runs-end",
    )
    def test_install_and_update_wait_until_concorde_is_idle(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, pi_runtime=False, d2=False, dependencies=False)
        receipt = (project / ".concorde/install.json").read_bytes()
        live = subprocess.Popen(["sleep", "60"])
        self.addCleanup(live.wait)
        self.addCleanup(live.kill)
        concorde = project / ".concorde"
        workspace = concorde / "tasks/t1/workspace"
        run = workspace / "runs/r-1/status.json"
        run.parent.mkdir(parents=True)
        run.write_text(
            json.dumps(
                {
                    "kind": "operation",
                    "run_id": "r-1",
                    "name": "implement",
                    "workspace": "t1",
                    "phase": "running",
                    "host_pid": live.pid,
                }
            )
        )
        # Its runner holds the run lock, as a live runner does.
        held = contextlib.ExitStack()
        self.addCleanup(held.close)
        held.enter_context(
            run_lock(Store(concorde, workspace), "r-1", "Execution runner")
        )
        # A bound run waiting for its workspace's lock keeps its progress file in the lobby.
        waiting = concorde / "lobby/r-2/status.json"
        waiting.parent.mkdir(parents=True)
        waiting.write_text(
            json.dumps(
                {
                    "kind": "command",
                    "run_id": "r-2",
                    "name": "delivery",
                    "workspace": "t1",
                    "phase": "waiting",
                    "host_pid": live.pid,
                }
            )
        )
        held.enter_context(
            run_lock(Store(concorde, workspace), "r-2", "Execution runner")
        )
        # A finished run, a run whose runner is gone (its process identifier, recorded in a
        # sandbox's PID namespace, names a live unrelated process here, and its lock file was
        # left behind held by nobody) and the progress file of the running Operation's own
        # worker do not count as runs of their own.
        for folder, state in (
            (
                workspace / "runs/r-0",
                {"kind": "operation", "phase": "finished", "host_pid": live.pid},
            ),
            (
                concorde / "unbound/r-dead",
                {"kind": "operation", "phase": "running", "host_pid": 1},
            ),
            (
                run.parent / "workers/w-1",
                {"phase": "worker", "host_pid": live.pid, "run_id": "w-1"},
            ),
        ):
            folder.mkdir(parents=True)
            (folder / "status.json").write_text(json.dumps(state))
        (concorde / "locks/runs/r-dead.lock").write_text("")
        for attempt in (
            lambda: install(
                project, package, pi_runtime=False, d2=False, dependencies=False
            ),
            lambda: update(project, package),
        ):
            with self.assertRaises(InstallError) as raised:
                attempt()
            self.assertEqual("concorde_busy", raised.exception.code)
            message = str(raised.exception)
            for fragment in (
                "operation run r-1",
                "implement",
                "workspace t1",
                f"held by Execution runner (process {os.getpid()}",
                ".concorde/locks/runs/r-1.lock",
                ".concorde/tasks/t1/workspace/runs/r-1/status.json",
                "command run r-2 (delivery, workspace t1",
                ".concorde/locks/runs/r-2.lock",
                ".concorde/lobby/r-2/status.json",
            ):
                self.assertIn(fragment, message)
            self.assertNotIn("r-0", message)
            self.assertNotIn("r-dead", message)
            self.assertNotIn("w-1", message)
            self.assertEqual(1, message.count("operation run"))
            self.assertEqual(receipt, (project / ".concorde/install.json").read_bytes())
            self.assertFalse((project / ".concorde/update.json").exists())
        held.close()
        live.kill()
        live.wait()
        install(project, package, pi_runtime=False, d2=False, dependencies=False)

    @verifies(
        "scenario.distribution.own-python",
        "scenario.distribution.install-python-env-failed",
    )
    def test_concorde_runs_in_its_own_python_whatever_the_caller_uses(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        receipt = install(
            project, package, pi_runtime=False, d2=False, dependencies=False
        )
        self.assertEqual(".concorde/framework/python", receipt["python"]["environment"])
        # uv made the environment for the package's own requirement, on an interpreter it chose.
        self.assertEqual(">=3.11", receipt["python"]["requirement"])
        self.assertGreaterEqual(
            tuple(int(part) for part in receipt["python"]["version"].split(".")),
            (3, 11),
        )
        self.assertTrue(Path(receipt["python"]["base"]).is_file())
        self.assertIn(
            "uv = ", (project / ".concorde/framework/python/pyvenv.cfg").read_text()
        )
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
        # A requirement no interpreter satisfies, with downloads forbidden: uv's refusal.
        descriptor = json.loads((package / "concorde.json").read_text())
        descriptor["runtime"]["python"] = "==3.2.1"
        (package / "concorde.json").write_text(json.dumps(descriptor, indent=2) + "\n")
        write_build(package)
        with (
            patch.dict(os.environ, {"UV_PYTHON_DOWNLOADS": "never"}),
            self.assertRaises(InstallError) as raised,
        ):
            install(project, package, pi_runtime=False, d2=False, dependencies=False)
        self.assertEqual("python_env_failed", raised.exception.code)
        self.assertIn("==3.2.1", str(raised.exception))
        self.assertIn("venv", str(raised.exception))

    @verifies("scenario.distribution.install-programs-missing")
    def test_missing_programs_refuse_the_install_before_anything_is_written(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        fetch = fake_d2(self, package)
        for found, pi_runtime, code in (
            ({"uv": None, "npm": "/usr/bin/npm"}, False, "uv_missing"),
            ({"uv": None, "npm": "/usr/bin/npm"}, True, "uv_missing"),
            ({}, True, "npm_missing"),
        ):
            with (
                self.subTest(code=code, pi_runtime=pi_runtime),
                which(**found),
                self.assertRaises(InstallError) as raised,
            ):
                install(project, package, pi_runtime=pi_runtime, fetch=fetch)
            self.assertEqual(code, raised.exception.code)
            self.assertIn("nothing was written", str(raised.exception))
            self.assertEqual([".git"], [path.name for path in project.iterdir()])
        # Not even the pinned d2 was fetched.
        self.assertEqual([], fetch.urls)

    @verifies(
        "scenario.distribution.update",
        "scenario.distribution.update-unvalidated-reported",
        "scenario.distribution.update-unvalidated-cleared",
    )
    def test_update_rebinds_the_protocol_and_waits_for_a_validation(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, pi_runtime=False, d2=False, dependencies=False)
        concorde = str(project / ".concorde/bin/concorde")

        def run(*argv):
            return subprocess.run(
                [concorde, *argv], cwd=project, capture_output=True, text=True
            )

        def git(*argv):
            subprocess.run(
                ["git", "-c", "user.name=t", "-c", "user.email=t@t", *argv],
                cwd=project,
                check=True,
                capture_output=True,
            )

        proposed = json.loads(run("init", "--propose", "--name", "Demo").stdout)
        (project.parent / "proposal.json").write_text(json.dumps(proposed["result"]))
        applied = run("init", "--apply", "--proposal", "../proposal.json")
        self.assertEqual(0, applied.returncode, applied.stdout)
        git("add", "-A")
        git("commit", "-qm", "adopt")
        opened = run("task", "open", "t1", "--goal", "g", "--modules", "module.project")
        self.assertEqual(0, opened.returncode, opened.stdout + opened.stderr)
        before = json.loads((project / ".concorde/config.json").read_text())["protocol"]
        # A newer Concorde: its Protocol changed.
        chapter = package / "protocol/views.md"
        chapter.write_text(chapter.read_text() + "\nAn added sentence.\n")
        write_build(package)
        written = command(
            "--project-root", str(package), "protocol-manifest", "--write"
        )
        self.assertEqual(0, written.returncode, written.stdout)
        updated = run("update")
        self.assertEqual(0, updated.returncode, updated.stdout + updated.stderr)
        report = json.loads(updated.stdout)
        after = json.loads((project / ".concorde/config.json").read_text())["protocol"]
        self.assertNotEqual(before, after)
        self.assertEqual({"from": before, "to": after}, report["update"]["protocol"])
        self.assertEqual("unvalidated", report["update"]["state"])
        self.assertEqual(["t1"], [task["id"] for task in report["open_tasks"]])
        self.assertTrue(
            any("merge the primary branch" in item for item in report["next"])
        )
        self.assertTrue((project / ".concorde/update.json").is_file())
        self.assertIn(".concorde/update.json", (project / ".gitignore").read_text())
        # Unvalidated: an error while anything else fails, kept until a validation passes.
        entry = project / "specs/project/module.md"
        text = entry.read_text()
        # A Mermaid block is a structural error (CHK.view.marked).
        entry.write_text(text + "\n```mermaid\ngraph TD\n  a --> b\n```\n")
        failing = json.loads(run("spec-validation").stdout)
        self.assertEqual("invalid", failing["status"])
        self.assertIn(
            "CONCORDE-UPDATE-001", [f["rule_id"] for f in failing["findings"]]
        )
        self.assertTrue((project / ".concorde/update.json").is_file())
        entry.write_text(text)
        passing = json.loads(run("spec-validation").stdout)
        self.assertEqual("success", passing["status"], passing)
        self.assertIn(
            "CONCORDE-UPDATE-002", [f["rule_id"] for f in passing["findings"]]
        )
        self.assertFalse((project / ".concorde/update.json").exists())
        # An update that brings no new Protocol asks for no task merges.
        again = json.loads(run("update").stdout)
        self.assertIsNone(again["update"]["protocol"])
        self.assertFalse(
            any("merge the primary branch" in item for item in again["next"])
        )

    @verifies("scenario.distribution.task-worktree-command")
    def test_the_command_of_a_task_worktree_runs_the_primary_framework(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, pi_runtime=False, d2=False, dependencies=False)

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

    @verifies(
        "scenario.distribution.python-dependencies",
        "scenario.distribution.python-dependencies-failed",
        "scenario.distribution.python-dependencies-skipped",
    )
    def test_install_places_the_locked_python_dependencies_in_its_own_environment(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        calls = []

        def fake_uv(command, cwd, **options):
            calls.append(command)
            if command[1] == "export":
                Path(command[command.index("--output-file") + 1]).write_text(
                    "# locked\nlanggraph==1.2.12 \\\n    --hash=sha256:00\n"
                )
            return subprocess.CompletedProcess(command, 0, "", "")

        receipt = install(project, package, pi_runtime=False, d2=False, run=fake_uv)
        export, pip, probe = calls
        self.assertEqual(
            [UV, "export", "--frozen", "--no-dev", "--no-emit-project"],
            export[:5],
        )
        self.assertIn(str(package), export)
        interpreter = str(project / ".concorde/framework/python/bin/python")
        self.assertEqual(
            [
                UV,
                "pip",
                "install",
                "--python",
                interpreter,
                "--require-hashes",
            ],
            pip[:6],
        )
        self.assertEqual(
            # Method's dependency, the only one an installed part names.
            [interpreter, "-E", "-s", "-c", "import langgraph"],
            probe,
        )
        self.assertEqual(
            {
                "requirements": ".concorde/framework/requirements.txt",
                "lock_sha256": hashlib.sha256(
                    (package / "uv.lock").read_bytes()
                ).hexdigest(),
                "packages": 1,
            },
            receipt["dependencies"],
        )

        def failing(command, cwd, **options):
            return subprocess.CompletedProcess(command, 1, "", "no network")

        with self.assertRaises(InstallError) as caught:
            install(project, package, pi_runtime=False, d2=False, run=failing)
        self.assertEqual("python_dependencies_failed", caught.exception.code)
        self.assertIn("no network", str(caught.exception))
        self.assertIsNone(
            install(project, package, pi_runtime=False, d2=False, dependencies=False)[
                "dependencies"
            ]
        )

    @verifies("scenario.distribution.install-repeat")
    def test_install_places_the_locked_runtime_once(self):
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

        with which(npm="/usr/bin/npm"):
            receipt = install(
                project, package, d2=False, run=fake_npm, dependencies=False
            )
            install(project, package, d2=False, run=fake_npm, dependencies=False)
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
        # No file of a pi main session is placed: the main agent runs on Claude Code.
        self.assertFalse((project / ".pi").exists())

    @verifies(
        "scenario.distribution.install",
        "scenario.distribution.install-settings-kept",
        "scenario.distribution.install-settings-invalid",
    )
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
        receipt = install(
            project, package, pi_runtime=False, d2=False, dependencies=False
        )
        workflow = project / ".claude/workflows/concorde-brownfield.js"
        self.assertTrue(workflow.read_text().startswith("export const meta = {"))
        self.assertIn(".claude/workflows/concorde-brownfield.js", receipt["files"])
        self.assertFalse((project / ".pi").exists())
        self.assertFalse((project / "AGENTS.md").exists())
        value = json.loads(settings.read_text())
        self.assertEqual("x", value["model"])
        allow = value["permissions"]["allow"]
        self.assertEqual(["Bash(ls:*)", mine], allow[:2])
        self.assertIn("Workflow(concorde-brownfield)", allow)
        self.assertIn("mcp__concorde__workflow_step", allow)
        self.assertNotIn("Bash(.concorde/bin/concorde workflow step:*)", allow)
        self.assertEqual(1, allow.count(mine))
        # The developer's own rule was there first, so Concorde does not own it.
        self.assertNotIn(mine, receipt["permissions"])
        # A rule Concorde recorded and no longer ships is removed; the developer's rules stay.
        recorded = json.loads((project / ".concorde/install.json").read_text())
        recorded["permissions"].append("Workflow(concorde-retired)")
        (project / ".concorde/install.json").write_text(json.dumps(recorded))
        value["permissions"]["allow"].append("Workflow(concorde-retired)")
        settings.write_text(json.dumps(value))
        install(project, package, pi_runtime=False, d2=False, dependencies=False)
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
            install(project, package, pi_runtime=False, d2=False, dependencies=False)
        self.assertEqual("settings_invalid", raised.exception.code)
        self.assertFalse(
            (project / ".claude/workflows/concorde-brownfield.js").exists()
        )

    @verifies("scenario.distribution.install-defaults-kept")
    def test_a_default_stays_once_no_part_or_package_declares_it(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        default = ".concorde/issues/.gitignore"
        first = install(
            project,
            package,
            part_names=["issues"],
            pi_runtime=False,
            d2=False,
            dependencies=False,
        )
        self.assertIn(default, first["files"])
        self.assertEqual([default], first["defaults"])
        (project / default).write_text("# the project's own\n")
        for _ in ("a part left out", "a package that no longer declares it"):
            receipt = install(
                project,
                package,
                part_names=["coordination"],
                pi_runtime=False,
                d2=False,
                dependencies=False,
            )
            self.assertEqual("# the project's own\n", (project / default).read_text())
            self.assertIn(default, receipt["files"])
            self.assertEqual([default], receipt["defaults"])
            path = package / "src/concorde/issues/registration.json"
            registration = json.loads(path.read_text())
            registration["install"]["defaults"] = {}
            path.write_text(json.dumps(registration, indent=2) + "\n")
            write_build(package)

    @verifies(
        "scenario.distribution.install-project-mcp",
        "scenario.distribution.install-mcp-config-invalid",
    )
    def test_install_registers_the_project_mcp_server(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        config = project / ".mcp.json"
        mine = {"command": "my-server", "args": ["--x"]}
        config.write_text(json.dumps({"mcpServers": {"mine": mine}}))
        receipt = install(
            project, package, pi_runtime=False, d2=False, dependencies=False
        )
        servers = json.loads(config.read_text())["mcpServers"]
        self.assertEqual(mine, servers["mine"])
        self.assertEqual(
            {"command": ".concorde/bin/concorde", "args": ["project-mcp"]},
            servers["concorde"],
        )
        self.assertIn(".mcp.json", receipt["amended"])
        self.assertNotIn(".mcp.json", receipt["files"])
        # Installing again leaves the file as it is.
        before = config.read_text()
        install(project, package, pi_runtime=False, d2=False, dependencies=False)
        self.assertEqual(before, config.read_text())
        # A configuration that is not a JSON object is refused before anything is written.
        config.write_text("[1]")
        (project / ".claude/workflows/concorde-brownfield.js").unlink()
        with self.assertRaises(InstallError) as raised:
            install(project, package, pi_runtime=False, d2=False, dependencies=False)
        self.assertEqual("mcp_config_invalid", raised.exception.code)
        self.assertFalse(
            (project / ".claude/workflows/concorde-brownfield.js").exists()
        )

    @verifies("scenario.distribution.install-programs-missing")
    def test_install_without_npm_installs_nothing(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        with which(), self.assertRaises(InstallError) as raised:
            install(project, package, d2=False, dependencies=False)
        self.assertEqual("npm_missing", raised.exception.code)
        self.assertFalse((project / ".concorde/framework").exists())

    @verifies("scenario.distribution.pi-runtime-default")
    def test_a_plain_install_places_the_pi_runtime_workers_run_in(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        calls = []
        with which(npm="/usr/bin/npm"):
            receipt = install(
                project, package, d2=False, run=fake_npm(calls), dependencies=False
            )
        self.assertEqual(1, len(calls))
        self.assertIn("pi-runtime", receipt["tools"])
        self.assertTrue(receipt["pi_runtime"])
        self.assertNotIn("pi", receipt)
        with which():
            left_out = install(
                project, package, d2=False, pi_runtime=False, dependencies=False
            )
        self.assertNotIn("pi-runtime", left_out["tools"])
        self.assertFalse(left_out["pi_runtime"])

    @verifies("scenario.distribution.install-without-pi-runtime")
    def test_an_install_without_the_pi_runtime_needs_no_npm(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        # A machine without npm, and a project that never had the runtime.
        with which():
            receipt = install(
                project, package, d2=False, pi_runtime=False, dependencies=False
            )
        self.assertFalse((project / ".concorde/tools/pi-runtime").exists())
        self.assertNotIn("pi-runtime", receipt["tools"])
        self.assertFalse(receipt["pi_runtime"])

    @verifies("scenario.distribution.update-pi-runtime")
    def test_an_update_adds_the_pi_runtime(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, d2=False, pi_runtime=False, dependencies=False)
        # A receipt written before the choice was recorded: it had no runtime.
        path = project / ".concorde/install.json"
        receipt = json.loads(path.read_text())
        del receipt["pi_runtime"]
        path.write_text(json.dumps(receipt))
        calls = []
        with which(npm="/usr/bin/npm"):
            updated = update(project, package, run=fake_npm(calls))["receipt"]
            self.assertIn("pi-runtime", updated["tools"])
            self.assertTrue(updated["pi_runtime"])
            self.assertFalse((project / ".pi").exists())
            # The choice is kept by the next update.
            kept = update(project, package, run=fake_npm(calls))["receipt"]
        self.assertTrue(kept["pi_runtime"])
        self.assertEqual(1, len(calls), "the locked runtime is installed once")

    @verifies("scenario.distribution.install-later-files-bound")
    def test_files_a_later_install_adds_stay_bound(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        (project / "app.py").write_text("print(1)\n")
        install(project, package, d2=False, pi_runtime=False, dependencies=False)
        # A project that is not initialized gets no Spec from the installer.
        self.assertFalse((project / "specs").exists())
        apply_project_proposal(
            project, package, project_proposal(project, package, "Demo")
        )
        metadata = project / "specs/project/module.md.json"

        def installation() -> list[str]:
            return next(
                r["entries"]
                for r in json.loads(metadata.read_text())["defines"]
                if r["id"] == "realization.project.concorde-installation"
            )

        # As if an older Concorde had not installed the brownfield workflow yet.
        added = ".claude/workflows/concorde-brownfield.js"
        (project / added).unlink()
        value = json.loads(metadata.read_text())
        for item in value["defines"]:
            if item["id"] == "realization.project.concorde-installation":
                item["entries"].remove(added)
        metadata.write_text(json.dumps(value, indent=2) + "\n")
        self.assertNotIn(added, installation())
        entry = (project / "specs/project/module.md").read_bytes()
        receipt = install(
            project, package, d2=False, pi_runtime=False, dependencies=False
        )
        placed = sorted(
            path
            for path in receipt["files"]
            if not path.startswith(".concorde/") and path not in receipt["amended"]
        )
        self.assertIn(added, placed)
        self.assertEqual(placed, installation())
        self.assertEqual(entry, (project / "specs/project/module.md").read_bytes())
        subprocess.run(["git", "add", "-A"], cwd=project, check=True)
        report = validate_repository(project, package_root=package)
        self.assertEqual(
            [],
            [f.source for f in report.findings if f.rule_id == "CHK.binds.unbound"],
        )
        self.assertEqual(
            "success",
            report.status,
            [f.message for f in report.findings if f.strictness == "error"],
        )
        # An update with nothing new to place leaves the Specs as they are.
        bound = metadata.read_bytes()
        with which():
            update(project, package)
        self.assertEqual(bound, metadata.read_bytes())

    @verifies(
        "scenario.distribution.install-parts",
        "scenario.distribution.update-installed-parts",
        "scenario.distribution.update-without-spec",
    )
    def test_the_installer_and_update_take_the_parts_to_install(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        installed = subprocess.run(
            [sys.executable, str(package / "scripts/install-concorde.py"), str(project)]
            # The choice to leave the pi runtime out holds for the worker harness added later.
            + ["--parts", "coordination", "--without-pi-runtime"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
        result = json.loads(installed.stdout)
        validate(result, contract_schema("contract.distribution.install-result"))
        self.assertEqual(
            {"coordination", "distribution", "kernel"}, set(result["parts"])
        )
        updated = subprocess.run(
            [str(project / ".concorde/bin/concorde"), "update"]
            + ["--parts", "issues,worker harness"],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, updated.returncode, updated.stdout + updated.stderr)
        report = json.loads(updated.stdout)
        validate(report, contract_schema("contract.distribution.update-result"))
        self.assertEqual(
            {"coordination", "distribution", "issues", "kernel", "worker harness"},
            set(report["receipt"]["parts"]),
        )
        # Without the spec part nothing waits for a validation.
        self.assertIsNone(report["update"])
        self.assertEqual(["commit the updated files"], report["next"])
        self.assertNotIn("pi-runtime", report["receipt"]["tools"])
        self.assertIsNone(report["receipt"]["dependencies"])
        self.assertFalse((project / ".concorde/update.json").exists())

    @verifies("scenario.distribution.update-adds-programs")
    def test_an_update_places_what_an_added_part_needs(self):
        package = package_copy(self)
        fetch = fake_d2(self, package)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        calls = []

        def fake_uv(command, cwd, **options):
            calls.append(command)
            if command[1] == "export":
                Path(command[command.index("--output-file") + 1]).write_text(
                    "# locked\nlanggraph==1.2.12 \\\n    --hash=sha256:00\n"
                )
            return subprocess.CompletedProcess(command, 0, "", "")

        # Coordination needs neither d2 nor a Python dependency: none is placed.
        with which():
            first = install(
                project, package, part_names=["coordination"], pi_runtime=False
            )
        self.assertNotIn("d2", first["tools"])
        self.assertIsNone(first["dependencies"])
        with which():
            updated = update(
                project, package, part_names=["method"], fetch=fetch, run=fake_uv
            )["receipt"]
        self.assertIn("d2", updated["tools"])
        self.assertEqual(1, len(fetch.urls))
        self.assertIsNotNone(updated["dependencies"])
        self.assertTrue(any(command[1:3] == ["pip", "install"] for command in calls))

    @verifies("scenario.distribution.install-unknown-part")
    def test_a_part_the_package_does_not_build_installs_nothing(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        refused = subprocess.run(
            [sys.executable, str(package / "scripts/install-concorde.py"), str(project)]
            + ["--parts", "spec,dashboard"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(1, refused.returncode, refused.stdout + refused.stderr)
        link = json.loads(refused.stdout)["error"]
        validate(link, ERROR_SCHEMA)
        self.assertEqual("unknown_part", link["code"])
        self.assertEqual("input", link["unhandled"]["reason"])
        self.assertIn("'dashboard'", link["detail"])
        self.assertIn("worker harness", link["detail"])
        self.assertEqual([".git"], sorted(path.name for path in project.iterdir()))

    @verifies("scenario.distribution.install")
    def test_install_and_update_print_their_contracted_results(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        installed = subprocess.run(
            [sys.executable, str(package / "scripts/install-concorde.py"), str(project)]
            + ["--without-d2", "--without-pi-runtime", "--without-dependencies"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
        result = json.loads(installed.stdout)
        validate(result, contract_schema("contract.distribution.install-result"))
        self.assertEqual(
            json.loads((project / ".concorde/install.json").read_text()), result
        )
        updated = subprocess.run(
            [str(project / ".concorde/bin/concorde"), "update"],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, updated.returncode, updated.stdout + updated.stderr)
        report = json.loads(updated.stdout)
        validate(report, contract_schema("contract.distribution.update-result"))
        validate(
            report["receipt"], contract_schema("contract.distribution.install-result")
        )
        self.assertEqual(
            json.loads((project / ".concorde/update.json").read_text()),
            report["update"],
        )
        # Nothing was installed before from a Git checkout, so no commit names either side.
        self.assertEqual({"from": None, "to": None}, report["update"]["commits"])
        self.assertEqual([], report["open_tasks"])

    @verifies("scenario.distribution.install-binding-failed")
    def test_a_failed_binding_is_reported_and_the_install_kept(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        refused = SpecError(
            "specs/project/module.md.json was not restored",
            "system_error",
            path="specs/project/module.md.json",
        )
        with patch("concorde.spec.installation.bind_installation", side_effect=refused):
            result = install(
                project, package, d2=False, pi_runtime=False, dependencies=False
            )
        validate(result, contract_schema("contract.distribution.install-result"))
        self.assertEqual("system_error", result["binding_error"]["code"])
        self.assertEqual(
            "specs/project/module.md.json",
            result["binding_error"]["location"]["path"],
        )
        receipt = json.loads((project / ".concorde/install.json").read_text())
        self.assertNotIn("binding_error", receipt)
        self.assertEqual(
            receipt, {k: v for k, v in result.items() if k != "binding_error"}
        )

    @verifies("scenario.distribution.update-keeps-pi-runtime-choice")
    def test_an_update_keeps_a_runtime_that_was_left_out(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, d2=False, pi_runtime=False, dependencies=False)
        with which():
            updated = update(project, package)["receipt"]
        self.assertNotIn("pi-runtime", updated["tools"])
        self.assertFalse(updated["pi_runtime"])

    @verifies("scenario.distribution.install-refusal-link")
    def test_installer_and_update_refuse_with_an_error_link(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        cases = (
            (
                [sys.executable, str(package / "scripts/install-concorde.py")]
                + [str(package.parent / "absent")],
                "invalid_project",
                "input",
                "Installer (install-concorde)",
            ),
            (
                [sys.executable, str(package / "scripts/concorde.py"), "update"]
                + ["--project-root", str(project)],
                "update_source_missing",
                "input",
                "concorde update",
            ),
        )
        for argv, code, reason, actor in cases:
            with self.subTest(code=code):
                result = subprocess.run(argv, capture_output=True, text=True)
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                error = json.loads(result.stdout)["error"]
                validate(error, ERROR_SCHEMA)
                self.assertEqual(
                    ("component", actor, code, reason),
                    (
                        error["level"],
                        error["actor"],
                        error["code"],
                        error["unhandled"]["reason"],
                    ),
                )
                self.assertTrue(error["detail"])
        self.assertEqual(
            "environment", refusal("concorde_busy", "busy")["unhandled"]["reason"]
        )

    def test_the_refusal_table_lists_every_refusal_with_its_reason(self):
        text = (REPOSITORY_ROOT / "specs/concorde/distribution/module.md").read_text()
        section = text.split("\n### Refusals\n", 1)[1].split("\n### ", 1)[0]
        table = {}
        for row in section.splitlines():
            if row.startswith("| `"):
                cells = [cell.strip() for cell in row.strip("|").split("|")]
                for code in re.findall(r"`([a-z0-9_]+)`", cells[0]):
                    table[code] = cells[2].strip("`")
        for code, reason in table.items():
            self.assertEqual(
                reason, refusal(code, "refused")["unhandled"]["reason"], code
            )
        raised = set()
        for source in (
            "src/concorde/distribution/install.py",
            "src/concorde/distribution/tools.py",
            "src/concorde/distribution/cli.py",
            "src/concorde/dogfooding/develop.py",
        ):
            raised.update(
                re.findall(
                    r'(?:InstallError|ToolError|DevelopError|refusal)\(\s*"([a-z0-9_]+)"',
                    (REPOSITORY_ROOT / source).read_text(),
                )
            )
        # The spec part's install service refuses a template Views' inventory rule rejects.
        raised.add(DocsiteTemplateError.DEFAULT_CODE)
        self.assertEqual(raised, set(table))

    @verifies("scenario.distribution.install-write-failed")
    def test_a_write_failing_after_the_first_write_is_refused(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        # A file where the project skill's folder goes: every check passes, the write fails.
        blocker = project / ".claude/skills/concorde"
        blocker.parent.mkdir(parents=True)
        blocker.write_text("in the way\n")
        with self.assertRaises(InstallError) as refused:
            install(project, package, d2=False, pi_runtime=False, dependencies=False)
        self.assertEqual("install_failed", refused.exception.code)
        self.assertIn(str(blocker), str(refused.exception))
        link = refusal(refused.exception.code, str(refused.exception))
        validate(link, ERROR_SCHEMA)
        self.assertEqual("environment", link["unhandled"]["reason"])
        # Nothing is rolled back, and the receipt, written last, records nothing.
        self.assertTrue((project / ".concorde/protocol/manifest.json").is_file())
        self.assertTrue((project / ".concorde/framework/scripts/concorde.py").is_file())
        self.assertFalse((project / ".concorde/install.json").exists())
        blocker.unlink()
        receipt = install(
            project, package, d2=False, pi_runtime=False, dependencies=False
        )
        self.assertEqual(
            receipt, json.loads((project / ".concorde/install.json").read_text())
        )
        self.assertTrue((project / ".claude/skills/concorde/SKILL.md").is_file())

    @verifies("scenario.distribution.update-mark-failed")
    def test_an_update_failing_after_its_receipt_is_completed_again(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        first = install(
            project, package, d2=False, pi_runtime=False, dependencies=False
        )
        mark = project / ".concorde/update.json"
        mark.mkdir()
        with self.assertRaises(InstallError) as refused:
            update(project, package)
        self.assertEqual("install_failed", refused.exception.code)
        self.assertIn(str(mark), str(refused.exception))
        # The install finished and replaced the receipt; only the mark is missing.
        receipt = json.loads((project / ".concorde/install.json").read_text())
        self.assertEqual(first["files"], receipt["files"])
        self.assertFalse((project / ".concorde/install.json.partial").exists())
        self.assertFalse(mark.is_file())
        self.assertFalse((project / ".concorde/update.json.partial").exists())
        mark.rmdir()
        update(project, package)
        self.assertEqual("unvalidated", json.loads(mark.read_text())["state"])

    @verifies("scenario.distribution.update-marked-again")
    def test_an_update_of_a_marked_project_keeps_the_earlier_before_state(self):
        package = package_copy(self)
        project = package.parent / "project"
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, d2=False, pi_runtime=False, dependencies=False)
        update(project, package)
        mark = project / ".concorde/update.json"
        # As if the first update had come from an older Concorde and rebound its Protocol.
        earlier = json.loads(mark.read_text())
        earlier.update(
            {
                "from": "0.0.1",
                "commits": {"from": "a" * 40, "to": None},
                "protocol": {
                    "from": {"version": "1.0.0", "digest": "sha256:old"},
                    "to": {"version": "2.0.0", "digest": "sha256:new"},
                },
            }
        )
        mark.write_text(json.dumps(earlier, indent=2) + "\n")
        # An update that fails before its own mark leaves the earlier one as it was.
        (project / ".concorde/update.json.partial").mkdir()
        with self.assertRaises(InstallError) as refused:
            update(project, package)
        self.assertEqual("install_failed", refused.exception.code)
        self.assertEqual(earlier, json.loads(mark.read_text()))
        (project / ".concorde/update.json.partial").rmdir()
        state = update(project, package)["update"]
        self.assertEqual(state, json.loads(mark.read_text()))
        self.assertEqual("0.0.1", state["from"])
        self.assertEqual("a" * 40, state["commits"]["from"])
        self.assertEqual(earlier["protocol"], state["protocol"])

    @verifies("scenario.distribution.install-docsite-template")
    def test_an_installed_concorde_proposes_the_docsite_scaffold(self):
        package = package_copy(self)
        # Neither a working site's files nor a stray suffix is part of the template.
        (package / "docsite/node_modules/left-over").mkdir(parents=True)
        (package / "docsite/node_modules/left-over/index.ts").write_text("x\n")
        (package / "docsite/notes.txt").write_text("not shipped\n")
        project = package.parent / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        install(project, package, pi_runtime=False, d2=False, dependencies=False)
        framework = project / ".concorde/framework"
        shipped = {
            path.relative_to(framework).as_posix(): path.read_bytes()
            for path in (framework / "docsite").rglob("*")
            if path.is_file()
        }
        self.assertEqual(template_files(package), shipped)
        self.assertIn("docsite/scaffold/deploy-docsite.yml", shipped)
        concorde = str(project / ".concorde/bin/concorde")
        proposed = subprocess.run(
            [concorde, "init", "--propose", "--name", "Demo"],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, proposed.returncode, proposed.stdout + proposed.stderr)
        proposal = package.parent / "proposal.json"
        proposal.write_text(json.dumps(json.loads(proposed.stdout)["result"]))
        applied = subprocess.run(
            [concorde, "init", "--apply", "--proposal", str(proposal)],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, applied.returncode, applied.stdout + applied.stderr)
        docsite = subprocess.run(
            [concorde, "docsite", "--propose", "--github-pages"],
            cwd=project,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, docsite.returncode, docsite.stdout + docsite.stderr)
        envelope = json.loads(docsite.stdout)
        self.assertEqual("proposal", envelope["status"], docsite.stdout)
        paths = {entry["path"] for entry in envelope["result"]["proposal"]["files"]}
        self.assertEqual(
            set(adapter_files(package))
            | {"docsite/site.json", ".github/workflows/deploy-docsite.yml"},
            paths,
        )

    @verifies("scenario.distribution.install-docsite-template-refused")
    def test_an_unsafe_docsite_template_installs_nothing(self):
        package = package_copy(self)
        (package / "docsite/linked.md").symlink_to(package / "docsite/README.md")
        project = package.parent / "project"
        project.mkdir()
        with self.assertRaises(InstallError) as raised:
            install(project, package, pi_runtime=False, d2=False, dependencies=False)
        self.assertEqual("invalid_docsite_template", raised.exception.code)
        self.assertIn("docsite/linked.md", str(raised.exception))
        self.assertEqual(
            "input",
            refusal("invalid_docsite_template", "x")["unhandled"]["reason"],
        )
        self.assertEqual([], list(project.iterdir()))

    def test_install_refuses_stale_guidance(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        (package / "prompts/main-session/skill.md").write_text(
            (package / "prompts/main-session/skill.md").read_text() + "\nNew.\n"
        )
        with self.assertRaises(InstallError) as raised:
            install(project, package, pi_runtime=False, dependencies=False)
        self.assertEqual("stale_build", raised.exception.code)
        self.assertFalse((project / ".claude").exists())


class D2InstallTests(unittest.TestCase):
    @verifies("scenario.distribution.install-d2-refused")
    def test_a_d2_archive_that_does_not_match_its_pin_installs_nothing(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        with self.assertRaises(InstallError) as raised:
            install(
                project,
                package,
                fetch=fake_d2(self, package, corrupt=True),
                dependencies=False,
            )
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
            install(
                project, package, pi_runtime=False, fetch=offline, dependencies=False
            )
        self.assertEqual("d2_unavailable", raised.exception.code)
        self.assertIn(
            "github.com/d2lang/d2/releases/download/v0.9.0", str(raised.exception)
        )
        self.assertIn("network is unreachable", str(raised.exception))
        self.assertEqual([], list(project.iterdir()))

    @verifies("scenario.distribution.install-without-d2")
    def test_install_without_d2_leaves_the_program_to_the_developer(self):
        package = package_copy(self)
        project = package.parent / "project"
        project.mkdir()
        receipt = install(
            project, package, pi_runtime=False, d2=False, dependencies=False
        )
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
