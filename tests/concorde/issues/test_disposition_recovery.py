"""Fault injection around the closing write: retries must not confuse it with completion."""
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from concorde.harness import change_worktree
from concorde.issues import flow, store
from concorde.spec.repository import digest
from concorde.spec.verification import verifies
# Import the module, not its TestCase class, so unittest does not collect the fixture tests twice.
from tests.concorde.issues import test_flow as fixtures


class DispositionRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.IssueFlowTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.healthy_implementation()
        self.root, self.identifier = self.fixture.root, self.fixture.ref['issue_id']
        self.path = self.root / store.issue_path(self.identifier)
        self.before = self.path.read_bytes()

    @staticmethod
    def disposition(stage, snapshot, data, cwd):
        if stage == 'issue-solve':
            data['issue_decision'].update(action='not-actionable', rationale='Controlled recovery fixture disposition.')

    def solve(self, **kwargs):
        return self.fixture.call('solve', self.disposition, **kwargs)

    def state(self):
        return change_worktree.read_change(self.root, required=True)

    def solution(self):
        return self.state()['issue_solutions'][self.identifier]

    def fail_checkpoint(self, status):
        original = change_worktree.save_change
        def save(root, state, **kwargs):
            value = state.get('issue_solutions', {}).get(self.identifier, {})
            if value.get('status') == status:
                raise OSError('injected checkpoint failure: ' + status)
            return original(root, state, **kwargs)
        return patch.object(change_worktree, 'save_change', side_effect=save)

    def assert_recovered(self, result):
        self.assertEqual('succeeded', result['status'], result)
        self.assertEqual('ready', result['output']['data']['outcome'])
        self.assertEqual('closed', store.read_issue(self.root, self.identifier)[0]['status'])
        self.assertEqual('completed', self.solution()['status'])
        self.assertNotIn('pending_disposition', self.solution())
        self.assertTrue(self.fixture.model.calls, 'an interrupted close must not use already-closed')
        self.assertFalse((self.root / '.concorde/deliveries').exists())

    @verifies('scenario.issues.disposition-recovery')
    def test_journal_persistence_failure_cannot_publish_a_close(self):
        with self.fail_checkpoint('closing'), patch.object(flow, 'dispose_issue', wraps=store.dispose_issue) as close:
            result = self.solve()
        self.assertEqual('failed', result['status'], result)
        close.assert_not_called()
        self.assertEqual(self.before, self.path.read_bytes())
        self.assertNotIn('pending_disposition', self.solution())
        self.assert_recovered(self.solve())

    @verifies('scenario.issues.disposition-recovery')
    def test_oversized_disposition_is_rejected_before_journaling(self):
        limit = len(self.before) + 10
        with patch.object(flow, 'MAX_RECORD_BYTES', limit), patch.object(store, 'MAX_RECORD_BYTES', limit):
            result = self.solve()
        self.assertEqual('blocked', result['status'], result)
        self.assertEqual('invalid_issue', result['errors'][0]['code'])
        self.assertEqual(self.before, self.path.read_bytes())
        self.assertNotIn('pending_disposition', self.solution())

    @verifies('scenario.issues.disposition-recovery')
    def test_interruption_before_publication_has_a_durable_exact_journal(self):
        def interrupt(*args, **kwargs):
            journal = self.solution()['pending_disposition']
            self.assertEqual(self.before, journal['before'].encode())
            self.assertEqual(digest(self.before), journal['before_digest'])
            prepared = store.parse(journal['after'], self.identifier)
            self.assertEqual('closed', prepared['status'])
            self.assertEqual(prepared['dispositions'][-1]['created_at'], kwargs['created_at'])
            self.assertEqual(digest(journal['after'].encode()), journal['after_digest'])
            raise KeyboardInterrupt('injected process interruption before publication')
        with patch.object(flow, 'dispose_issue', side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            self.solve()
        self.assertEqual(self.before, self.path.read_bytes())
        self.assertIn('pending_disposition', self.solution())
        self.assert_recovered(self.solve())

    @verifies('scenario.issues.disposition-recovery')
    def test_closed_write_followed_by_checkpoint_failure_is_not_already_closed(self):
        with self.fail_checkpoint('verifying-candidate'):
            result = self.solve()
        self.assertEqual('failed', result['status'], result)
        journal = self.solution()['pending_disposition']
        self.assertEqual(journal['after'].encode(), self.path.read_bytes())
        self.assertEqual('failed', self.state()['status'])
        # Retrying the original frozen request is allowed only for the two journaled versions.
        self.assert_recovered(self.solve(expected_revision=digest(self.before)))
        self.assertEqual(1, len(store.read_issue(self.root, self.identifier)[0]['dispositions']))

    @verifies('scenario.issues.disposition-recovery')
    def test_store_write_with_lost_acknowledgement_is_recoverable(self):
        publish = store._publish
        def lost_ack(root, record, revision):
            publish(root, record, revision)
            if record['status'] == 'closed':
                raise OSError('injected loss after Issue rename')
        with patch.object(store, '_publish', side_effect=lost_ack):
            result = self.solve()
        self.assertEqual('failed', result['status'], result)
        self.assertEqual('closed', store.read_issue(self.root, self.identifier)[0]['status'])
        self.assertEqual('closing', self.solution()['status'])
        self.assert_recovered(self.solve())

    @verifies('scenario.issues.disposition-recovery')
    def test_lost_completion_checkpoint_invalidates_ready_before_restoration(self):
        # Use real Git tree identities so an old ready receipt cannot accidentally survive rollback.
        for arguments in (('init', '-q'), ('add', '.'), ('-c', 'user.name=Fixture', '-c',
                          'user.email=fixture@example.invalid', 'commit', '-qm', 'Recovery fixture')):
            subprocess.run(('git', '-C', str(self.root), *arguments), check=True, capture_output=True)
        with self.fail_checkpoint('completed'):
            result = self.solve()
        self.assertEqual('failed', result['status'], result)
        self.assertIsNotNone(self.state()['validated_tree'])
        self.assertIn('pending_disposition', self.solution())
        restore = flow.restore_issue
        def check_before_restore(*args, **kwargs):
            self.assertIsNone(self.state()['validated_tree'])
            self.assertNotEqual('ready', self.state()['status'])
            return restore(*args, **kwargs)
        with patch.object(flow, 'restore_issue', side_effect=check_before_restore) as restored:
            result = self.solve()
        restored.assert_called_once()
        self.assert_recovered(result)

    @verifies('scenario.issues.disposition-recovery')
    def test_retry_after_rollback_write_but_before_ack_is_idempotent(self):
        with self.fail_checkpoint('verifying-candidate'):
            self.solve()
        write = store._publish_text
        def lose_restore_ack(root, identifier, text, revision):
            write(root, identifier, text, revision)
            if text.encode() == self.before:
                raise OSError('injected loss after restoring original bytes')
        with patch.object(store, '_publish_text', side_effect=lose_restore_ack):
            result = self.solve()
        self.assertEqual('failed', result['status'], result)
        self.assertEqual(self.before, self.path.read_bytes())
        self.assertIn('pending_disposition', self.solution())
        def no_duplicate_restore(root, identifier, text, revision):
            self.assertNotEqual(self.before, text.encode(), 'the completed restore should not write again')
            return write(root, identifier, text, revision)
        with patch.object(store, '_publish_text', side_effect=no_duplicate_restore):
            result = self.solve()
        self.assert_recovered(result)

    @verifies('scenario.issues.disposition-recovery-stale')
    def test_concurrent_reopen_is_preserved_without_a_worker_or_rollback(self):
        with self.fail_checkpoint('verifying-candidate'):
            self.solve()
        _, revision = store.read_issue(self.root, self.identifier)
        store.dispose_issue(self.root, self.identifier, revision, reason='reopened',
                            note='Independent developer decision', evidence=['developer'], actor='developer')
        changed = self.path.read_bytes()
        result = self.solve()
        self.assertEqual('blocked', result['status'], result)
        self.assertEqual('stale_issue', result['errors'][0]['code'])
        self.assertEqual(changed, self.path.read_bytes())
        self.assertEqual([], self.fixture.model.calls)
        self.assertIn('pending_disposition', self.solution())

    @verifies('scenario.issues.disposition-recovery-stale')
    def test_edit_between_admission_and_restore_is_not_overwritten(self):
        with self.fail_checkpoint('verifying-candidate'):
            self.solve()
        restore = flow.restore_issue
        edited = []
        def concurrent_edit(root, identifier, original, revision):
            store.dispose_issue(root, identifier, revision, reason='reopened', note='Concurrent edit',
                                evidence=['developer'], actor='developer')
            edited.append(self.path.read_bytes())
            return restore(root, identifier, original, revision)
        with patch.object(flow, 'restore_issue', side_effect=concurrent_edit):
            result = self.solve()
        self.assertEqual('blocked', result['status'], result)
        self.assertEqual('stale_issue', result['errors'][0]['code'])
        self.assertEqual(edited[0], self.path.read_bytes())
        self.assertEqual([], self.fixture.model.calls)

    @verifies('scenario.issues.disposition-recovery')
    def test_recovery_preserves_noncanonical_original_bytes_and_attempt_budget(self):
        self.before = self.before.replace(b'"schema_version": 1', b'"schema_version" : 1')
        self.path.write_bytes(self.before)
        with self.fail_checkpoint('verifying-candidate'):
            self.solve()
        attempts = self.solution()['attempts']
        restore = flow.restore_issue
        def check_exact_restore(*args, **kwargs):
            restore(*args, **kwargs)
            self.assertEqual(self.before, self.path.read_bytes())
        with patch.object(flow, 'restore_issue', side_effect=check_exact_restore):
            result = self.solve()
        self.assert_recovered(result)
        self.assertEqual(attempts + 1, self.solution()['attempts'])

    @verifies('scenario.issues.disposition-recovery-stale')
    def test_recovery_never_creates_a_new_candidate_to_escape_owning_authority(self):
        from concorde.development import capability_host
        from concorde.spec.typed_data import typed
        from tests.concorde.spec.support import CONFIGURATION, PACKAGE
        with self.fail_checkpoint('verifying-candidate'):
            self.solve()
        current = self.path.read_bytes()
        host = capability_host.CapabilityHost(self.root, PACKAGE)
        with patch.object(capability_host, 'create_worktree') as create:
            result = capability_host.run_capability('concorde-issues', CONFIGURATION,
                typed('concorde-issues-request', {'action': 'solve', 'issue_id': self.identifier}), host_context=host)
        create.assert_not_called()
        self.assertEqual('blocked', result['status'], result)
        self.assertEqual('workspace_mismatch', result['errors'][0]['code'])
        self.assertIn('pending Issue disposition', result['errors'][0]['message'])
        self.assertEqual(current, self.path.read_bytes())

    @verifies('scenario.issues.disposition-recovery-stale')
    def test_corrupted_journal_cannot_authorize_restoration(self):
        with self.fail_checkpoint('verifying-candidate'):
            self.solve()
        state = self.state()
        state['issue_solutions'][self.identifier]['pending_disposition']['before'] += '\n'
        change_worktree.save_change(self.root, state)
        current = self.path.read_bytes()
        result = self.solve()
        self.assertEqual('blocked', result['status'], result)
        self.assertEqual('invalid_worktree_state', result['errors'][0]['code'])
        self.assertEqual(current, self.path.read_bytes())
        self.assertEqual([], self.fixture.model.calls)

    @verifies('scenario.issues.disposition-recovery-stale')
    def test_legacy_unfinished_close_without_journal_fails_closed(self):
        with self.fail_checkpoint('verifying-candidate'):
            self.solve()
        state = self.state()
        state['issue_solutions'][self.identifier].pop('pending_disposition')
        change_worktree.save_change(self.root, state)
        current = self.path.read_bytes()
        result = self.solve()
        self.assertEqual('blocked', result['status'], result)
        self.assertEqual('invalid_worktree_state', result['errors'][0]['code'])
        self.assertEqual(current, self.path.read_bytes())
        self.assertEqual([], self.fixture.model.calls)
