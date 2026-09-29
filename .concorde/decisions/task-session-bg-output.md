# Decision log: task-session-bg-output

Goal: concorde task session reports session_failed and records no session although claude --bg started it: Claude Code now colours the session id in its 'backgrounded · <id> · <name>' line with ANSI escapes, which the STARTED pattern in tasks/session.py does not match; recognise the line with the escapes removed, record the session, and test it with the exact current output

## 2026-09-29 — main agent

- Cause verified: `claude --bg` (Claude Code 2.1.283) prints `backgrounded · ESC[36m<id>ESC[39m ·
  <name>` plus dimmed help lines, so `STARTED` never matched; `task session` raised
  `session_failed` although the session ran, and recorded no session (seen for five sessions on
  2026-09-29).
- Decision: remove terminal escape sequences (CSI) from the output before matching and from the
  output quoted in a `session_failed` detail, rather than widening the pattern around the escapes;
  no Spec change, since the promise (record a started session, refuse one that did not start) is
  unchanged. Test added with the exact current output.
- Verification: spec-validation 0/0, build --check clean, pytest 641 passed / 1 known pre-existing
  failure (test_grading_runs_the_case_tests_on_a_throwaway_tree).
- The five sessions started before this fix are not in their task records; left as they are.

## Closed: merged, 2026-09-28T16:30:30Z
