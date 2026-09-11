"""Unit coverage for scratch preparation; full cold checks run separately without doubles."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.concorde.support.paths import REPOSITORY_ROOT


def load_wrapper():
    spec = importlib.util.spec_from_file_location(
        "repository_checks", REPOSITORY_ROOT / "docsite/tests/repository/run-checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(root: Path):
    return {str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
            for path in root.rglob("*")}


class RepositoryCheckPreparationTests(unittest.TestCase):
    def make_source(self, root, wrapper, *, stale=False):
        for name in wrapper.FILES:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fixture input\n")
        docsite = root / "docsite"
        docsite.mkdir()
        (docsite / "package.json").write_bytes(b'{"name": "checked-package"}\n')
        (docsite / "package-lock.json").write_bytes(
            b'{"name": "checked-package", "lockfileVersion": 3}\n')
        if stale:
            installed = docsite / "node_modules/vitest"
            installed.mkdir(parents=True)
            (installed / "vitest.mjs").write_bytes(b"stale installation must not be used\n")

    def test_prepares_copied_inputs_without_using_source_installation(self):
        for stale in (False, True):
            with self.subTest(stale=stale), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "source"
                wrapper = load_wrapper()
                self.make_source(root, wrapper, stale=stale)
                before = snapshot(root)
                calls = []

                def run(argv, *, cwd, env):
                    calls.append(list(argv))
                    if len(calls) == 1:
                        self.assertEqual(argv, ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"])
                        self.assertFalse(cwd.is_relative_to(root))
                        self.assertFalse((cwd / "node_modules").exists())
                        self.assertFalse((cwd / "node_modules").is_symlink())
                        for name in ("package.json", "package-lock.json"):
                            self.assertEqual((cwd / name).read_bytes(), (root / "docsite" / name).read_bytes())
                        (cwd / "node_modules").mkdir()
                        (cwd / "node_modules/prepared").write_bytes(b"scratch only")
                    else:
                        project = Path(env["PYTHONPATH"]).parent
                        self.assertEqual((project / "docsite/node_modules/prepared").read_bytes(), b"scratch only")
                        self.assertFalse((project / "docsite/node_modules").is_symlink())
                        (project / "generated-test-output").write_bytes(b"scratch only")
                    return subprocess.CompletedProcess(argv, 0)

                with patch.object(wrapper, "ROOT", root), patch.object(wrapper.subprocess, "run", side_effect=run):
                    self.assertEqual(wrapper.main(), 0)
                self.assertTrue(any("build" in argv for argv in calls[1:]))
                self.assertTrue(any("unittest" in argv for argv in calls[1:]))
                self.assertTrue(any("node_modules/vitest/vitest.mjs" in argv for argv in calls[1:]))
                self.assertEqual(snapshot(root), before)

    def test_failed_install_stops_checks_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            wrapper = load_wrapper()
            self.make_source(root, wrapper)
            before = snapshot(root)

            def fail(argv, *, cwd, env):
                (cwd / "node_modules").mkdir()
                (cwd / "node_modules/partial").write_bytes(b"incomplete install")
                return subprocess.CompletedProcess(argv, 37)

            with patch.object(wrapper, "ROOT", root), patch.object(wrapper.subprocess, "run", side_effect=fail) as run:
                self.assertEqual(wrapper.main(), 37)
            run.assert_called_once()
            self.assertEqual(run.call_args.args[0][:2], ["npm", "ci"])
            self.assertFalse(run.call_args.kwargs["cwd"].exists())
            self.assertEqual(snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
