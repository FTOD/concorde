"""Development integrates the real Harness sandbox without granting log writes to checks."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from concorde.development.capability_host import _check, _check_revision
from concorde.development.capability_service import CapabilityHost, run_capability
from concorde.harness.check_executor import CheckSandboxError, execute_check
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import project, PACKAGE, CONFIGURATION


class CheckIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.registry = project(self.root)

    def configure(self, code, timeout=10):
        check = self.registry['checks'][0]
        check.update(argv=['{python}', '-c', code], timeout_seconds=timeout)
        (self.root / '.concorde/specs.json').write_text(json.dumps(self.registry))
        repo = SpecRepository(self.root, PACKAGE)
        return repo, repo.select('service.transfer'), check['id']

    @verifies('scenario.development.validate-check-isolation')
    def test_check_cannot_forge_logs_but_host_persists_private_output_and_digest(self):
        repo, target, check_id = self.configure("""
from pathlib import Path
import sys
assert Path('app/transfer.py').is_file()
try: Path('.concorde/runs/forged').mkdir(parents=True)
except OSError: pass
else: raise AssertionError('project was writable')
print('PRIVATE_CHECK_OUTPUT')
print('PRIVATE_CHECK_ERROR',file=sys.stderr)
sys.exit(17)
""")
        before = _check_revision(repo, target)
        result = _check(repo, target, 'test-private')
        log = self.root / f'.concorde/runs/test-private/{check_id}.log'
        self.assertEqual(b'PRIVATE_CHECK_OUTPUT\n\nPRIVATE_CHECK_ERROR\n', log.read_bytes())
        self.assertFalse((self.root / '.concorde/runs/forged').exists())
        self.assertEqual('failed', result[0]['status'])
        self.assertEqual(17, result[0]['exit_code'])
        self.assertEqual(before, result[0]['source_digest'])
        self.assertEqual(digest(log.read_bytes()), result[0]['log_digest'])
        self.assertNotIn('PRIVATE_CHECK', json.dumps(result))

    @verifies('scenario.development.validate-check-isolation')
    def test_real_project_write_fails_validation_and_never_records_ready(self):
        self.configure("open('unlisted-new.txt','w').write('unsafe')")
        result = run_capability('concorde-validate', CONFIGURATION,
            typed('concorde-validate-request', {'target_id': 'service.transfer', 'task': 'Check candidate'}),
            host_context=CapabilityHost(self.root, PACKAGE, allow_primary_worktree=True))
        self.assertNotEqual('succeeded', result['status'], result)
        self.assertFalse((self.root / 'unlisted-new.txt').exists())
        self.assertIn('failed', json.dumps(result))
        state = self.root / '.concorde/worktree.json'
        if state.exists():
            self.assertNotEqual('ready', json.loads(state.read_text())['status'])

    @verifies('scenario.development.validate-check-isolation')
    def test_unavailable_sandbox_blocks_without_leaking_private_diagnostics(self):
        repo, target, check_id = self.configure("open('unlisted-new.txt','w').write('unsafe')")
        with patch('concorde.harness.check_executor._bubblewrap',
                   side_effect=CheckSandboxError('PRIVATE_STARTUP_ERROR')):
            with self.assertRaises(SpecError) as caught:
                _check(repo, target, 'unavailable')
        self.assertEqual('check_sandbox_unavailable', caught.exception.code)
        self.assertNotIn('PRIVATE_STARTUP_ERROR', str(caught.exception))
        self.assertIn(b'PRIVATE_STARTUP_ERROR',
            (self.root / f'.concorde/runs/unavailable/{check_id}.log').read_bytes())
        self.assertFalse((self.root / 'unlisted-new.txt').exists())

    @verifies('scenario.development.validate-check-isolation')
    def test_timeout_retains_output_and_status(self):
        repo, target, check_id = self.configure("import time; print('partial',flush=True); time.sleep(60)", 1)
        result = _check(repo, target, 'timeout')[0]
        self.assertEqual(('timeout', -1), (result['status'], result['exit_code']))
        self.assertIn(b'partial', (self.root / f'.concorde/runs/timeout/{check_id}.log').read_bytes())

    @verifies('scenario.development.validate-blocked')
    def test_external_host_change_still_invalidates_post_check_digest(self):
        repo, target, _ = self.configure("print('read-only check')")
        def concurrent_host_change(*args, **kwargs):
            result = execute_check(*args, **kwargs)
            # Simulates a separate authorized host writer, outside the check's sandbox.
            with (self.root / 'app/transfer.py').open('a') as stream:
                stream.write('\n# changed externally\n')
            return result
        with patch('concorde.development.capability_host.execute_check', concurrent_host_change):
            with self.assertRaises(SpecError) as caught:
                _check(repo, target, 'stale')
        self.assertEqual('stale_evidence', caught.exception.code)


if __name__ == '__main__':
    unittest.main()
