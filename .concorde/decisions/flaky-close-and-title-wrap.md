# Decision log: flaky-close-and-title-wrap

Goal: Find and fix the cause of the intermittent task close failure in test_a_report_is_recorded_before_the_message, and stop CHK.term.unlinked from warning on Module titles wrapped across lines

## Brief (main agent, 2026-10-02)

Two Issues recorded by task term-link-warnings. Read each with
`python3 scripts/concorde.py issues show <id>` first.

- I-c496879cc46153919fbd45a38c152858 (module.tasks, medium, decision-needed): check.tasks.tests
  failed once in task-validation r-20261002T031349-task_validation-f65cfd75 (in that task's
  trace, now under .concorde/history/term-link-warnings/), test_a_report_is_recorded_before_the_message,
  `task close` exiting 1; it passed alone three times. Decided by the main agent (a test defect,
  ordinary scope): find the cause from that run's saved check log and by reproducing under load or
  in the check boundary (repeat runs, parallel runs), then fix the cause, in the test or in Tasks'
  code if close really fails intermittently. No retries or serial marks that only hide it. If the
  cause turns out to be a real defect whose fix changes what Tasks promises, escalate.
- I-cf00a5fa111f59c9919cb54bff6084d1 (module.spec, low, obvious-fix): CHK.term.unlinked blanks
  Module titles line by line, so a title wrapped across lines yields a false warning. Fix the
  check, with a test.

Change only module.tasks and module.spec; escalate anything else. Verify with build --check,
spec-validation and the full suite, then task-validation and delivery, and report the cause found.

## Task session: CHK.term.unlinked over paragraphs (2026-10-02)

- I-cf00a5fa111f59c9919cb54bff6084d1 (obvious-fix): `term_uses` in `src/concorde/spec/syntax.py`
  now matches Module titles and term titles over each paragraph (a run of adjacent non-blank
  prose lines), so a Module title or longer term wrapped across a line break is one title and
  never a use of a shorter one. Test `test_titles_wrapped_across_lines_are_still_one_title`
  (scenario.spec.term-unlinked) fails on the old code. Committed.
- Decision (mine): a term use that itself wraps across lines stays unreported, as before.
  Reporting it is what the Protocol asks, but it yields 10 new warnings, all real uses, in Specs
  of Modules outside this task. Recorded as Issue I-74f24f06b9025c9e8571d48f5b7bf019
  (module.spec, preferred-fix, low) for a task covering those Modules.
- Observed while reading the close: `holder_pids` in `src/concorde/tracing/locks.py` compares
  inode numbers without the device, so `stop_task` could SIGTERM an unrelated process. Not this
  task's Modules; recorded as Issue I-bf5871eb5db656db9d125248ebafe458 (module.tracing,
  obvious-fix, medium).

## Task session: cause of the intermittent close failure (2026-10-02)

- The failing check ran 03:15:34.999–03:15:49.587 UTC. Claude Code's auto-update ran
  `npm install --global @anthropic-ai/claude-code@2.1.287` at 03:15:37.677–~03:15:40.08 UTC
  (~/.npm/_logs/2026-10-02T03_15_37_677Z-debug-0.log), and npm's reify moves `bin/claude` aside
  while it installs. The test's close (without a merge) runs `claude stop s1` against the real
  `claude` on PATH; with it missing, `stop_sessions` refuses with `session_stop_failed`, exit 1.
  Reproduced exactly by running the test with `claude` absent from PATH. The CLI is reinstalled
  every few minutes here (npm logs at 02:49, 02:57, 03:12, 03:15, 03:19, 03:22 UTC).
- Not reproduced otherwise: 400 parallel runs of the test, 20+ runs of the whole check in the
  check boundary and 400 parallel `claude stop s1` calls all passed / answered the same.
