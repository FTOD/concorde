"""Candidate worktree scenarios, each exercised through the lifecycle and status store code.

Every test runs in disposable Git repositories: a primary worktree on branch ``trunk`` and a
linked candidate on branch ``task``.
"""

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.change_worktree import (
    GUIDANCE_END,
    GUIDANCE_START,
    WorktreeBoundaryError,
    bind_owner,
    create_worktree,
    ensure_change,
    git,
    git_value,
    read_change,
    refresh_registry,
    require_isolated_worktree,
    resume_owner,
    save_change,
    snapshot_tree,
)
from concorde.harness.host import OperationHost
from concorde.harness.status_store import (
    all_status,
    coordinate_child,
    declare_section,
    put_section,
    read_status,
    record_run,
    run_path,
    status_path,
    write_run,
    write_status,
)
from concorde.spec.repository import SpecError, digest
from concorde.spec.typed_data import STRING, artifact, obj, register, typed
from concorde.spec.verification import verifies
from concorde.harness import status_store
from concorde.spec import typed_data

# Provider sections declared only by these tests; the store must treat them like any provider's.
NOTE_TYPE = "worktrees-fixture-note"
OTHER_TYPE = "worktrees-fixture-other"
NOTE_SECTION = "worktrees-fixture"
OTHER_SECTION = "worktrees-fixture-other"


def setUpModule():
    # Registered only while this module's tests run: the registries are process-global, and a
    # fixture type left behind would change every later build's exported schemas.
    register(NOTE_TYPE, 1, obj({"note": STRING}))
    register(OTHER_TYPE, 1, obj({"count": {"type": "integer"}}))
    declare_section(NOTE_SECTION, NOTE_TYPE)
    declare_section(OTHER_SECTION, OTHER_TYPE)


def tearDownModule():
    for type_id in (NOTE_TYPE, OTHER_TYPE):
        typed_data._TYPES.pop(type_id, None)
        typed_data._ORIGINS.pop(type_id, None)
    for name in (NOTE_SECTION, OTHER_SECTION):
        status_store._SECTIONS.pop(name, None)


