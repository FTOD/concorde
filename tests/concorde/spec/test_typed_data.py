from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import ExitStack, chdir
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.paths import RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.development.configuration import apply_configuration, load_configuration, propose_configuration
from concorde.spec.typed_data import TypedDataError, artifact, decode, verify_artifacts, typed, validate_typed
from concorde.spec.verification import verifies
from tests.concorde.support.capability_json import CONFIGURATION


class TypedDataTests(unittest.TestCase):
    @verifies("scenario.spec.task-control-values")
    def test_task_control_values_validate_shape_without_rewriting_input(self):
        examples = {
            "concorde-task-scope-feedback": {"tasks_digest": "sha256:" + "a" * 64,
                                             "reason": "implementation_boundary"},
            "concorde-task-identity-constraints": {"reserved_task_ids": ["task.previous", "task.current"]},
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sentinel = root / ".concorde/worktree.json"
            sentinel.parent.mkdir()
            sentinel.write_bytes(b'{"sentinel": "unchanged"}\n')
            before_files = {path.relative_to(root): path.read_bytes()
                            for path in root.rglob("*") if path.is_file()}
            before_examples = json.dumps(examples, sort_keys=True)
            # Install lifecycle guards before filesystem guards so importing patch
            # targets is outside the measured validation region.
            boundaries = (
                "concorde.harness.change_worktree.save_change",
                "concorde.harness.change_worktree.save_target_state",
                "builtins.open", "io.open", "os.open", "os.read", "os.write",
                "os.stat", "os.lstat", "os.listdir", "os.scandir",
                "os.mkdir", "os.rmdir", "os.remove", "os.unlink",
                "os.rename", "os.replace", "os.truncate",
            )
            with chdir(root), ExitStack() as stack:
                guards = [stack.enter_context(patch(
                    boundary, side_effect=AssertionError(f"unexpected side effect: {boundary}")))
                    for boundary in boundaries]
                for name, data in examples.items():
                    value = typed(name, data)
                    before = json.dumps(value, sort_keys=True)
                    for _ in range(2):
                        self.assertEqual(value, validate_typed(value, name))
                        self.assertEqual(before, json.dumps(value, sort_keys=True))
                    with self.assertRaises(TypedDataError) as raised:
                        validate_typed({**value, "schema_version": 2}, name)
                    self.assertEqual(("unsupported_version", "/schema_version"),
                                     (raised.exception.code, raised.exception.field))
                    with self.assertRaises(TypedDataError) as raised:
                        typed(name, {**data, "authority": "write"})
                    self.assertEqual(("invalid_field", "/data/authority"),
                                     (raised.exception.code, raised.exception.field))
                    self.assertEqual(before, json.dumps(value, sort_keys=True))
                self.assertEqual([], typed("concorde-task-identity-constraints", {"reserved_task_ids": []})
                                 ["data"]["reserved_task_ids"])
                for ids, field in ((["duplicate", "duplicate"], "/data/reserved_task_ids"),
                                   ([""], "/data/reserved_task_ids/0"),
                                   ([" "], "/data/reserved_task_ids/0"),
                                   ([1], "/data/reserved_task_ids/0"),
                                   ("task.one", "/data/reserved_task_ids")):
                    with self.subTest(ids=ids), self.assertRaises(TypedDataError) as raised:
                        typed("concorde-task-identity-constraints", {"reserved_task_ids": ids})
                    self.assertEqual(("invalid_field", field),
                                     (raised.exception.code, raised.exception.field))
                for update, field in (({"tasks_digest": "sha256:" + "A" * 64}, "/data/tasks_digest"),
                                      ({"reason": "skip_validation"}, "/data/reason")):
                    with self.subTest(update=update), self.assertRaises(TypedDataError) as raised:
                        typed("concorde-task-scope-feedback", {**examples["concorde-task-scope-feedback"], **update})
                    self.assertEqual(("invalid_field", field),
                                     (raised.exception.code, raised.exception.field))
            for guard in guards:
                guard.assert_not_called()
            self.assertEqual(before_examples, json.dumps(examples, sort_keys=True))
            self.assertEqual(before_files, {path.relative_to(root): path.read_bytes()
                                           for path in root.rglob("*") if path.is_file()})

    def test_artifact_references_detect_staleness_missing_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "artifact.md"
            path.write_text("original")
            reference = artifact(root, "artifact.fixture", "artifact.md")
            verify_artifacts(root, reference)
            path.write_text("modified")
            with self.assertRaisesRegex(TypedDataError, "changed"):
                verify_artifacts(root, reference)
            path.unlink()
            with self.assertRaisesRegex(TypedDataError, "does not exist"):
                verify_artifacts(root, reference)
            (root / "other.md").write_text("original")
            path.symlink_to(root / "other.md")
            with self.assertRaisesRegex(TypedDataError, "symlink"):
                verify_artifacts(root, reference)

    @verifies("scenario.harness.typed-reject")
    def test_json_rejects_duplicate_fields_and_non_finite_numbers(self):
        for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value), self.assertRaises(TypedDataError):
                decode(value)

    def test_existing_configuration_migration_preserves_fields_and_rejects_stale_proposal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / ".concorde/config.json"
            path.parent.mkdir()
            original = {"profile_version": 12, "registry": ".concorde/specs.json", "project_setting": {"keep": True}}
            path.write_text(json.dumps(original))
            with self.assertRaises(TypedDataError):
                load_configuration(root)
            proposed = propose_configuration(root, CONFIGURATION)
            self.assertEqual(json.loads(path.read_text()), original)
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            path.write_text(json.dumps({**original, "new_setting": True}))
            self.assertEqual(apply_configuration(root, "accepted.json").status, "invalid")
            proposed = propose_configuration(root, CONFIGURATION)
            (root / "accepted.json").write_text(json.dumps(proposed.result["proposal"]))
            self.assertEqual(apply_configuration(root, "accepted.json").status, "success")
            self.assertEqual(json.loads(path.read_text())["project_setting"], {"keep": True})
            self.assertTrue(json.loads(path.read_text())["new_setting"])
            self.assertEqual(load_configuration(root), CONFIGURATION)
            self.assertEqual(apply_configuration(root, "accepted.json").status, "unchanged")


if __name__ == "__main__":
    unittest.main()