- Decision (mine): the close's refusal is the promised behaviour (a session it cannot confirm
  stopped refuses the close), so the defect is the test's: TaskStoreTests runs the developer's own
  `claude` and reads their ~/.claude. setUp now puts a fake `claude` that knows no session first
  on PATH and an empty CLAUDE_CONFIG_DIR, as test_session.py already does; the failing assertion
  now prints the close's refusal. No change of Tasks' code or promises.
- One sandbox repeat run (11:24–11:25 local) failed 5 test_merge tests (`-9 != 1`, a Traceback).
  It ran while `src/concorde/spec/syntax.py` held my first draft, an f-string invalid on the
  venv's Python 3.11, so every Concorde subprocess the merge tests start crashed on import:
  self-inflicted, no flake. The same merge test then passed 400 times in 16 parallel processes,
  and 24 later runs of the whole check in the boundary passed.
- Verified: with the fix, test_store passes with no `claude` on PATH; the full suite (952
  passed, 5 skipped) ran with a logging `claude` shim first on PATH, and no test called it.

## Report 1 to the main agent (spec-review quality criteria), 2026-10-02T03:45:08Z

Task flaky-close-and-title-wrap delivered: delivery commit b6a191256f6c on concorde/flaky-close-and-title-wrap (task-validation r-20261002T033208-task_validation-e9fa9efd ready, no blocking findings; delivery r-20261002T033830-delivery-66bb7eca). Resolves I-c496879cc46153919fbd45a38c152858 and I-cf00a5fa111f59c9919cb54bff6084d1 (added with task resolve).

Cause of the intermittent close failure (I-c496879c…): the test ran the developer's real `claude` CLI. A close without a merge runs `claude stop` on each recorded task session. Claude Code's auto-update ran `npm install --global @anthropic-ai/claude-code@2.1.287` from 03:15:37.7 to ~03:15:40.1 UTC (~/.npm/_logs/2026-10-02T03_15_37_677Z-debug-0.log). npm moves bin/claude aside while it installs, and the failing check ran from 03:15:35.0 to 03:15:49.6 UTC. With `claude` missing, stop_sessions refuses with session_stop_failed, so the close exits 1. Running the test with `claude` removed from PATH reproduces exactly this failure. On this machine the CLI is reinstalled every few minutes (02:49, 02:57, 03:12, 03:15, 03:19 and 03:22 UTC). The close's refusal is the promised behaviour, so Tasks' code and promises are unchanged.

Fix: TaskStoreTests.setUp now puts a fake `claude` that knows no session first on PATH, with an empty CLAUDE_CONFIG_DIR, as test_session.py already does. The close assertion now prints its refusal. The full suite (952 passed) ran with a logging shim in front of the real `claude`, and no test called it.

Term check (I-cf00a5fa…): term_uses now matches Module titles and term titles over each paragraph, so a wrapped "Spec\ncore" or "Task\ntype" counts as one title and is not a use of "Spec" or "Task". A new test fails on the old code.

Decisions I made: (1) A term use that wraps across lines itself is still not reported, as before. Reporting it is what the Protocol asks, but it adds 10 real warnings in Specs of Modules outside this task. I recorded this as Issue I-74f24f06b9025c9e8571d48f5b7bf019 (module.spec, preferred-fix, low), for a task that covers those Modules. (2) While reading the close I found that locks.holder_pids matches /proc/locks entries by inode alone, without the device, so stop_task could SIGTERM an unrelated process. Recorded as Issue I-bf5871eb5db656db9d125248ebafe458 (module.tracing, obvious-fix, medium). (3) One sandbox repeat run showed 5 test_merge failures. They happened while my draft of syntax.py held an f-string that is invalid on Python 3.11, so they were self-inflicted and not a flake; that test then passed 400 times in parallel.

Verified: build --check, spec-validation (success, 0 findings) and the full suite all pass. Nothing is left open in this task.

## Closed: merged, 2026-10-02T03:45:36Z

The merge answered report(s) 1 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit b6a191256f6c72c1c3474cc25e93ad63d3de76e1 into main and closed it as merged. Nobody answers a report after that.
