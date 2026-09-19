import shutil
import tempfile
import unittest
from pathlib import Path

from concorde.distribution.build import (
    BuildError,
    build,
    write_build,
    write_published_skills,
)
from concorde.distribution.session_selection import select_session
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class SessionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("prompts", "protocol", "operations", "src", "pi", "scripts"):
            shutil.copytree(
                REPOSITORY_ROOT / directory,
                self.root / directory,
                ignore=shutil.ignore_patterns("node_modules", "__pycache__"),
            )
        write_published_skills(self.root)
        write_build(self.root)
        self.skill = self.root / "generated/session/claude/concorde-main/SKILL.md"
        self.runtime = self.root / "scripts/run-operation.py"

    @verifies(
        "scenario.distribution.private-selection",
        "scenario.distribution.build-checkout-skills-user-invoked",
    )
    def test_source_build_has_no_ambient_registration_and_selection_is_exact(self):
        for relative in (".agents", ".claude", ".pi"):
            self.assertFalse((self.root / relative).exists())
        selected = select_session(
            self.root, mode="test", skill_paths=[str(self.skill)], runtime=self.runtime
        )
        self.assertEqual(self.skill.read_text(), selected["skills"][0]["body"])
        self.assertTrue(selected["fresh_context"])
        self.assertFalse(selected["fork_context"])
        self.assertFalse(selected["inherit_skills"])
        self.assertFalse(selected["discover_skills"])
        self.assertFalse(selected["task_delegation"])
        self.assertIsNone(selected["execution_evidence"])
        self.assertTrue(selected["build_digest"].startswith("sha256:"))
        installed = build(self.root, framework_prefix=".concorde/framework")
        self.assertIn(
            ".pi/extensions/concorde-session.ts", [o.path for o in installed.outputs]
        )

    @verifies("scenario.distribution.private-selection")
    def test_selection_never_falls_back(self):
        for path in (
            "concorde-main",
            str(self.root.parent / "SKILL.md"),
            str(self.root / "missing/SKILL.md"),
        ):
            with self.subTest(path=path), self.assertRaises(BuildError):
                select_session(
                    self.root, mode="test", skill_paths=[path], runtime=self.runtime
                )
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="maintenance",
                skill_paths=[str(self.skill)],
                runtime=self.runtime,
            )
        self.skill.write_text("modified")
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="test",
                skill_paths=[str(self.skill)],
                runtime=self.runtime,
            )
        write_build(self.root)
        self.runtime.write_text("changed runtime")
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="test",
                skill_paths=[str(self.skill)],
                runtime=self.runtime,
            )

    @verifies("scenario.distribution.private-selection")
    def test_aliased_skill_and_empty_tester_selection_are_rejected(self):
        with self.assertRaises(BuildError):
            select_session(self.root, mode="test", skill_paths=[], runtime=self.runtime)
        content = self.skill.read_bytes()
        self.skill.unlink()
        other = self.root / "other.md"
        other.write_bytes(content)
        self.skill.symlink_to(other)
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="test",
                skill_paths=[str(self.skill)],
                runtime=self.runtime,
            )
        self.skill.unlink()
        write_build(self.root)
        selected = select_session(
            self.root, mode="maintenance", skill_paths=[], runtime=self.runtime
        )
        self.assertEqual([], selected["skills"])

    @verifies("scenario.distribution.private-selection")
    def test_saved_selection_is_reverified_before_runtime_use(self):
        import json
        from concorde.distribution.session_selection import load_selection

        selected = select_session(
            self.root, mode="test", skill_paths=[str(self.skill)], runtime=self.runtime
        )
        path = self.root / "selection.json"
        path.write_text(json.dumps(selected))
        self.assertEqual(selected, load_selection(self.root, path))
        selected["fork_context"] = True
        path.write_text(json.dumps(selected))
        with self.assertRaises(BuildError):
            load_selection(self.root, path)

    @verifies("scenario.distribution.private-selection")
    def test_cli_failure_keeps_selection_identity_and_private_selection_rejects_studio(
        self,
    ):
        import io
        import json
        from unittest.mock import Mock, patch
        from concorde.distribution.cli import main
        from concorde.harness.entry import json_main

        output = io.StringIO()
        with patch("sys.stdout", output):
            code = main(
                [
                    "--project-root",
                    str(self.root),
                    "select-session",
                    "--mode",
                    "test",
                    "--runtime",
                    str(self.runtime),
                    "--skill",
                    "missing",
                ]
            )
        self.assertNotEqual(0, code)
        self.assertEqual("select-session", json.loads(output.getvalue())["tool"])
        request = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-main",
            "mode": "execute",
            "configuration": None,
            "input": {},
        }
        runner = Mock()
        output = io.StringIO()
        with (
            patch.dict(
                "os.environ",
                {
                    "CONCORDE_STUDIO_URL": "http://not-candidate",
                    "CONCORDE_SESSION_SELECTION": str(self.root / "selection.json"),
                },
            ),
            patch("sys.argv", ["run-operation.py"]),
            patch("sys.stdin", io.StringIO(json.dumps(request))),
            patch("sys.stdout", output),
        ):
            self.assertEqual(3, json_main(self.root, "concorde-main", runner))
        self.assertEqual(
            "workspace_mismatch", json.loads(output.getvalue())["errors"][0]["code"]
        )
        runner.assert_not_called()

    @verifies("scenario.distribution.private-selection")
    def test_private_runtime_can_target_disposable_project_data_without_moving_code(
        self,
    ):
        import io
        import json
        from unittest.mock import patch
        from concorde.harness.entry import json_main
        from concorde.spec.typed_data import typed

        selection = select_session(
            self.root, mode="test", skill_paths=[str(self.skill)], runtime=self.runtime
        )
        path = self.root / "selection.json"
        path.write_text(json.dumps(selection))
        project = self.root / "disposable-project"
        project.mkdir()
        observed = {}

        def runner(data, runtime):
            observed["host"] = runtime.context.host
            return {"result": {"status": "described", "invocation_id": "fixture"}}

        request = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-main",
            "mode": "describe-policy",
            "configuration": None,
            "input": typed(
                "concorde-main-request", {"task": "Inspect disposable project"}
            ),
        }
        with (
            patch.dict(
                "os.environ",
                {"CONCORDE_STUDIO_URL": "", "CONCORDE_SESSION_SELECTION": str(path)},
            ),
            patch("sys.argv", ["run-operation.py"]),
            patch("sys.stdin", io.StringIO(json.dumps(request))),
            patch("sys.stdout", io.StringIO()),
            patch("pathlib.Path.cwd", return_value=project),
        ):
            self.assertEqual(0, json_main(self.root, "concorde-main", runner))
        self.assertEqual(project, observed["host"].project_root)
        self.assertEqual(self.root, observed["host"].package_root)
        self.assertEqual(
            str(self.root), observed["host"].session_provenance["candidate"]
        )
