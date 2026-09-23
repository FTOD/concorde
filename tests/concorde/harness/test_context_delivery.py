"""Task context: implementation contents, stage inputs, capsules and rechecks of frozen snapshots.

Every test freezes real snapshots of the shared-file project (A and B both bind
``source/shared.py``) with the production ``resolve_context``, then delivers or rechecks them with
the production capsule and recheck functions.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from concorde.harness.capsule import assemble_capsule, verify_capsule
from concorde.harness.change_worktree import git
from concorde.harness.context import recheck_context, resolve_context
from concorde.spec.repository import SpecError, digest
from concorde.spec.typed_data import decode
from concorde.spec.verification import verifies
from tests.concorde.support.shared_file_project import SharedFileFixture

TASK_INPUT = {
    "type_id": "concorde-implementation-task",
    "schema_version": 1,
    "data": {"plan": "Plan", "tasks": []},
}
PLAN_INPUT = {
    "type_id": "concorde-plan-artifact",
    "schema_version": 1,
    "data": {"plan": "Plan"},
}
IMPLEMENTATION_SCOPE = ("source/a.py", "source/shared.py")


def _files(directory: Path) -> set[str]:
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
    }


class ContextFixture(unittest.TestCase):
    def setUp(self):
        self.fixture = SharedFileFixture(self)
        self.fixture.setUp()
        self.root = self.fixture.root
        self.fixture.write("reference/lib/api.md", "## connect(url)\n")
        self.fixture.write("reference/lib/diagram.png", "binary")
        self.fixture.write("notes/private.md", "UNRELATED_PROJECT_FILE\n")
        self.fixture.declare_reference()

    def freeze(self, agent, **arguments):
        arguments.setdefault("task", "Adapt the shared value")
        return resolve_context(
            self.fixture.repository(), "module.a", agent=agent, **arguments
        )

    def refused(self, code, call, *arguments, **keywords):
        with self.assertRaises(SpecError) as raised:
            call(*arguments, **keywords)
        self.assertEqual(code, raised.exception.code, raised.exception)
        return raised.exception


class ImplementationContentsTests(ContextFixture):
    @verifies("scenario.context.implementation-contents")
    def test_only_implementation_readers_get_paths_and_digests(self):
        reviewer = self.freeze("code-reviewer").value
        self.assertEqual(
            [
                {
                    "id": path,
                    "path": path,
                    "digest": digest((self.root / path).read_bytes()),
                }
                for path in IMPLEMENTATION_SCOPE
            ],
            reviewer["implementation_artifacts"],
        )
        for agent in ("planner", "context-assessor"):
            with self.subTest(agent=agent):
                value = self.freeze(agent).value
                self.assertEqual([], value["implementation_artifacts"])
                self.assertNotIn(
                    digest((self.root / "source/a.py").read_bytes()),
                    self.freeze(agent).serialized,
                )


class SharedFileOtherAgentTests(ContextFixture):
    @verifies("scenario.context.shared-file-other-agents")
    def test_non_writers_are_bound_to_the_selected_module_alone(self):
        for agent in ("planner", "code-reviewer", "context-assessor"):
            with self.subTest(agent=agent):
                snapshot = self.freeze(agent)
                value = snapshot.value
                self.assertEqual("module.a", value["target_id"])
                self.assertEqual([], value["shared_bindings"])
                self.assertFalse(
                    [
                        source
                        for source in value["spec_resolution"]["sources"]
                        if source["path"].startswith("specs/b/")
                    ]
                )
                self.assertNotIn("specs/b/", snapshot.serialized)
        # The programmer of the same Module is the call that is bound to B.
        programmer = self.freeze("programmer", stage_inputs=(TASK_INPUT,)).value
        self.assertEqual(
            ["module.b"], [item["module_id"] for item in programmer["shared_bindings"]]
        )


class ExternalReferenceDeliveryTests(ContextFixture):
    @verifies("scenario.context.external-references-not-read")
    def test_non_readers_see_the_digest_but_receive_no_copy(self):
        repository = self.fixture.repository()
        (entry,) = repository.external_context("module.a")
        snapshot = self.freeze("context-assessor")
        self.assertEqual([entry.record()], snapshot.value["external_references"])
        capsule = self.root.parent / (self.root.name + "-capsule")
        self.addCleanup(shutil.rmtree, capsule, True)
        delivered = assemble_capsule(repository, snapshot, capsule)
        self.assertFalse([path for path in delivered if path.startswith("reference/")])
        self.assertFalse((capsule / "reference").exists())

    @verifies("scenario.context.external-reference-missing")
    def test_a_missing_checkout_stops_freezing(self):
        shutil.rmtree(self.root / "reference/lib")
        snapshots = []
        for agent in ("planner", "context-assessor"):
            with self.subTest(agent=agent):
                error = self.refused(
                    "invalid_reference",
                    lambda agent=agent: snapshots.append(self.freeze(agent)),
                )
                self.assertIn("reference/lib/", str(error))
        self.assertEqual([], snapshots)


class StageInputTests(ContextFixture):
    @verifies("scenario.context.stage-input-refused")
    def test_unadmitted_duplicate_or_missing_inputs_are_refused(self):
        snapshots = []
        for label, agent, inputs, require in (
            ("unadmitted type", "planner", (TASK_INPUT,), False),
            (
                "unadmitted for a definition without inputs",
                "code-reviewer",
                (PLAN_INPUT,),
                False,
            ),
            ("same type twice", "programmer", (TASK_INPUT, TASK_INPUT), False),
            ("launch without the required input", "programmer", (), True),
        ):
            with self.subTest(label):
                self.refused(
                    "incompatible_handoff",
                    lambda agent=agent, inputs=inputs, require=require: (
                        snapshots.append(
                            self.freeze(
                                agent, stage_inputs=inputs, require_inputs=require
                            )
                        )
                    ),
                )
        self.assertEqual([], snapshots)
        # A policy preview may omit a required input that does not exist yet; a launch may not.
        preview = self.freeze("programmer", require_inputs=False).value
        self.assertEqual([], preview["stage_inputs"])
        launch = self.freeze(
            "programmer", stage_inputs=(TASK_INPUT,), require_inputs=True
        ).value
        self.assertEqual([TASK_INPUT], launch["stage_inputs"])


class CapsuleTests(ContextFixture):
    def assemble(self, snapshot, name):
        directory = self.root.parent / f"{self.root.name}-{name}"
        self.addCleanup(shutil.rmtree, directory, True)
        return directory, assemble_capsule(
            self.fixture.repository(), snapshot, directory
        )

    @verifies("scenario.context.capsule")
    def test_capsules_hold_exact_copies_of_the_delivered_files_only(self):
        spec_a = [
            "specs/a/details.md",
            "specs/a/details.md.json",
            "specs/a/module.md",
            "specs/a/module.md.json",
            "specs/a/obligations.md",
            "specs/a/obligations.md.json",
        ]
        spec_b = [
            "specs/b/module.md",
            "specs/b/module.md.json",
            "specs/b/obligations.md",
            "specs/b/obligations.md.json",
        ]
        protocol = [
            ".concorde/protocol/kinds/module.md",
            ".concorde/protocol/principles.md",
        ]
        references = ["reference/lib/api.md"]
        for agent, inputs, expected in (
            ("planner", (), [*protocol, *spec_a, *references]),
            ("context-assessor", (), [*protocol, *spec_a]),
            (
                "code-reviewer",
                (),
                [*protocol, *spec_a, *references, *IMPLEMENTATION_SCOPE],
            ),
            ("programmer", (TASK_INPUT,), [*protocol, *spec_a, *spec_b, *references]),
        ):
            with self.subTest(agent=agent):
                snapshot = self.freeze(agent, stage_inputs=inputs)
                directory, delivered = self.assemble(snapshot, agent)
                self.assertEqual({*expected, "context.json"}, _files(directory))
                self.assertEqual(_files(directory), set(delivered))
                recorded = {
                    item["path"]: item["digest"]
                    for item in (
                        *snapshot.value["protocol"],
                        *snapshot.value["spec_resolution"]["sources"],
                        *(
                            source
                            for shared in snapshot.value["shared_bindings"]
                            for source in shared["spec_resolution"]["sources"]
                        ),
                        *snapshot.value["implementation_artifacts"],
                    )
                }
                for path in expected:
                    copy = (directory / path).read_bytes()
                    self.assertEqual((self.root / path).read_bytes(), copy, path)
                    self.assertEqual(digest(copy), delivered[path])
                    if path in recorded:
                        self.assertEqual(recorded[path], digest(copy), path)
                index = decode((directory / "context.json").read_text())
                if agent == "programmer":
                    self.assertEqual(str(self.root), index["native_workspace"])
                    self.assertEqual(
                        sorted(str(self.root / path) for path in IMPLEMENTATION_SCOPE),
                        sorted(index["intended_write_paths"]),
                    )
                    index = {
                        key: value
                        for key, value in index.items()
                        if key in snapshot.value
                    }
                else:
                    self.assertNotIn("intended_write_paths", index)
                self.assertEqual(snapshot.value, index)
                self.assertFalse((directory / "notes").exists())

    @verifies("scenario.context.capsule")
    def test_a_source_changed_after_freezing_is_not_delivered(self):
        snapshot = self.freeze("planner")
        entry = self.root / "specs/a/module.md"
        entry.write_text(entry.read_text() + "\nChanged after freezing.\n")
        directory = self.root.parent / f"{self.root.name}-stale"
        self.addCleanup(shutil.rmtree, directory, True)
        self.refused(
            "stale_context",
            assemble_capsule,
            self.fixture.repository(),
            snapshot,
            directory,
        )

    @verifies("scenario.context.capsule-changed")
    def test_a_changed_copy_fails_verification(self):
        for agent, path in (
            ("planner", "specs/a/module.md"),
            ("planner", "context.json"),
            ("planner", "reference/lib/api.md"),
            ("code-reviewer", "source/shared.py"),
        ):
            with self.subTest(agent=agent, path=path):
                snapshot = self.freeze(agent)
                directory, delivered = self.assemble(snapshot, f"{agent}-{len(path)}")
                repository = self.fixture.repository()
                verify_capsule(repository, snapshot, directory, delivered)
                copy = directory / path
                copy.write_bytes(copy.read_bytes() + b"\nedited copy\n")
                self.refused(
                    "stale_context",
                    verify_capsule,
                    repository,
                    snapshot,
                    directory,
                    delivered,
                )


class RecheckTests(ContextFixture):
    @verifies("scenario.context.programmer-recheck")
    def test_the_programmers_own_edits_do_not_stale_its_snapshot(self):
        (self.root / "source/a.py").unlink()
        snapshot = self.freeze("programmer", stage_inputs=(TASK_INPUT,))
        # Created, changed and removed implementation files of the selected Module.
        self.fixture.write("source/a.py", "def adapt(value):\n    return abs(value)\n")
        self.fixture.write(
            "source/shared.py", "def value():\n    return 43\n# PRIVATE_SOURCE_MARKER\n"
        )
        recheck_context(self.fixture.repository(), snapshot)
        (self.root / "source/shared.py").unlink()
        recheck_context(self.fixture.repository(), snapshot)
        for path in ("specs/a/module.md", "specs/b/module.md"):
            with self.subTest(path=path):
                document = self.root / path
                original = document.read_bytes()
                document.write_bytes(original + b"\nA changed promise.\n")
                self.refused(
                    "stale_context",
                    recheck_context,
                    self.fixture.repository(),
                    snapshot,
                )
                document.write_bytes(original)
        # The same implementation edits stale a reader's snapshot.
        self.fixture.write("source/shared.py", "def value():\n    return 42\n")
        reviewer = self.freeze("code-reviewer")
        self.fixture.write("source/shared.py", "def value():\n    return 44\n")
        self.refused(
            "stale_context", recheck_context, self.fixture.repository(), reviewer
        )

    @verifies("scenario.context.other-worktrees-move")
    def test_other_worktrees_may_move_while_a_call_runs(self):
        git(self.root, "init", "-q", "-b", "integration")
        git(self.root, "config", "user.name", "Concorde Test")
        git(self.root, "config", "user.email", "concorde-test@example.invalid")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "Fixture")
        others = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, others, True)
        first = others / "first"
        git(self.root, "worktree", "add", "-q", "-b", "first", str(first))
        snapshot = self.freeze("planner")
        listed = snapshot.value["workspace"]["active_worktrees"]
        self.assertEqual([str(first.resolve())], [item["path"] for item in listed])
        # Another worktree advances, a new one appears and the first is removed.
        (first / "source/extra.py").write_text("EXTRA = 1\n")
        git(first, "add", "-A")
        git(first, "commit", "-qm", "Advance")
        recheck_context(self.fixture.repository(), snapshot)
        git(self.root, "worktree", "add", "-q", "-b", "second", str(others / "second"))
        recheck_context(self.fixture.repository(), snapshot)
        git(self.root, "worktree", "remove", "--force", str(first))
        recheck_context(self.fixture.repository(), snapshot)
        # The current worktree's own facts are not exempt.
        git(self.root, "checkout", "-q", "-b", "elsewhere")
        self.refused(
            "stale_context", recheck_context, self.fixture.repository(), snapshot
        )


if __name__ == "__main__":
    unittest.main()
