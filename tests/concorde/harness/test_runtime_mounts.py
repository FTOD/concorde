"""Trusted runtime assets survive private /tmp without exposing a candidate tree."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.harness.worker_sandbox import (
    WorkerSandboxError,
    bubblewrap_argv,
    plan_mounts,
)
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class RuntimeMountTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(
            prefix="concorde-mount-test-", dir="/tmp"
        )
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.candidate = self.root / "candidate"
        self.extension = self.candidate / "pi/extensions/concorde-worker.ts"
        self.extension.parent.mkdir(parents=True)
        self.extension.write_text("// runtime asset\n")
        self.dependencies = self.candidate / "pi/node_modules"
        (self.dependencies / "typebox").mkdir(parents=True)
        (self.dependencies / "typebox/package.json").write_text("{}")
        self.workspace = self.root / "capsule"
        self.workspace.mkdir()
        (self.workspace / "reading.md").write_text("granted")
        (self.workspace / "output.txt").touch()
        self.run = self.root / "run"
        (self.run / "home").mkdir(parents=True)
        self.home = self.root / "developer"
        (self.home / ".ssh").mkdir(parents=True)
        (self.home / ".ssh/secret").write_text("secret")
        (self.candidate / "src").mkdir()
        (self.candidate / "src/private.py").write_text("PRIVATE SOURCE")
        (self.candidate / ".concorde").mkdir()
        (self.candidate / ".concorde/config.json").write_text("PRIVATE CONFIG")
        (self.root / "sibling-secret").write_text("SECRET")

    def plan(self, **changes):
        values = dict(
            runtime_files=(self.extension,),
            runtime_directories=(self.dependencies,),
            home=self.home,
        )
        values.update(changes)
        return plan_mounts(self.workspace, ("output.txt",), self.run, **values)

    @verifies("scenario.harness.worker-sandbox")
    def test_runtime_mounts_are_narrow_read_only_and_do_not_change_grants(self):
        plan = self.plan()
        self.assertEqual(
            (str(self.extension), str(self.dependencies)), plan.runtime_readonly
        )
        self.assertEqual((str(self.workspace / "output.txt"),), plan.writable)
        argv = bubblewrap_argv(plan, ["true"])
        extension_bind = argv.index(str(self.extension))
        self.assertEqual("--ro-bind", argv[extension_bind - 1])
        self.assertLess(argv.index("/tmp"), extension_bind)
        self.assertNotIn(str(self.candidate), argv)
        self.assertNotIn(str(self.candidate / "src"), argv)

    @verifies("scenario.harness.worker-sandbox")
    def test_missing_wrong_kind_noncanonical_and_masked_runtime_paths_are_refused(self):
        alias = self.root / "alias"
        alias.symlink_to(self.dependencies, target_is_directory=True)
        cases = (
            {"runtime_files": (self.root / "missing",)},
            {"runtime_files": (self.dependencies,)},
            {"runtime_directories": (self.extension,)},
            {"runtime_directories": (alias,)},
            {"runtime_directories": (Path("relative"),)},
            {"runtime_directories": (self.root / "candidate/../candidate/pi",)},
            {"runtime_files": (self.home / ".ssh/secret",)},
            {"runtime_directories": (self.home,)},
            {"runtime_directories": (Path("/tmp"),)},
            {"runtime_directories": (self.run,)},
            {"runtime_files": (self.workspace / "output.txt",)},
            {"runtime_directories": (self.workspace,)},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(WorkerSandboxError):
                self.plan(**changes)

    @verifies("scenario.harness.worker-sandbox")
    def test_dependency_symlinks_cannot_escape_the_admitted_subtree(self):
        link = self.dependencies / "escape"
        link.symlink_to(self.home / ".ssh")
        with self.assertRaises(WorkerSandboxError):
            self.plan()
        link.unlink()
        link.symlink_to(self.dependencies / "typebox", target_is_directory=True)
        self.plan()

    @verifies("scenario.harness.worker-sandbox")
    def test_runtime_mount_cannot_restore_another_worktree(self):
        from unittest.mock import patch

        with (
            patch(
                "concorde.harness.worker_sandbox._other_worktrees",
                return_value=(self.candidate,),
            ),
            self.assertRaises(WorkerSandboxError),
        ):
            self.plan()

    @verifies("scenario.harness.worker-sandbox")
    def test_real_process_sees_runtime_not_source_control_or_sibling_secrets(self):
        plan = self.plan()
        script = r"""