def files_below(root: Path) -> dict[str, bytes]:
    """Every regular file below ``root`` outside Git's own storage, with its bytes."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(root).parts[:1]
    }


class CandidateFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.primary = self.directory / "primary"
        self.primary.mkdir()
        git(self.primary, "init", "-q", "-b", "trunk")
        git(self.primary, "config", "user.name", "Test")
        git(self.primary, "config", "user.email", "test@example.invalid")
        (self.primary / "file.txt").write_text("base\n")
        (self.primary / "AGENTS.md").write_text("# Project policy\nKeep it.\n")
        git(self.primary, "add", ".")
        git(self.primary, "commit", "-qm", "base")
        self.candidate = self.directory / "candidate"
        git(self.primary, "worktree", "add", "-q", "-b", "task", str(self.candidate))

    def status_bytes(self, change_id: str) -> bytes:
        return (self.primary / status_path(change_id)).read_bytes()

    def index_entries(self, root: Path) -> str:
        return git_value(root, "ls-files", "-s")


class CreationTests(CandidateFixture, unittest.TestCase):
    def repository_state(self):
        return (
            git_value(self.primary, "branch", "--list", "--format=%(refname)"),
            git_value(self.primary, "worktree", "list", "--porcelain"),
            all_status(self.primary),
        )

    @verifies("scenario.worktrees.create-candidate-refused")
    def test_linked_or_detached_origin_creates_nothing(self):
        before = self.repository_state()
        with self.assertRaises(SpecError) as linked:
            create_worktree(self.candidate, {"task": "Nested change"})
        self.assertEqual("workspace_mismatch", linked.exception.code)
        self.assertEqual(before, self.repository_state())

        git(self.primary, "checkout", "-q", "--detach")
        before = self.repository_state()
        with self.assertRaises(SpecError) as detached:
            create_worktree(self.primary, {"task": "Detached change"})
        self.assertEqual("workspace_mismatch", detached.exception.code)
        self.assertEqual(before, self.repository_state())
        self.assertEqual([], all_status(self.primary))

    @verifies("scenario.worktrees.guidance-rollback")
    def test_failed_registration_restores_or_removes_agents_md(self):
        # Tracked runtime records make the status write refuse after guidance was appended.
        tracked = self.primary / ".concorde/runs/historical/result"
        tracked.parent.mkdir(parents=True)
        tracked.write_bytes(b"project owned")
        git(self.primary, "add", ".")
        git(self.primary, "commit", "-qm", "tracked runtime record")
        for existing in (True, False):
            with self.subTest(existing=existing):
                root = self.directory / f"candidate-{existing}"
                git(self.primary, "worktree", "add", "-q", "-b", root.name, str(root))
                agents = root / "AGENTS.md"
                if existing:
                    agents.write_bytes(b"# Existing policy\r\nKeep original bytes.\r\n")
                    agents.chmod(0o751)
                    before = agents.read_bytes()
                else:
                    agents.unlink()
                with self.assertRaises(SpecError) as refused:
                    ensure_change(root, task={"task": "work"})
                self.assertEqual("invalid_worktree_state", refused.exception.code)
                if existing:
                    self.assertEqual(before, agents.read_bytes())
                    self.assertEqual(0o751, agents.stat().st_mode & 0o777)
                else:
                    self.assertFalse(agents.exists())
                self.assertFalse((root / "CLAUDE.md").exists())
                self.assertIsNone(read_change(root))
                self.assertFalse((self.primary / ".concorde/status").exists())


class OwnershipTests(CandidateFixture, unittest.TestCase):
    @verifies("scenario.worktrees.owner-restored")
    def test_omitted_owner_fields_are_restored_from_the_record(self):
        ensure_change(
            self.candidate,
            task={"task": "Implement the change", "constraints": ["Keep the API"]},
        )
        owner = {
            "target_id": "module.example",
            "focus_id": "module.example.focus",
            "task": "Implement the change",
            "constraints": ["Keep the API"],
        }
        bind_owner(self.candidate, owner)
        recorded = read_change(self.candidate, required=True)
        self.assertEqual(
            owner, {field: recorded[field] for field in owner}, "owner recorded"
        )
        for omitted in (
            {"target_id": "module.example"},
            {"target_id": "module.example", "task": "Implement the change"},
            {"task": "Implement the change", "constraints": ["Keep the API"]},
        ):
            with self.subTest(omitted=sorted(omitted)):
                restored = resume_owner(read_change(self.candidate), omitted)
                self.assertEqual(owner, {field: restored[field] for field in owner})
        self.assertEqual(recorded, read_change(self.candidate))

    @verifies("scenario.worktrees.change-id-unique")
    def test_another_worktree_cannot_register_a_taken_identity(self):
        other = self.directory / "other"
        git(self.primary, "worktree", "add", "-q", "-b", "other", str(other))
        first = ensure_change(
            self.candidate, task={"task": "first"}, change_id="change.shared"
        )
        with self.assertRaises(SpecError) as refused:
            ensure_change(other, task={"task": "second"}, change_id="change.shared")
        self.assertEqual("workspace_mismatch", refused.exception.code)
        self.assertEqual([first], all_status(self.primary))
        self.assertIsNone(read_change(other))

    @verifies("scenario.worktrees.incarnation")
    def test_recreated_worktree_is_unbound_but_a_renamed_branch_stays_bound(self):
        old = ensure_change(self.candidate, task={"task": "old"})
        head = git_value(self.candidate, "rev-parse", "HEAD")
        git(self.primary, "worktree", "remove", "--force", str(self.candidate))
        git(self.primary, "worktree", "add", "-q", str(self.candidate), "task")
        self.assertEqual(head, git_value(self.candidate, "rev-parse", "HEAD"))
        self.assertEqual("task", git_value(self.candidate, "branch", "--show-current"))
        self.assertIsNone(read_change(self.candidate))
        summary = refresh_registry(self.primary)["worktrees"][0]
        self.assertEqual(("unmanaged", None), (summary["status"], summary["change_id"]))
        self.assertEqual(old, read_status(self.primary, old["change_id"]))

        live = ensure_change(self.candidate, task={"task": "live"})
        self.assertNotEqual(old["change_id"], live["change_id"])
        git(self.candidate, "branch", "-m", "renamed")
        bound = read_change(self.candidate, required=True)
        self.assertEqual(live["change_id"], bound["change_id"])
        save_change(self.candidate, bound)
        self.assertEqual(
            "renamed", read_status(self.primary, live["change_id"])["branch"]
        )

    @verifies("scenario.worktrees.child-owner")
    def test_user_session_records_and_releases_a_task_subagent(self):
        state = ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        launched = []
        real = subprocess.Popen

        def spy(arguments, *rest, **options):
            launched.append(arguments)
            return real(arguments, *rest, **options)

        with patch.object(subprocess, "Popen", spy):
            owned = coordinate_child(
                self.primary,
                state["change_id"],
                child_id="writer-1",
                phase="maintenance",
            )
            stored = read_status(self.primary, state["change_id"])
            self.assertEqual(owned, stored)
            self.assertEqual("writer-1", stored["child"]["id"])
            self.assertEqual("maintenance", stored["child"]["phase"])
            self.assertTrue(stored["child"]["fresh_context"])
            self.assertFalse(stored["child"]["fork_context"])
            self.assertEqual("maintenance", stored["phase"])
            released = coordinate_child(
                self.primary,
                state["change_id"],
                child_id="writer-1",
                phase="maintenance",
                release=True,
            )
            tester = coordinate_child(
                self.primary, state["change_id"], child_id="tester-1", phase="test"
            )
        self.assertIsNone(released["child"])
        self.assertEqual("handoff", released["phase"])
        self.assertEqual(("tester-1", "test"), (tester["child"]["id"], tester["phase"]))
        # Recording ownership only runs Git; it never starts a session.
        self.assertTrue(launched)
        self.assertTrue(all(command[0] == "git" for command in launched), launched)

    @verifies("scenario.worktrees.child-owner-conflict")
    def test_a_second_task_subagent_cannot_take_an_owned_worktree(self):
        state = ensure_change(self.candidate, task={"task": "work"}, mode="maintenance")
        coordinate_child(
            self.primary, state["change_id"], child_id="writer-1", phase="maintenance"
        )
        before = self.status_bytes(state["change_id"])
        with self.assertRaises(SpecError) as conflict:
            coordinate_child(
                self.primary, state["change_id"], child_id="writer-2", phase="test"
            )
        self.assertEqual("workspace_mismatch", conflict.exception.code)
        self.assertEqual(before, self.status_bytes(state["change_id"]))

        with self.assertRaises(SpecError) as linked:
            coordinate_child(
                self.candidate, state["change_id"], child_id="writer-1", phase="test"
            )
        self.assertEqual("primary_session_required", linked.exception.code)
        with self.assertRaises(SpecError) as unknown:
            coordinate_child(
                self.primary, "change.unknown", child_id="writer-2", phase="test"
            )
        self.assertEqual("unknown_change", unknown.exception.code)
        self.assertEqual(before, self.status_bytes(state["change_id"]))

    @verifies("scenario.worktrees.child-owner-conflict")
    def test_another_change_on_the_same_worktree_cannot_take_its_owner(self):
        from concorde.delivery.manual_merge import record_manual_merge

        first = ensure_change(
            self.primary, task={"task": "first"}, allow_primary=True, mode="direct"
        )
        record_manual_merge(
            self.primary, first["change_id"], commit="HEAD", cleanup="retained"
        )
        second = ensure_change(
            self.primary, task={"task": "second"}, allow_primary=True, mode="direct"
        )
        self.assertEqual(first["path"], second["path"])
        coordinate_child(
            self.primary, first["change_id"], child_id="writer-1", phase="task"
        )
        owners = (
            self.status_bytes(first["change_id"]),
            self.status_bytes(second["change_id"]),
        )
        with self.assertRaises(SpecError) as refused:
            coordinate_child(
                self.primary, second["change_id"], child_id="writer-2", phase="task"
            )
        self.assertEqual("workspace_mismatch", refused.exception.code)
        self.assertEqual(
            owners,
            (
                self.status_bytes(first["change_id"]),
                self.status_bytes(second["change_id"]),
            ),
        )


class PersistenceTests(CandidateFixture, unittest.TestCase):
    @verifies("scenario.worktrees.primary-unavailable")
    def test_status_and_run_writes_stop_without_the_primary(self):
        state = ensure_change(self.candidate, task={"task": "work"})
        state["phase"] = "implementation"
        before = files_below(self.candidate)
        moved = self.primary.with_name("temporarily-unavailable")
        self.primary.rename(moved)
        try:
            for write in (
                lambda: write_status(self.candidate, copy.deepcopy(state)),
                lambda: save_change(self.candidate, copy.deepcopy(state)),
                lambda: write_run(
                    self.candidate, ".concorde/runs/run-1/result.json", b"{}"
                ),
            ):
                with self.assertRaises(SpecError) as stopped:
                    write()
                self.assertEqual("primary_unavailable", stopped.exception.code)
            self.assertEqual(before, files_below(self.candidate))
            self.assertFalse((self.candidate / ".concorde").exists())
        finally:
            moved.rename(self.primary)
        self.assertEqual(
            "created", read_status(self.primary, state["change_id"])["phase"]
        )

    @verifies("scenario.worktrees.stale-status")
    def test_second_writer_of_one_revision_is_refused(self):
        state = ensure_change(self.candidate, task={"task": "work"})
        first = read_change(self.candidate, required=True)
        second = read_change(self.candidate, required=True)
        self.assertEqual(first["revision"], second["revision"])
        put_section(first, NOTE_SECTION, {"note": "first writer"})
        first["phase"] = "planning"
        save_change(self.candidate, first)
        stored = read_status(self.primary, state["change_id"])
        put_section(second, NOTE_SECTION, {"note": "second writer"})
        second["phase"] = "review"
        for write in (save_change, write_status):
            with self.assertRaises(SpecError) as refused:
                write(self.candidate, copy.deepcopy(second))
            self.assertEqual("stale_status", refused.exception.code)
        self.assertEqual(stored, read_status(self.primary, state["change_id"]))
        self.assertEqual("planning", stored["phase"])
        self.assertEqual(
            {"note": "first writer"}, stored["sections"][NOTE_SECTION]["data"]
        )

    @verifies("scenario.worktrees.provider-section")
    def test_declared_section_value_is_stored_unchanged(self):
        state = ensure_change(self.candidate, task={"task": "work"})
        put_section(state, OTHER_SECTION, {"count": 1})
        save_change(self.candidate, state)
        before = read_status(self.primary, state["change_id"])
        value = typed(NOTE_TYPE, {"note": "provider value"})
        state["sections"][NOTE_SECTION] = copy.deepcopy(value)
        save_change(self.candidate, state)
        after = read_status(self.primary, state["change_id"])
        self.assertEqual(value, after["sections"][NOTE_SECTION])
        self.assertEqual(before["revision"] + 1, after["revision"])
        self.assertEqual(
            before["sections"][OTHER_SECTION], after["sections"][OTHER_SECTION]
        )
        unchanged = {
            key: item
            for key, item in after.items()
            if key not in {"sections", "revision"}
        }
        self.assertEqual(
            {key: item for key, item in before.items() if key in unchanged}, unchanged
        )

    @verifies("scenario.worktrees.provider-section-refused")
    def test_undeclared_or_mistyped_section_is_refused(self):
        state = ensure_change(self.candidate, task={"task": "work"})
        put_section(state, NOTE_SECTION, {"note": "kept"})
        save_change(self.candidate, state)
        before = self.status_bytes(state["change_id"])
        with self.assertRaises(SpecError) as undeclared_put:
            put_section(copy.deepcopy(state), "worktrees-undeclared", {"note": "x"})
        self.assertEqual("invalid_worktree_state", undeclared_put.exception.code)
        mistyped = {"type_id": NOTE_TYPE, "schema_version": 1, "data": {"note": 3}}
        for name, value in (
            ("worktrees-undeclared", typed(NOTE_TYPE, {"note": "x"})),
            (NOTE_SECTION, mistyped),
            (NOTE_SECTION, typed(OTHER_TYPE, {"count": 2})),
        ):
            with self.subTest(section=name, value=value):
                attempt = copy.deepcopy(state)
                attempt["sections"][name] = value
                with self.assertRaises(SpecError) as refused:
                    write_status(self.candidate, attempt)
                self.assertEqual("invalid_worktree_state", refused.exception.code)
                self.assertEqual(before, self.status_bytes(state["change_id"]))

    @verifies("scenario.worktrees.run-record")
    def test_run_record_keeps_provenance_and_artifacts(self):
        change = ensure_change(self.candidate, task={"task": "work"})
        package = self.directory / "package"
        (package / "generated").mkdir(parents=True)
        (package / "scripts").mkdir()
        manifest = b'{"fixture": "build manifest"}\n'
        (package / "generated/build-manifest.json").write_bytes(manifest)
        (package / "scripts/run-operation.py").write_bytes(b"# launcher\n")
        (self.candidate / "file.txt").write_text("draft edit\n")
        host = OperationHost(self.candidate, package)
        input_tree = snapshot_tree(self.candidate, change)
        record_run(host, operation="fixture-operation", task={"task": "work"})

        accepted = self.candidate / "accepted.md"
        accepted.write_bytes(b"accepted plan\n")
        changed = self.candidate / "changed.md"
        changed.write_bytes(b"recorded bytes\n")
        kept, stale = (
            artifact(self.candidate, "plan", "accepted.md"),
            artifact(self.candidate, "note", "changed.md"),
        )
        changed.write_bytes(b"bytes changed after the envelope\n")
        envelope = {"status": "succeeded", "output": {"plan": kept, "note": stale}}
        record_run(host, operation="fixture-operation", result=envelope)

        relative = f".concorde/runs/{host.invocation_id}/run.json"
        record = json.loads(run_path(self.primary, relative).read_text())
        self.assertFalse((self.candidate / ".concorde/runs").exists())
        self.assertEqual(str(self.candidate.resolve()), record["source_worktree"])
        self.assertEqual("task", record["branch"])
        self.assertEqual(
            git_value(self.candidate, "rev-parse", "HEAD"), record["commit"]
        )
        self.assertEqual(input_tree, record["input_tree"])
        self.assertEqual(
            "draft edit\n",
            git_value(self.candidate, "show", f"{record['input_tree']}:file.txt")
            + "\n",
        )
        self.assertTrue(record["dirty"])
        self.assertEqual(str(package.resolve()), record["runtime"]["root"])
        self.assertEqual(digest(b"# launcher\n"), record["runtime"]["launcher_digest"])
        self.assertEqual(digest(manifest), record["build_digest"])
        self.assertEqual(
            manifest, run_path(self.primary, record["build_artifact"]).read_bytes()
        )
        self.assertEqual(("succeeded", envelope), (record["status"], record["result"]))
        self.assertEqual(change["change_id"], record["change_id"])
        by_id = {item["id"]: item for item in record["artifacts"]}
        self.assertEqual("archived", by_id["plan"]["status"])
        self.assertEqual(
            b"accepted plan\n",
            run_path(self.primary, by_id["plan"]["archive"]).read_bytes(),
        )
        self.assertEqual(
            ("unavailable", None), (by_id["note"]["status"], by_id["note"]["archive"])
        )
        archived = {
            str(path.relative_to(self.primary))
            for path in (self.primary / ".concorde/runs").rglob("*")
            if path.is_file()
        }
        self.assertFalse(any(path.endswith("changed.md") for path in archived))


class BoundaryTests(CandidateFixture, unittest.TestCase):
    def assert_refused(self, root, *, allow: bool = False):
        before = files_below(self.directory)
        with self.assertRaises(WorktreeBoundaryError) as refused:
            require_isolated_worktree(root, allow_primary_worktree=allow)
        # Every refusal says how to obtain an isolated worktree.
        self.assertIn(
            "create a unique branch and linked worktree", str(refused.exception).lower()
        )
        self.assertEqual(before, files_below(self.directory))
        return str(refused.exception)

    @verifies("scenario.worktrees.boundary-refused")
    def test_primary_symlink_missing_or_failing_probe_is_refused(self):
        status = git_value(self.primary, "status", "--porcelain")
        message = self.assert_refused(self.primary)
        self.assertIn("not allowed in the primary Git worktree", message)
        self.assertEqual(status, git_value(self.primary, "status", "--porcelain"))

        link = self.directory / "link"
        link.symlink_to(self.candidate, target_is_directory=True)
        self.assertIn("symlink", self.assert_refused(link, allow=True))

        missing = self.directory / "missing"
        self.assertIn("not a directory", self.assert_refused(missing, allow=True))
        self.assertFalse(missing.exists())

        # Inside a repository whose HEAD probe fails: no commit exists yet.
        empty = self.directory / "empty"
        empty.mkdir()
        git(empty, "init", "-q")
        self.assertIn("preflight failed", self.assert_refused(empty))
        self.assertEqual("", git_value(empty, "status", "--porcelain"))


class SnapshotTests(CandidateFixture, unittest.TestCase):
    def draft(self):
        (self.candidate / "file.txt").write_text("changed\n")
        (self.candidate / "added.txt").write_text("new file\n")
        for relative in (".concorde/work/module.x/plan.md", ".concorde/runs/r/result"):
            path = self.candidate / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("local control state\n")

    def show(self, tree: str, path: str) -> bytes:
        return subprocess.run(
            ["git", "-C", str(self.candidate), "show", f"{tree}:{path}"],
            capture_output=True,
            check=True,
        ).stdout

    @verifies("scenario.worktrees.deliverable-snapshot")
    def test_snapshot_drops_control_paths_and_the_recorded_guidance(self):
        original = (self.candidate / "AGENTS.md").read_bytes()
        state = ensure_change(self.candidate, task={"task": "work"})
        self.assertEqual({"AGENTS.md": {"created": False}}, state["guidance"])
        self.draft()
        working = files_below(self.candidate)
        index = self.index_entries(self.candidate)
        status = self.status_bytes(state["change_id"])
        self.assertIn(GUIDANCE_START.encode(), working["AGENTS.md"])

        tree = snapshot_tree(self.candidate)
        paths = git_value(self.candidate, "ls-tree", "-r", "--name-only", tree)
        self.assertEqual(["AGENTS.md", "added.txt", "file.txt"], sorted(paths.split()))
        self.assertEqual(b"changed\n", self.show(tree, "file.txt"))
        self.assertEqual(b"new file\n", self.show(tree, "added.txt"))
        self.assertEqual(original, self.show(tree, "AGENTS.md"))
        self.assertEqual(working, files_below(self.candidate))
        self.assertEqual(index, self.index_entries(self.candidate))
        self.assertEqual(status, self.status_bytes(state["change_id"]))

    @verifies("scenario.worktrees.deliverable-snapshot")
    def test_created_guidance_file_is_omitted_only_when_empty(self):
        (self.candidate / "AGENTS.md").unlink()
        git(self.candidate, "commit", "-qam", "no guidance file")
        state = ensure_change(self.candidate, task={"task": "work"})
        self.assertEqual({"AGENTS.md": {"created": True}}, state["guidance"])
        tree = snapshot_tree(self.candidate)
        self.assertEqual("", git_value(self.candidate, "ls-tree", tree, "AGENTS.md"))
        agents = self.candidate / "AGENTS.md"
        agents.write_text("# New policy\n" + agents.read_text())
        tree = snapshot_tree(self.candidate)
        self.assertEqual(b"# New policy\n", self.show(tree, "AGENTS.md"))

    @verifies("scenario.worktrees.guidance-markers-edited")
    def test_edited_removed_or_duplicated_markers_block_the_snapshot(self):
        state = ensure_change(self.candidate, task={"task": "work"})
        agents = self.candidate / "AGENTS.md"
        guided = agents.read_text()
        block = guided[guided.index(GUIDANCE_START) :]
        variants = {
            "edited": guided.replace(
                "concorde-change-worktree:start", "concorde-change-worktree:begin"
            ),
            "end removed": guided.replace(GUIDANCE_END, "trailing user note\n"),
            "start removed": guided.replace(GUIDANCE_START, "\n"),
            "duplicated": guided + block,
        }
        for name, content in variants.items():
            with self.subTest(variant=name):
                agents.write_text(content)
                working = files_below(self.candidate)
                index = self.index_entries(self.candidate)
                status = self.status_bytes(state["change_id"])
                with self.assertRaises(SpecError) as blocked:
                    snapshot_tree(self.candidate)
                self.assertEqual("invalid_worktree_state", blocked.exception.code)
                self.assertEqual(content, agents.read_text())
                self.assertEqual(working, files_below(self.candidate))
                self.assertEqual(index, self.index_entries(self.candidate))
                self.assertEqual(status, self.status_bytes(state["change_id"]))


if __name__ == "__main__":
    unittest.main()
