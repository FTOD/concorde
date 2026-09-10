import unittest
from unittest.mock import patch

from concorde.harness.session_handoff import handoff_prompt, UNKNOWN


class SessionHandoffTests(unittest.TestCase):
    def test_default_is_honest_self_contained_and_has_no_filesystem_side_effects(self):
        with patch('pathlib.Path.resolve', side_effect=AssertionError('must not enter target')):
            prompt = handoff_prompt('/unknown/target')
        self.assertIn('```text\n', prompt)
        self.assertTrue(prompt.endswith('```'))
        self.assertIn('/unknown/target', prompt)
        self.assertIn(UNKNOWN, prompt)
        self.assertIn('AGENTS.md and CLAUDE.md', prompt)
        self.assertIn("Skills this worktree built for itself", prompt)
        self.assertIn("do not create or enter another worktree", prompt)
        self.assertIn('grants no additional reads, writes, merge, or delivery authority', prompt)
        with self.assertRaisesRegex(ValueError, 'absolute'):
            handoff_prompt('relative/path')

    def test_complete_context_preserves_task_constraints_artifact_paths_and_storage(self):
        prompt = handoff_prompt(
            '/work/project', branch='feat/session', change_id='change.session',
            task='完成会话交接。保留用户原文。', constraints=['仅此 worktree；不合并、不 push'],
            completed='Implementation is applied; patch is a backup.', remaining='Run regression tests.',
            checks='Unit tests passed; full regression not run.',
            artifacts=[{'path': '/tmp/recovery.patch', 'applied': True, 'temporary': True},
                       {'path': '/home/user/handoffs/progress.md', 'applied': False, 'temporary': False}],
            next_steps='Review the saved patch against the applied diff, then run regression tests.',
            completion='Commit the verified implementation to feat/session.')
        self.assertNotIn(UNKNOWN, prompt)
        for value in ('完成会话交接', '不合并', '/tmp/recovery.patch', '/home/user/handoffs/progress.md',
                      '"temporary": true', '"temporary": false', '"applied": true', 'change.session',
                      'full regression not run'):
            self.assertIn(value, prompt)

    def test_embedded_fences_cannot_end_the_copyable_block(self):
        prompt = handoff_prompt('/work/project', task='Preserve this example: ```text\nfoo\n```')
        self.assertIn('\n````text\n', prompt)
        self.assertTrue(prompt.endswith('````'))