import json, sys
from pathlib import Path
candidate, root, workspace, home = map(Path, sys.argv[1:])
results = {
    'extension': (candidate / 'pi/extensions/concorde-worker.ts').is_file(),
    'dependency': (candidate / 'pi/node_modules/typebox/package.json').is_file(),
    'source': (candidate / 'src/private.py').exists(),
    'control': (candidate / '.concorde/config.json').exists(),
    'sibling': (root / 'sibling-secret').exists(),
    'secret': (home / '.ssh/secret').exists(),
    'reading': (workspace / 'reading.md').read_text(),
}
for name, path in (
    ('extension_write', candidate / 'pi/extensions/concorde-worker.ts'),
    ('dependency_write', candidate / 'pi/node_modules/typebox/package.json'),
    ('ungranted_write', workspace / 'reading.md'),
    ('granted_write', workspace / 'output.txt'),
):
    try:
        with path.open('r+'):
            pass
        results[name] = 'writable'
    except OSError:
        results[name] = 'denied'
print(json.dumps(results))
"""
        process = subprocess.run(
            bubblewrap_argv(
                plan,
                [
                    str(Path(sys.executable).resolve()),
                    "-c",
                    script,
                    str(self.candidate),
                    str(self.root),
                    str(self.workspace),
                    str(self.home),
                ],
            ),
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual(
            dict(
                extension=True,
                dependency=True,
                source=False,
                control=False,
                sibling=False,
                secret=False,
                reading="granted",
                extension_write="denied",
                dependency_write="denied",
                ungranted_write="denied",
                granted_write="writable",
            ),
            json.loads(process.stdout),
        )

    @verifies("scenario.harness.pi-worker-launch")
    def test_declared_children_admit_only_the_pinned_runtime_dependency_tree(self):
        from unittest.mock import patch
        from concorde.harness.pi_rpc import PiRpcError
        from concorde.harness.pi_worker import (
            ChildAgent,
            PiWorkerRuntime,
            WorkerExecutionError,
            WorkerLaunch,
        )

        launch = WorkerLaunch(
            worker="test",
            workspace=str(self.workspace),
            system_prompt="test",
            message="test",
            result_schema={"type": "object"},
            tools=("submit_result", "subagent"),
            child_tools=("read",),
            children=(ChildAgent("scout", "---\nname: scout\n---\nRead the grant."),),
        )
        with (
            patch("concorde.harness.pi_worker.unavailable_reason", return_value=None),
            patch("concorde.harness.pi_worker.plan_mounts") as mounts,
            patch("concorde.harness.pi_worker.create_placeholders", return_value=()),
            patch("concorde.harness.pi_worker.bubblewrap_argv", return_value=[]),
            patch(
                "concorde.harness.pi_worker.run_prompt", side_effect=PiRpcError("test")
            ),
            self.assertRaises(WorkerExecutionError),
        ):
            PiWorkerRuntime(
                REPOSITORY_ROOT,
                pi_executable="unused",
                credentials_dir=self.root / "absent",
            )(launch)
        self.assertEqual(
            (REPOSITORY_ROOT / "pi/node_modules",),
            mounts.call_args.kwargs["runtime_directories"],
        )

    @unittest.skipUnless(shutil.which("node"), "Node is not installed")
    @verifies("scenario.harness.worker-sandbox")
    def test_real_node_resolves_typebox_from_the_tmp_extension(self):
        source = REPOSITORY_ROOT / "pi/node_modules/typebox"
        if not source.is_dir():
            self.skipTest("locked Pi dependencies are not installed")
        shutil.copytree(source, self.dependencies / "typebox", dirs_exist_ok=True)
        shutil.copyfile(
            REPOSITORY_ROOT / "pi/extensions/concorde-worker.ts", self.extension
        )
        script = "const r=require('node:module').createRequire(process.argv[1]); console.log(typeof r('typebox').Type.Object)"
        process = subprocess.run(
            bubblewrap_argv(
                self.plan(), [shutil.which("node"), "-e", script, str(self.extension)]
            ),
            capture_output=True,
            text=True,
            timeout=10,
            env={"PATH": os.environ["PATH"]},
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("function", process.stdout.strip())
