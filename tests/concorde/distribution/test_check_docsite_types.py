"""Preparation destinations and dependency reuse; real compiler isolation is an integration check."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class DocsiteTypeCheckTests(unittest.TestCase):
    @verifies('scenario.distribution.check-docsite-external')
    def test_preparation_and_dependency_installation_use_only_temporary_copy(self):
        spec = importlib.util.spec_from_file_location('check_docsite_types',
            REPOSITORY_ROOT / 'scripts/development/check-docsite-types.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for reuse in (False, True):
            with self.subTest(reuse=reuse), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                docsite = root / 'docsite'
                docsite.mkdir()
                for filename in ('package.json', 'package-lock.json', 'tsconfig.json'):
                    (docsite / filename).write_text('{}')
                (docsite / '.generated').mkdir()
                (docsite / '.generated/specs-sidebar.json').write_text('original')
                if reuse:
                    compiler = docsite / 'node_modules/typescript/bin/tsc'
                    compiler.parent.mkdir(parents=True)
                    compiler.write_text('compiler')
                    (docsite / 'node_modules/.concorde-typecheck-dependencies').write_text(
                        hashlib.sha256(b'{}\0{}').hexdigest())
                original = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                calls = []
                def run(argv, *, cwd, **kwargs):
                    cwd = Path(cwd)
                    self.assertFalse(cwd.is_relative_to(root))
                    calls.append((argv, cwd))
                    if argv[0] == 'npm':
                        (cwd / 'node_modules').mkdir()
                    elif '--import' in argv:
                        self.assertEqual(str(root), argv[-1])
                        (cwd / '.generated').mkdir()
                        (cwd / '.generated/specs-sidebar.json').write_text('temporary sidebar')
                    else:
                        self.assertIn('--noEmit', argv)
                        return subprocess.CompletedProcess(argv, 7)
                    return subprocess.CompletedProcess(argv, 0)
                with patch.object(module, 'ROOT', root), patch.object(module, 'DOCSITE', docsite), \
                     patch.object(module.subprocess, 'run', run):
                    self.assertEqual(7, module.main())
                self.assertEqual(not reuse, any(argv[0] == 'npm' for argv, _ in calls))
                self.assertTrue(all(not cwd.exists() for _, cwd in calls))
                self.assertEqual(original, {str(p.relative_to(root)): p.read_bytes()
                    for p in root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
