"""The Kernel library: workspace bindings, delivery commits, typed values, file transactions and the
workspace and merge locks, on the Kernel's scenarios."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.kernel import binding, delivery, files, locking, schema
from concorde.kernel.refusal import KernelError
from concorde.spec.verification import verifies

IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@t")


def git(root: Path, *arguments: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["git", *IDENTITY, *arguments],
        cwd=root,
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def repository() -> Path:
    root = Path(os.path.realpath(tempfile.mkdtemp()))
    git(root, "init", "-q", "-b", "main")
    git(root, "commit", "-q", "--allow-empty", "-m", "start")
    return root


def commit(root: Path, message: str) -> str:
    git(
        root,
        "commit",
        "-q",
        "--allow-empty",
        "--cleanup=verbatim",
        "-F",
        "-",
        stdin=message,
    )
    return git(root, "rev-parse", "HEAD")


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.root = repository()
        self.traces = Path(tempfile.mkdtemp())

    def value(self, **changes) -> dict:
        return {
            "schema_version": 2,
            "workspace": "retry",
            "root": str(self.root),
            "branch": "concorde/retry",
            "base_commit": git(self.root, "rev-parse", "HEAD"),
            "goal": "Limit HTTP retries to three attempts.",
            "modules": ["module.http"],
            "traces": str(self.traces),
            "concorde": str(self.root / ".concorde"),
            **changes,
        }

    def place(self, text: str) -> Path:
        path = binding.path_of(self.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    @verifies("scenario.kernel.binding-read")
    def test_a_binding_is_read_whole_from_its_own_worktree(self):
        value = self.value()
        self.assertEqual(binding.path_of(self.root), binding.write(self.root, value))
        self.assertEqual(value, binding.load(self.root))
        self.assertEqual(self.root, binding.toplevel(self.root / ".concorde"))
        self.assertIsNone(binding.load(repository()))

    @verifies("scenario.kernel.binding-refused")
    def test_a_broken_binding_is_refused_whole(self):
        cases = (
            ("{not json", "binding_unreadable", ""),
            (
                json.dumps(self.value(workspace="Not A Name")),
                "binding_invalid",
                "/workspace",
            ),
            (json.dumps(self.value(traces="relative/folder")), "binding_invalid", None),
            (
                json.dumps(self.value(traces=str(self.traces / "missing"))),
                "binding_invalid",
                None,
            ),
        )
        for text, code, field in cases:
            with self.subTest(code=code, text=text[:40]):
                path = self.place(text)
                with self.assertRaises(KernelError) as refused:
                    binding.load(self.root)
                self.assertEqual(code, refused.exception.code)
                self.assertIn(str(path), str(refused.exception))
                if field:
                    self.assertIn(f"at {field}:", str(refused.exception))
        with self.assertRaises(KernelError) as refused:
            binding.write(self.root, self.value(workspace="Not A Name"))
        self.assertEqual("binding_invalid", refused.exception.code)

    @verifies("scenario.kernel.binding-copied")
    def test_a_copied_binding_is_refused(self):
        other = repository()
        self.place(json.dumps(self.value(root=str(other))))
        with self.assertRaises(KernelError) as refused:
            binding.load(self.root)
        self.assertEqual("binding_misplaced", refused.exception.code)
        self.assertIn(str(other), str(refused.exception))
        self.assertIn(str(self.root), str(refused.exception))


class DeliveryTests(unittest.TestCase):
    @verifies("scenario.kernel.deliveries-listed")
    def test_deliveries_are_recognized_by_their_subject_since_the_base(self):
        root = repository()
        base = commit(root, delivery.message("retry", "Before the base."))
        first = commit(root, delivery.message("retry", "Limit retries."))
        commit(root, delivery.message("other", "Another workspace."))
        commit(root, "an ordinary commit\n")
        second = commit(root, delivery.message("retry", "Limit retries."))
        self.assertEqual(
            [{"commit": first, "mismatches": []}, {"commit": second, "mismatches": []}],
            delivery.deliveries(root, "main", base, "retry"),
        )
        self.assertEqual(
            "concorde: deliver retry\n\nLimit retries.",
            git(root, "log", "-1", "--format=%B", second),
        )

    @verifies("scenario.kernel.delivery-merge-unverified")
    def test_a_merge_commit_with_the_subject_does_not_verify(self):
        root = repository()
        base = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "-q", "-b", "side")
        commit(root, "side work\n")
        git(root, "checkout", "-q", "main")
        commit(root, "main work\n")
        git(root, "merge", "-q", "--no-ff", "side", "-m", "concorde: deliver retry")
        [listed] = delivery.deliveries(root, "main", base, "retry")
        self.assertEqual(git(root, "rev-parse", "HEAD"), listed["commit"])
        self.assertEqual(1, len(listed["mismatches"]))
        self.assertIn("2 parent(s)", listed["mismatches"][0])
        with self.assertRaises(KernelError) as refused:
            delivery.deliveries(root, "no-such-branch", base, "retry")
        self.assertEqual("git_failed", refused.exception.code)
        self.assertIn("git log", str(refused.exception))
        self.assertIn("no-such-branch", str(refused.exception))


NOTE = {
    "type": "object",
    "additionalProperties": False,
    "required": ["text"],
    "properties": {"text": {"type": "string", "minLength": 1}},
}


class TypedValueTests(unittest.TestCase):
    def setUp(self):
        # Each test registers types of its own, and the registry is the process's.
        self.registry = patch.dict(schema._TYPES, {})
        self.registry.start()
        self.addCleanup(self.registry.stop)

    @verifies("scenario.kernel.registration-repeated")
    def test_registering_a_type_again_changes_nothing_or_is_refused(self):
        schema.register("example-note", 1, NOTE)
        schema.register("example-note", 1, json.loads(json.dumps(NOTE)))
        for version, other in ((2, NOTE), (1, {**NOTE, "required": []})):
            with (
                self.subTest(version=version),
                self.assertRaises(KernelError) as refused,
            ):
                schema.register("example-note", version, other)
            self.assertEqual("duplicate_type", refused.exception.code)
        self.assertEqual(1, schema.type_version("example-note"))
        value = schema.typed("example-note", {"text": "kept"})
        self.assertEqual(
            {"type_id": "example-note", "schema_version": 1, "data": {"text": "kept"}},
            value,
        )

    @verifies("scenario.kernel.registration-dialect")
    def test_a_schema_outside_the_registered_dialect_is_refused(self):
        outside = {
            "oneOf": {"oneOf": [NOTE, {"type": "null"}]},
            "defs": {"$defs": {"note": NOTE}, "type": "object"},
            "local": {"$ref": "#/$defs/note"},
            "types": {"type": ["string", "null"]},
            "format": {"type": "string", "format": "email"},
            "bounds": {"type": "string", "minLength": 3, "maxLength": 2},
        }
        for name, value in outside.items():
            with self.subTest(name), self.assertRaises(KernelError) as refused:
                schema.register(f"example-{name}", 1, value)
            self.assertEqual("invalid_input", refused.exception.code)
            with self.assertRaises(KernelError):
                schema.type_version(f"example-{name}")
        record = {
            "type": "object",
            "properties": {"child": {"$ref": "#/$defs/node"}},
            "$defs": {
                "node": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/node2"}]},
                "node2": {
                    "type": "object",
                    "properties": {"child": {"$ref": "#/$defs/node"}},
                },
            },
        }
        schema.validate({"child": {"child": {"child": None}}}, record)
        with self.assertRaises(KernelError) as refused:
            schema.validate({"child": {"child": 1}}, record)
        # The alternative that fails names where it lies.
        self.assertEqual(
            ("invalid_field", "/child"),
            (refused.exception.code, refused.exception.field),
        )
        with self.assertRaises(KernelError) as refused:
            schema.validate({}, {"$ref": "#/$defs/missing", "$defs": {}})
        self.assertEqual("invalid_input", refused.exception.code)

    @verifies("scenario.kernel.typed-embedded")
    def test_a_typed_value_is_checked_with_every_value_it_embeds(self):
        schema.register(
            "example-batch",
            1,
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["runs"],
                "properties": {
                    "runs": {"type": "array", "items": {"$ref": "example-run"}}
                },
            },
        )
        run = {"type_id": "example-run", "schema_version": 1, "data": {"text": "one"}}
        batch = {
            "type_id": "example-batch",
            "schema_version": 1,
            "data": {"runs": [run]},
        }
        with self.assertRaises(KernelError) as refused:
            schema.validate_typed(batch)
        self.assertEqual(
            ("unknown_type", "/data/runs/0"),
            (refused.exception.code, refused.exception.field),
        )
        schema.register("example-run", 1, NOTE)
        checked = schema.validate_typed(batch, "example-batch")
        self.assertEqual(batch, checked)
        self.assertIsNot(batch["data"]["runs"][0], checked["data"]["runs"][0])
        for broken, code, field in (
            (
                {**run, "schema_version": 2},
                "unsupported_version",
                "/data/runs/0/schema_version",
            ),
            (
                {**run, "type_id": "example-batch"},
                "incompatible_handoff",
                "/data/runs/0/type_id",
            ),
            ({**run, "data": {"text": ""}}, "invalid_field", "/data/runs/0/data/text"),
        ):
            with self.subTest(code), self.assertRaises(KernelError) as refused:
                schema.validate_typed({**batch, "data": {"runs": [broken]}})
            self.assertEqual(
                (code, field), (refused.exception.code, refused.exception.field)
            )
        with self.assertRaises(KernelError) as refused:
            schema.validate_typed(run, "example-batch")
        self.assertEqual("incompatible_handoff", refused.exception.code)


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "a.txt").write_text("a\n")
        (self.root / "b.txt").write_text("b\n")

    def changes(self) -> list[dict]:
        return [
            files.file_change(self.root, "a.txt", "A\n"),
            files.file_change(self.root, "b.txt", "B\n"),
        ]

    def contents(self) -> dict[str, str]:
        return {
            path.name: path.read_text()
            for path in sorted(self.root.iterdir())
            if path.is_file()
        }

    @verifies("scenario.kernel.transaction-stale")
    def test_a_stale_change_writes_nothing(self):
        changes = self.changes()
        (self.root / "b.txt").write_text("changed meanwhile\n")
        with self.assertRaises(KernelError) as refused:
            files.apply_files(self.root, changes, {"a.txt", "b.txt"})
        self.assertEqual(
            ("stale_proposal", "b.txt"),
            (refused.exception.code, refused.exception.field),
        )
        self.assertEqual(
            {"a.txt": "a\n", "b.txt": "changed meanwhile\n"}, self.contents()
        )
        with self.assertRaises(KernelError) as refused:
            files.apply_files(self.root, self.changes(), {"a.txt"})
        self.assertEqual("permission_denied", refused.exception.code)
        for malformed in (
            [],
            [{"path": "a.txt"}],
            [*self.changes(), self.changes()[0]],
            [{"path": "../a.txt", "before_digest": None, "content": ""}],
        ):
            with (
                self.subTest(malformed=malformed),
                self.assertRaises(KernelError) as refused,
            ):
                files.apply_files(self.root, malformed, {"a.txt", "b.txt", "../a.txt"})
            self.assertEqual("invalid_proposal", refused.exception.code)
        self.assertEqual(
            {"a.txt": "a\n", "b.txt": "changed meanwhile\n"}, self.contents()
        )

    @verifies("scenario.kernel.transaction-restored")
    def test_a_failed_final_check_restores_every_file(self):
        failure = RuntimeError("the final check failed")

        def check():
            raise failure

        changes = [
            files.file_change(self.root, "a.txt", "A\n"),
            files.file_change(self.root, "new/c.txt", "C\n"),
        ]
        with self.assertRaises(RuntimeError) as raised:
            files.apply_files(self.root, changes, {"a.txt", "new/c.txt"}, verify=check)
        self.assertIs(failure, raised.exception)
        self.assertEqual("a\n", (self.root / "a.txt").read_text())
        self.assertFalse((self.root / "new/c.txt").exists())
        self.assertEqual(
            ["a.txt", "b.txt"],
            files.apply_files(self.root, self.changes(), {"a.txt", "b.txt"}),
        )
        self.assertEqual({"a.txt": "A\n", "b.txt": "B\n"}, self.contents())

    @verifies("scenario.kernel.transaction-unrestored")
    def test_a_refused_restoration_is_named(self):
        failure = RuntimeError("the final check failed")
        write = files._write

        def refusing(path: Path, data: bytes) -> None:
            if path.name == "a.txt" and data == b"a\n":
                raise PermissionError(13, "Permission denied", str(path))
            write(path, data)

        def check():
            raise failure

        with (
            patch.object(files, "_write", refusing),
            self.assertRaises(KernelError) as raised,
        ):
            files.apply_files(
                self.root, self.changes(), {"a.txt", "b.txt"}, verify=check
            )
        error = raised.exception
        self.assertEqual(("system_error", "a.txt"), (error.code, error.field))
        self.assertIn("a.txt", str(error))
        self.assertIn("still holds", str(error))
        self.assertIs(failure, error.causes[0])
        self.assertIsInstance(error.causes[1], PermissionError)
        self.assertEqual(2, len(error.causes))
        self.assertEqual({"a.txt": "A\n", "b.txt": "b\n"}, self.contents())


class LockTests(unittest.TestCase):
    @verifies("scenario.kernel.busy-lock-refused")
    def test_a_busy_lock_is_refused_naming_its_holder(self):
        concorde = Path(tempfile.mkdtemp())
        with locking.merge_lock(
            concorde, "`concorde task merge` of task t1", task="t1"
        ):
            with self.assertRaises(KernelError) as refused:
                with locking.merge_lock(concorde, "an Issue write", wait=0):
                    pass
            self.assertEqual("merge_busy", refused.exception.code)
            self.assertIn("`concorde task merge` of task t1", str(refused.exception))
            self.assertIn("task t1", locking.merge_lock_holder(concorde))
        with locking.workspace_lock(concorde, "t2", "implement run r-1"):
            with self.assertRaises(KernelError) as refused:
                with locking.workspace_lock(concorde, "t2", "delivery run r-2"):
                    pass
            self.assertEqual("workspace_busy", refused.exception.code)
            self.assertIn("implement run r-1", str(refused.exception))
        self.assertIsNone(locking.merge_lock_holder(concorde))
        self.assertIsNone(locking.workspace_lock_holder(concorde, "t2"))

    @verifies("scenario.kernel.busy-lock-refused")
    def test_a_workspace_retired_while_awaited_is_refused(self):
        concorde = Path(tempfile.mkdtemp())
        waiting = threading.Event()
        outcome: list[BaseException | None] = []

        def taker():
            try:
                with locking.workspace_lock(
                    concorde,
                    "t2",
                    "a run",
                    wait=30,
                    waiting=lambda holder: waiting.set(),
                    retake=False,
                ):
                    outcome.append(None)
            except KernelError as error:
                outcome.append(error)

        from concorde.kernel.tracing import locks

        path = locking.workspace_lock_path(concorde, "t2")
        with locks.hold(path, "`concorde task close` of task t2", remove=True):
            thread = threading.Thread(target=taker)
            thread.start()
            self.assertTrue(waiting.wait(10))
        thread.join(30)
        [error] = outcome
        self.assertEqual("workspace_retired", error.code)


if __name__ == "__main__":
    unittest.main()
