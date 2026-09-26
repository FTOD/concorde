"""Task-type grants: levels per boundary set, union, shared files and the worktree they come from."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.grants import LEVELS, TASK_TYPES, context_identity, grant
from concorde.spec.repository import SpecRepository
from concorde.spec.repository_base import SpecError
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.spec_project import (
    SpecProject,
    module_document,
    sync_registry,
    uses,
)


def realization(identity, entries, pending=()):
    return {
        "id": identity,
        "type": "realization",
        "title": identity.rsplit(".", 1)[-1].title(),
        "meaning": "It binds files of the Module.",
        "entries": list(entries),
        "pending": list(pending),
    }


def document(module, title, realizations, used=()):
    return module_document(
        f"document.{module}",
        f"module.{module}",
        title,
        f"{title} answers one question.",
        f"### scenario.{module}.answer — {title} answers\n\n"
        f"- GIVEN a question\n- WHEN {title} is asked\n- THEN it answers\n",
        ("The design is one function.", list(realizations)),
        f"{title} is small.",
        uses=[uses(f"module.{target}", f"{title} reads {target}.") for target in used],
    )


class GrantTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.project = SpecProject(self.root)
        for path in ("src/a/one.py", "src/a/two.py", "src/bmod/b.py", "src/shared.py"):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text("value = 1\n")
        (self.root / "references/lib").mkdir(parents=True)
        (self.root / "references/lib/api.md").write_text("# API\n")
        self.project.module(
            "module.a",
            "specs/a/module.md",
            document(
                "a",
                "A",
                [
                    realization("realization.a.code", ["src/a/"]),
                    realization("realization.a.extra", ["src/b.py"], ["src/b.py"]),
                ],
                used=("b",),
            ),
        )
        self.project.module(
            "module.b",
            "specs/b/module.md",
            document("b", "B", [realization("realization.b.code", ["src/bmod/"])]),
        )
        self.project.module(
            "module.d",
            "specs/d/module.md",
            document("d", "D", [realization("realization.d.code", ["src/shared.py"])]),
        )
        self.project.update(
            "module.a",
            includes=[
                {
                    "kind": "external",
                    "target": "references/lib/",
                    "reason": "the library's API reference",
                }
            ],
        )

    def grant(self, modules, task_type, root=None):
        repository = (
            self.project.repository()
            if root is None
            else SpecRepository(root, REPOSITORY_ROOT)
        )
        return grant(repository, modules, task_type).value

    @staticmethod
    def levels(value):
        return {entry["path"]: entry["level"] for entry in value["entries"]}

    def own_documents(self, module):
        return {
            f"specs/{module}/module.md",
            f"specs/{module}/module.md.json",
            f"specs/{module}/obligations.md",
            f"specs/{module}/obligations.md.json",
        }

    @verifies("scenario.spec.grant-understand")
    def test_understand_reads_specs_and_names_code(self):
        value = self.grant(["module.a"], "understand")
        levels = self.levels(value)
        for path in self.own_documents("a") | self.own_documents("b"):
            self.assertEqual("ro", levels[path], path)
        self.assertEqual("names", levels["src/a/one.py"])
        self.assertEqual("names", levels["src/a/two.py"])
        self.assertEqual("names", levels["src/b.py"])
        self.assertEqual("ro", levels["references/lib/"])
        self.assertNotIn("rw", levels.values())
        self.assertFalse(any(path.startswith("src/bmod") for path in levels))
        self.assertFalse(any(path.startswith("specs/d") for path in levels))
        review = self.grant(["module.a"], "review-spec")
        self.assertEqual("review-spec", review["task_type"])
        self.assertEqual(value["entries"], review["entries"])

    @verifies("scenario.spec.grant-specify")
    def test_specify_writes_only_the_modules_own_documents(self):
        levels = self.levels(self.grant(["module.a"], "specify"))
        for path in self.own_documents("a"):
            self.assertEqual("rw", levels[path], path)
        for path in self.own_documents("b"):
            self.assertEqual("ro", levels[path], path)
        self.assertEqual("names", levels["src/a/one.py"])
        code = {
            path: level for path, level in levels.items() if path.startswith("src/")
        }
        self.assertEqual({"names"}, set(code.values()))

    @verifies("scenario.spec.grant-implement")
    def test_implement_writes_the_realization_including_pending_entries(self):
        levels = self.levels(self.grant(["module.a"], "implement"))
        self.assertEqual("rw", levels["src/a/"])
        self.assertEqual("rw", levels["src/b.py"])
        self.assertFalse((self.root / "src/b.py").exists())
        for path in self.own_documents("a"):
            self.assertEqual("ro", levels[path], path)
        self.assertNotIn("src/a/one.py", levels)

    @verifies("scenario.spec.grant-read-code")
    def test_test_and_review_code_read_the_realization(self):
        for task_type in ("test", "review-code"):
            with self.subTest(task_type=task_type):
                levels = self.levels(self.grant(["module.a"], task_type))
                self.assertEqual("ro", levels["src/a/"])
                self.assertEqual("ro", levels["specs/a/module.md"])
                self.assertNotIn("rw", levels.values())
                self.assertNotIn("src/a/one.py", levels)

    @verifies("scenario.spec.grant-project-implementation")
    def test_code_phases_read_the_whole_project_implementation(self):
        for task_type in ("implement", "test", "review-code", "code-to-spec"):
            with self.subTest(task_type=task_type):
                levels = self.levels(self.grant(["module.a"], task_type))
                # Another Module's code is read and run, never written.
                self.assertEqual("ro", levels["src/bmod/b.py"])
        for task_type in ("understand", "specify", "review-spec"):
            with self.subTest(task_type=task_type):
                levels = self.levels(self.grant(["module.a"], task_type))
                self.assertNotIn("src/bmod/b.py", levels)
                self.assertNotEqual("ro", levels.get("src/a/"))

    @verifies("scenario.spec.grant-code-to-spec")
    def test_code_to_spec_reads_the_realization_and_writes_the_spec(self):
        levels = self.levels(self.grant(["module.a"], "code-to-spec"))
        self.assertEqual("ro", levels["src/a/"])
        for path in self.own_documents("a"):
            self.assertEqual("rw", levels[path], path)
        writable = {path for path, level in levels.items() if level == "rw"}
        self.assertEqual(self.own_documents("a"), writable)

    @verifies("scenario.spec.grant-multi-module")
    def test_several_modules_receive_the_union_at_the_highest_level(self):
        value = self.grant(["module.b", "module.a"], "specify")
        self.assertEqual(["module.a", "module.b"], value["modules"])
        levels = self.levels(value)
        for path in self.own_documents("a") | self.own_documents("b"):
            self.assertEqual("rw", levels[path], path)
        paths = [entry["path"] for entry in value["entries"]]
        self.assertEqual(sorted(set(paths)), paths)

    @verifies("scenario.spec.grant-shared-file")
    def test_a_shared_file_needs_every_binding_module(self):
        self.project.write(
            "specs/a/module.md.json",
            json.dumps(self.with_shared_entry()),
        )
        sync_registry(self.root)
        with self.assertRaises(SpecError) as raised:
            self.grant(["module.a"], "implement")
        self.assertEqual("shared_file", raised.exception.code)
        self.assertIn("src/shared.py", str(raised.exception))
        self.assertIn("module.d", str(raised.exception))
        both = self.levels(self.grant(["module.a", "module.d"], "implement"))
        self.assertEqual("rw", both["src/shared.py"])
        alone = self.levels(self.grant(["module.a"], "understand"))
        self.assertEqual("names", alone["src/shared.py"])

    def installed_project(self, entries):
        """Module I binding ``entries`` in a project whose installer placed a skill and a
        workflow of its own and amended the project's settings."""
        for path in (
            ".claude/skills/concorde/SKILL.md",
            ".claude/workflows/concorde-brownfield.js",
            ".claude/settings.json",
            ".claude/agents/mine.md",
        ):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text("x\n")
        (self.root / ".concorde").mkdir(exist_ok=True)
        (self.root / ".concorde/install.json").write_text(
            json.dumps(
                {
                    "files": [
                        ".claude/skills/concorde/SKILL.md",
                        ".claude/workflows/concorde-brownfield.js",
                        ".concorde/bin/concorde",
                    ],
                    "amended": [".claude/settings.json", "CLAUDE.md"],
                }
            )
        )
        self.project.module(
            "module.i",
            "specs/i/module.md",
            document("i", "I", [realization("realization.i.files", entries)]),
        )

    @verifies("scenario.spec.grant-installed")
    def test_an_installed_file_is_never_writable(self):
        self.installed_project(
            [
                ".claude/skills/concorde/SKILL.md",
                ".claude/workflows/concorde-brownfield.js",
                ".claude/settings.json",
                ".claude/agents/mine.md",
            ]
        )
        self.assertEqual([], self.project.findings("CHK.binds.installed"))
        for task_type in ("implement", "code-to-spec", "test"):
            with self.subTest(task_type=task_type):
                levels = self.levels(self.grant(["module.i"], task_type))
                self.assertEqual("ro", levels[".claude/skills/concorde/SKILL.md"])
                self.assertEqual(
                    "ro", levels[".claude/workflows/concorde-brownfield.js"]
                )
        levels = self.levels(self.grant(["module.i"], "implement"))
        # A file the installer only amends, and the Module's own files, stay writable.
        self.assertEqual("rw", levels[".claude/settings.json"])
        self.assertEqual("rw", levels[".claude/agents/mine.md"])

    @verifies("scenario.spec.installed-exact")
    def test_a_directory_entry_may_not_cover_an_installed_file(self):
        self.installed_project([".claude/"])
        [finding] = self.project.findings("CHK.binds.installed")
        self.assertIn(
            "realization.i.files binds the directory .claude/", finding.message
        )
        self.assertIn(".claude/skills/concorde/SKILL.md", finding.message)
        self.assertIn(".claude/workflows/concorde-brownfield.js", finding.message)
        self.assertNotIn("settings.json", finding.message)
        self.assertIn(".concorde/install.json", finding.message)
        self.assertTrue(finding.remediation)

    def with_shared_entry(self):
        value = self.project.metadata("specs/a/module.md")
        for record in value["defines"]:
            if record["id"] == "realization.a.code":
                record["entries"] = ["src/a/", "src/shared.py"]
        return value

    @verifies("scenario.spec.grant-invalid")
    def test_an_unanswerable_request_gets_no_grant(self):
        before = sorted(str(p) for p in self.root.rglob("*"))
        for modules, task_type, code in (
            (["module.a"], "plan", "invalid_task_type"),
            (["module.missing"], "understand", "unknown_module"),
            ([], "understand", "invalid_input"),
            (["module.a", "module.a"], "understand", "invalid_input"),
        ):
            with self.subTest(code=code, modules=modules):
                with self.assertRaises(SpecError) as raised:
                    self.grant(modules, task_type)
                self.assertEqual(code, raised.exception.code)
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))
        self.assertEqual(7, len(TASK_TYPES))

    @verifies("scenario.spec.grant-worktree")
    def test_a_grant_comes_from_the_worktree_it_names(self):
        other = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(other)]))
        subprocess.run(["cp", "-a", f"{self.root}/.", str(other)], check=True)
        value = self.project.metadata("specs/a/module.md")
        for record in value["defines"]:
            if record["id"] == "realization.a.extra":
                record["entries"] = ["src/b.py", "lib/extra.py"]
                record["pending"] = ["src/b.py", "lib/extra.py"]
        (other / "specs/a/module.md.json").write_text(json.dumps(value, indent=2))
        sync_registry(other)
        task = self.grant(["module.a"], "implement", root=other)
        primary = self.grant(["module.a"], "implement", root=self.root)
        self.assertEqual("rw", self.levels(task)["lib/extra.py"])
        self.assertNotIn("lib/extra.py", self.levels(primary))
        self.assertNotEqual(task["context_identity"], primary["context_identity"])

    @verifies("scenario.spec.context-identity")
    def test_the_context_identity_changes_only_with_the_context(self):
        def identity():
            return context_identity(self.project.repository(), ["module.a"])

        first = identity()
        self.assertEqual(
            first, self.grant(["module.a"], "understand")["context_identity"]
        )
        (self.root / "src/a/one.py").write_text("value = 2\n")
        self.assertEqual(first, identity())
        path = self.root / "specs/b/module.md"
        path.write_text(path.read_text() + " ")
        changed = identity()
        self.assertNotEqual(first, changed)
        self.project.update(
            "module.a",
            includes=[
                {
                    "kind": "external",
                    "target": "references/lib/",
                    "reason": "the library's API reference",
                },
                {
                    "kind": "document",
                    "target": "document.b",
                    "reason": "B's entry, already selected by uses",
                },
            ],
        )
        redundant = identity()
        self.assertNotEqual(changed, redundant)

    @verifies("scenario.spec.grant-invalid")
    def test_the_grant_command_prints_the_envelope(self):
        command = [sys.executable, str(REPOSITORY_ROOT / "scripts/concorde.py")]
        ok = subprocess.run(
            [
                *command,
                "grant",
                "--root",
                str(self.root),
                "--modules",
                "module.a",
                "--type",
                "test",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, ok.returncode, ok.stdout + ok.stderr)
        payload = json.loads(ok.stdout)
        self.assertEqual(("grant", "success"), (payload["tool"], payload["status"]))
        self.assertEqual("test", payload["result"]["task_type"])
        bad = subprocess.run(
            [
                *command,
                "grant",
                "--root",
                str(self.root),
                "--modules",
                "module.a",
                "--type",
                "plan",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, bad.returncode)
        refused = json.loads(bad.stdout)
        self.assertEqual("invalid", refused["status"])
        # The refusal is Spec tooling's own error record: what, where, why and how to fix.
        error = refused["error"]
        self.assertEqual(
            ("invalid_task_type", "task_type"),
            (error["code"], error["location"]["field"]),
        )
        self.assertIn("'plan'", error["message"])
        self.assertIn("seven task types", error["reason"])
        self.assertIn("review-code", error["remediation"])


class ProtocolTableTests(unittest.TestCase):
    @verifies("scenario.spec.grant-understand")
    def test_the_levels_are_the_protocols_task_type_table(self):
        import re

        text = (REPOSITORY_ROOT / "protocol/model.yaml").read_text()
        table = {}
        for task_type, levels in re.findall(
            r"- id: ([a-z-]+)\n\s+levels: \{([^}]*)\}", text
        ):
            table[task_type] = dict(
                (key.strip(), value.strip())
                for key, value in (item.split(":") for item in levels.split(","))
            )
        words = {"none": None, "names": "names", "read": "ro", "write": "rw"}
        expected = {
            task_type: {name: words[level] for name, level in levels.items()}
            for task_type, levels in table.items()
        }
        self.assertEqual(expected, LEVELS)
        self.assertEqual(tuple(table), TASK_TYPES)


if __name__ == "__main__":
    unittest.main()
