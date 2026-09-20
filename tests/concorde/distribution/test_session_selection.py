import shutil
import tempfile
import unittest
from pathlib import Path

from concorde.distribution.build import (
    BuildError,
    build,
    write_build,
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
        write_build(self.root)
        self.pi_entry = self.root / "generated/session/pi/concorde-session.ts"
        self.runtime = self.root / "scripts/run-operation.py"

    @verifies(
        "scenario.distribution.private-selection",
        "scenario.distribution.build-checkout-skills-user-invoked",
    )
    def test_source_build_has_no_ambient_registration_and_selection_is_exact(self):
        for relative in (".agents", ".claude", ".pi/extensions/concorde-session.ts"):
            self.assertFalse((self.root / relative).exists())
        self.assertEqual(
            {
                p.relative_to(self.root / ".pi").as_posix()
                for p in (self.root / ".pi").rglob("*")
                if p.is_file()
            },
            {
                "extensions/concorde-coordinator.ts",
                "agents/maintenance-worker.md",
                "agents/tester.md",
                "extensions/concorde-observe.ts",
            },
        )
        selected = select_session(
            self.root, mode="test", pi_entry=self.pi_entry, runtime=self.runtime
        )
        self.assertEqual(self.pi_entry.read_text(), selected["pi_entry"]["content"])
        self.assertTrue(selected["fresh_context"])
        self.assertFalse(selected["fork_context"])
        self.assertFalse(selected["inherit_catalogs"])
        self.assertFalse(selected["discover_catalogs"])
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
            "concorde-context-solve",
            str(self.root.parent / "SKILL.md"),
            str(self.root / "missing/SKILL.md"),
        ):
            with self.subTest(path=path), self.assertRaises(BuildError):
                select_session(
                    self.root, mode="test", pi_entry=Path(path), runtime=self.runtime
                )
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="maintenance",
                pi_entry=self.pi_entry,
                runtime=self.runtime,
            )
        self.pi_entry.write_text("modified")
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="test",
                pi_entry=self.pi_entry,
                runtime=self.runtime,
            )
        write_build(self.root)
        self.runtime.write_text("changed runtime")
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="test",
                pi_entry=self.pi_entry,
                runtime=self.runtime,
            )

    @verifies("scenario.distribution.private-selection")
    def test_aliased_entry_and_empty_tester_selection_are_rejected(self):
        with self.assertRaises(BuildError):
            select_session(self.root, mode="test", pi_entry=None, runtime=self.runtime)
        content = self.pi_entry.read_bytes()
        self.pi_entry.unlink()
        other = self.root / "other.md"
        other.write_bytes(content)
        self.pi_entry.symlink_to(other)
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="test",
                pi_entry=self.pi_entry,
                runtime=self.runtime,
            )
        self.pi_entry.unlink()
        write_build(self.root)
        selected = select_session(
            self.root, mode="maintenance", pi_entry=None, runtime=self.runtime
        )
        self.assertIsNone(selected["pi_entry"])

    @verifies("scenario.distribution.private-selection")
    def test_saved_selection_is_reverified_before_runtime_use(self):
        import json
        from concorde.distribution.session_selection import load_selection

        selected = select_session(
            self.root, mode="test", pi_entry=self.pi_entry, runtime=self.runtime
        )
        path = self.root / ".concorde/work/selection.json"
        path.parent.mkdir(parents=True, exist_ok=True)
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
                    "--pi-entry",
                    "missing",
                ]
            )
        self.assertNotEqual(0, code)
        self.assertEqual("select-session", json.loads(output.getvalue())["tool"])
        request = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-context-solve",
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
            self.assertEqual(3, json_main(self.root, "concorde-context-solve", runner))
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
            self.root, mode="test", pi_entry=self.pi_entry, runtime=self.runtime
        )
        path = self.root / ".concorde/work/selection.json"
        path.parent.mkdir(parents=True, exist_ok=True)
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
            "operation_id": "concorde-context-solve",
            "mode": "describe-policy",
            "configuration": None,
            "input": typed(
                "concorde-context-solve-request",
                {"target_id": "module.project", "task": "Inspect disposable project"},
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
            self.assertEqual(0, json_main(self.root, "concorde-context-solve", runner))
        self.assertEqual(project, observed["host"].project_root)
        self.assertEqual(self.root, observed["host"].package_root)
        self.assertEqual(
            str(self.root), observed["host"].session_provenance["candidate"]
        )

    @verifies("scenario.distribution.private-selection")
    def test_transitive_runtime_sources_and_entire_catalog_are_bound(self):
        import json
        from concorde.distribution.session_selection import (
            load_selection,
            save_selection,
        )

        selected = select_session(
            self.root, mode="test", pi_entry=self.pi_entry, runtime=self.runtime
        )
        path = self.root / ".concorde/work/selection.json"
        save_selection(self.root, path, selected)
        for relative in (
            "pi/extensions/concorde-session.ts",
            "pi/extensions/concorde-worker.ts",
            "pi/package-lock.json",
            "scripts/requirements.lock",
            "src/concorde/harness/entry.py",
            "prompts/operation-guidance/concorde-plan.md",
            "generated/agents/planner.md",
            "generated/session/pi/concorde-session.ts",
        ):
            source = self.root / relative
            before = source.read_bytes()
            try:
                source.write_bytes(before + b"\n")
                with self.subTest(relative=relative), self.assertRaises(BuildError):
                    load_selection(self.root, path)
            finally:
                source.write_bytes(before)
        value = json.loads(path.read_text())
        for key in ("content", "digest"):
            changed = json.loads(json.dumps(value))
            changed["pi_entry"]["catalog"][key] += "changed"
            path.write_text(json.dumps(changed))
            with self.subTest(key=key), self.assertRaises(BuildError):
                load_selection(self.root, path)
        path.write_text(json.dumps(value))
        # A legitimate rebuild also invalidates an already-issued selection.
        source = self.root / "pi/extensions/concorde-session.ts"
        source.write_text(source.read_text() + "\n// changed\n")
        write_build(self.root)
        with self.assertRaises(BuildError):
            load_selection(self.root, path)

    @verifies("scenario.distribution.private-selection")
    def test_scratch_only_legacy_and_unknown_selection_fields_fail_closed(self):
        import json
        from concorde.distribution.cli import create_parser
        from concorde.distribution.session_selection import (
            load_selection,
            save_selection,
        )

        selected = select_session(
            self.root, mode="test", pi_entry=self.pi_entry, runtime=self.runtime
        )
        for relative in (
            "selection.json",
            "generated/session/selection.json",
            ".concorde/runs/selection.json",
            "src/selection.json",
        ):
            with self.subTest(relative=relative), self.assertRaises(BuildError):
                save_selection(self.root, self.root / relative, selected)
        path = self.root / ".concorde/work/selection.json"
        save_selection(self.root, path, selected)
        for value in (
            {**selected, "schema_version": 1},
            {**selected, "skills": []},
            {**selected, "fork_context": True},
            {**selected, "fork_context": 0},
        ):
            path.write_text(json.dumps(value))
            with self.assertRaises(BuildError):
                load_selection(self.root, path)
        path.write_text('{"schema_version":2,"schema_version":2}')
        with self.assertRaises(BuildError):
            load_selection(self.root, path)
        with self.assertRaises(SystemExit):
            create_parser().parse_args(
                [
                    "select-session",
                    "--mode",
                    "test",
                    "--runtime",
                    str(self.runtime),
                    "--skill",
                    str(self.pi_entry),
                ]
            )
        with self.assertRaises(TypeError):
            select_session(self.root, mode="test", skill_paths=[], runtime=self.runtime)
        path.unlink()
        path.symlink_to(self.pi_entry)
        with self.assertRaises(BuildError):
            save_selection(self.root, path, selected)

    @verifies("scenario.distribution.private-selection")
    def test_source_symlink_ancestors_and_foreign_runtime_are_refused(self):
        with self.assertRaises(BuildError):
            select_session(
                self.root,
                mode="test",
                pi_entry=self.pi_entry,
                runtime=REPOSITORY_ROOT / "scripts/run-operation.py",
            )
        source = self.root / "pi/extensions"
        moved = self.root / "moved-extensions"
        source.rename(moved)
        source.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(BuildError):
            select_session(
                self.root, mode="test", pi_entry=self.pi_entry, runtime=self.runtime
            )

    @verifies("scenario.distribution.private-selection")
    def test_linked_source_redirect_is_refused_before_runner(self):
        import io
        import json
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from concorde.harness.entry import json_main

        request = {
            "type_id": "concorde-operation-invocation",
            "schema_version": 3,
            "operation_id": "concorde-plan",
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
                    "CONCORDE_SESSION_SELECTION": str(
                        self.root / ".concorde/work/selection.json"
                    ),
                    "CONCORDE_STUDIO_URL": "",
                },
            ),
            patch(
                "concorde.harness.change_worktree.git",
                return_value=SimpleNamespace(returncode=0, stdout="/same/git\n"),
            ),
            patch("pathlib.Path.cwd", return_value=self.root.parent),
            patch("sys.argv", ["run-operation.py"]),
            patch("sys.stdin", io.StringIO(json.dumps(request))),
            patch("sys.stdout", output),
        ):
            self.assertEqual(3, json_main(self.root, "concorde-plan", runner))
        self.assertEqual(
            "workspace_mismatch", json.loads(output.getvalue())["errors"][0]["code"]
        )
        runner.assert_not_called()

    @verifies("scenario.distribution.private-selection")
    def test_run_archive_keeps_pi_bytes_without_loading_claim(self):
        import json
        from concorde.harness.host import OperationHost
        from concorde.harness.status_store import record_run

        selection = select_session(
            self.root, mode="test", pi_entry=self.pi_entry, runtime=self.runtime
        )
        host = OperationHost(self.root, self.root, session_provenance=selection)
        record_run(host, operation="concorde-plan")
        directory = self.root / ".concorde/runs" / host.invocation_id
        record = json.loads((directory / "run.json").read_text())
        self.assertEqual(2, record["schema_version"])
        self.assertNotIn("skill_provenance", record)
        self.assertIsNone(record["pi_provenance"]["execution_evidence"])
        self.assertEqual(
            selection["pi_entry"]["digest"],
            record["pi_provenance"]["pi_entry"]["digest"],
        )
        self.assertEqual(
            [self.pi_entry.read_bytes()],
            [p.read_bytes() for p in (directory / "pi").glob("*.ts")],
        )

    @verifies("scenario.distribution.private-selection")
    def test_cli_saves_and_reverifies_without_primary_or_discovery_mutation(self):
        import io
        import json
        from unittest.mock import patch
        from concorde.distribution.cli import main

        path = self.root / ".concorde/work/pi-selection.json"
        with (
            patch(
                "concorde.harness.change_worktree._exclude_control_files"
            ) as excludes,
            patch("sys.stdout", io.StringIO()) as output,
        ):
            self.assertEqual(
                0,
                main(
                    [
                        "--project-root",
                        str(self.root),
                        "select-session",
                        "--mode",
                        "test",
                        "--pi-entry",
                        str(self.pi_entry),
                        "--runtime",
                        str(self.runtime),
                        "--output",
                        str(path),
                    ]
                ),
            )
        selected = json.loads(output.getvalue())["result"]
        self.assertEqual(2, selected["schema_version"])
        self.assertEqual(["-e", str(self.pi_entry)], selected["launch"]["pi_args"][-2:])
        self.assertEqual(
            str(self.root / "pi/extensions/concorde-session.ts"),
            selected["implementation"]["path"],
        )
        excludes.assert_not_called()
        with patch("sys.stdout", io.StringIO()) as output:
            self.assertEqual(
                0,
                main(
                    [
                        "--project-root",
                        str(self.root),
                        "select-session",
                        "--verify",
                        str(path),
                    ]
                ),
            )
        self.assertEqual(selected, json.loads(output.getvalue())["result"])
        with patch("sys.stdout", io.StringIO()):
            self.assertNotEqual(
                0,
                main(
                    [
                        "--project-root",
                        str(self.root),
                        "select-session",
                        "--verify",
                        str(path),
                        "--runtime",
                        str(self.runtime),
                    ]
                ),
            )
        for relative in (
            ".agents",
            ".claude",
            ".pi/extensions/concorde-session.ts",
            ".pi/skills",
            ".concorde/status",
            ".concorde/runs",
        ):
            self.assertFalse((self.root / relative).exists(), relative)
