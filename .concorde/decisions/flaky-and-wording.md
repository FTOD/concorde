# Decision log: flaky-and-wording

Goal: Make the intermittent tests and the Views check's npm install deterministic, and align Dogfood scenarios' wording with the narrowed Issue-system exception

## Task brief (main agent, 2026-10-13)

Resolves the four Issues open after round 3 (read each with `concorde issues show`):
- I-4bb624fc (decision-needed, main-session): register_wait test intermittently sees the wait
  outlive its killed server; cause not established. Decided by the main agent: find the race
  (reproduce under load, e.g. the full suite with -n and repetition) and fix the test or the code,
  whichever is wrong; if the code is wrong, report it; if you cannot establish the cause after a
  bounded effort, report what you tried instead of guessing.
- I-566e82f1 (decision-needed, e2e): owners busy-workspace test flaky under load; same approach. The
  earlier fix waited for the runner; check whether a second race remains.
- I-ade0efbf (preferred-fix, views): check.views.publication-types' npm ci in a scratch copy
  sometimes skips @esbuild/linux-x64; make the install deterministic (your choice; report it).
- I-2d958da3 (obvious-fix, dogfood-scenarios): align the wording with the developer's narrowed rule
  (only failures of the Issue system go as bare error chains).
A project_review run reads the primary branch meanwhile; it does not touch your worktree. Deliver
with task-validation then delivery; run the full suite at least twice on the final input to show
the flakes are gone.

## Task session (2026-10-13)

- **I-4bb624fc (register_wait test) — cause established; the test was wrong, not the code.**
  Reproduced 3 times in 480 runs of the test (48 at once). With a diagnostic in the failure
  message, the failing case showed the wait process already a zombie (`Z`, PPid 1) at the first
  look: the server's death had killed it through PR_SET_PDEATHSIG as designed. The test's
  `alive()` counted only `Z` as ended, and its final assertion read `/proc/<pid>/stat` again;
  that second read caught the process in state `X` (EXIT_DEAD) while init reaped it, and `X`
  counted as alive. Fix in `tests/concorde/project_mcp/test_server.py`: `alive()` treats `Z` and
  `X` (and an unreadable stat) as ended, and the assertion judges the loop's last observation.
  After the fix: 384 of 384 loaded runs passed. No code change in the server.
- **I-566e82f1 (owners busy-workspace test) — a second race remained, in `scripts/e2e/owners.py`.**
  Reproduced 8 times in 288 loaded runs, every time at the test's evidence assertion: the
  refusal named `.concorde/unbound/<run>/result.json` instead of the lobby result. After reading
  the result, the case looked the run's folder up again for the error's evidence; the runner
  rewrites its progress file as it ends, and `run_folder` matched folders only through that file,
  so it fell back to `unbound/`. Fix: `run_folder` matches a folder by its name (the run id) first,
  and through the progress file only for a workflow step's `run` folder. The test now makes every
  progress file read as being rewritten once the result was found, so it exercises the race every
  time (it fails without the fix).
- **I-ade0efbf (Views check's npm install) — fix chosen: use an install only once it is complete
  for this platform, retrying npm ci at most three times.** The old reuse of the checkout's
  `docsite/node_modules` depended on a marker file nothing wrote, so every run did a fresh `npm ci`
  whose optional-package download can fail silently. Now the script compares the install with
  `package-lock.json` (every non-optional package admitted on this platform, plus every optional
  package declaring `os`/`cpu`/`libc` that admits this platform; an optional package for every
  platform is skipped, since npm leaves it out when its dependent is left out). It reuses the
  checkout's install when complete, else runs `npm ci` in the copy up to three times and fails
  naming the missing packages. Alternatives not taken: retry blindly (not verified), or require
  the checkout's install (unbound runs have none).
  **Beyond the task's Modules:** `scripts/development/check-docsite-types.py`, its test
  `tests/concorde/development/test_check_docsite_types.py` and its scenarios in
  `specs/concorde/development.md` belong to module.concorde (realization
  development-environment), not module.views; the Views check only calls the script. I made the
  change since no fix is possible inside module.views, and I escalate it for approval rather than
  deliver it unasked. New scenario: `scenario.concorde.check-docsite-complete-install`.
- **I-2d958da3 (Dogfood scenarios wording)** — fixed as the Issue suggests: a fault in the Issue
  store, `concorde issues` or the Issue tools is a failure of the Issue system, which Dogfooding
  sends as a bare error chain.
- Recorded two Issues for the same `/proc` race found elsewhere, outside this task's Modules:
  I-069a8e8fdc835010935348fbd931ba84 (module.execution: `pid_alive` and the runner test) and
  I-4898cef0565a5252993a2723c10e7867 (module.workers: the worker timeout test).

## Escalated to the main agent, 2026-10-13T15:56:47Z

- **task-session** task session (task flaky-and-wording): `change_outside_task_modules`
  The fix of I-ade0efbf (Views check's npm install) can only be made in scripts/development/check-docsite-types.py, which check.views.publication-types calls. That script, its test tests/concorde/development/test_check_docsite_types.py and its scenarios in specs/concorde/development.md belong to module.concorde (realization development-environment), not to any of the task's Modules (main-session, e2e, views, dogfood-scenarios). I made the change as commit 8e410f67e on the task branch: the script uses an npm install only when it holds every package the lockfile asks for on this platform. It reuses the checkout's docsite/node_modules when complete; otherwise it runs npm ci in the copy at most three times. It fails naming the missing packages. It adds scenario.concorde.check-docsite-complete-install. Verified: unit tests, the real check with reuse (exit 0, 5 s) and with a fresh install (exit 0), build --check and spec-validation. The other three Issues are fixed within the task's Modules.
  Not handled here (decision): The task session may not change a Module outside its task's Modules without the main agent's approval; the root Module's development environment is outside them.
  Options: Approve: deliver with commit 8e410f67e (module.concorde's development script, its test and one new scenario); Reject: revert 8e410f67e, deliver the other three fixes, and leave I-ade0efbf open for a task on module.concorde
  Recommendation: Approve: the Views check cannot be made deterministic inside module.views, and the change is self-contained and revertible

```json
{
  "level": "task-session",
  "actor": "task session (task flaky-and-wording)",
  "code": "change_outside_task_modules",
  "detail": "The fix of I-ade0efbf (Views check's npm install) can only be made in scripts/development/check-docsite-types.py, which check.views.publication-types calls. That script, its test tests/concorde/development/test_check_docsite_types.py and its scenarios in specs/concorde/development.md belong to module.concorde (realization development-environment), not to any of the task's Modules (main-session, e2e, views, dogfood-scenarios). I made the change as commit 8e410f67e on the task branch: the script uses an npm install only when it holds every package the lockfile asks for on this platform. It reuses the checkout's docsite/node_modules when complete; otherwise it runs npm ci in the copy at most three times. It fails naming the missing packages. It adds scenario.concorde.check-docsite-complete-install. Verified: unit tests, the real check with reuse (exit 0, 5 s) and with a fresh install (exit 0), build --check and spec-validation. The other three Issues are fixed within the task's Modules.",
  "evidence": [],
  "attempts": [],
  "unhandled": {
    "reason": "decision",
    "explanation": "The task session may not change a Module outside its task's Modules without the main agent's approval; the root Module's development environment is outside them."
  },
  "options": [
    "Approve: deliver with commit 8e410f67e (module.concorde's development script, its test and one new scenario)",
    "Reject: revert 8e410f67e, deliver the other three fixes, and leave I-ade0efbf open for a task on module.concorde"
  ],
  "recommendation": "Approve: the Views check cannot be made deterministic inside module.views, and the change is self-contained and revertible",
  "causes": []
}
```
- After the owners fix: the whole `OwnersCaseTests` class passed 192 of 192 runs, 48 at once.

## Report 1 to the main agent (Review流程), 2026-10-13T15:57:01Z

Report 1 (flaky-and-wording): all four Issues are fixed on the task branch (commits ed5780206, c5603ace9, 01d0de066, 8e410f67e). One decision is needed before delivery: escalation 1.

- I-4bb624fc (register_wait): cause established. The test was wrong; the server code is right. On a failure, the wait was already a zombie (PPid 1), killed by PR_SET_PDEATHSIG as designed. The test's second /proc read caught it in state X (being reaped by init), and the test counted X as alive. Fixed the test: alive() treats Z/X as ended, and the assertion uses the loop's last observation. Reproduced 3/480 before the fix; 0/384 after.
- I-566e82f1 (owners): a second race remained in scripts/e2e/owners.py. The refusal's evidence re-resolved the run folder while the runner rewrote its progress file, so it named unbound/<run>. Reproduced 8/288. run_folder now matches a folder by its name first. The test now forces the race every time and fails without the fix. After the fix: 192/192 runs of the whole class.
- I-ade0efbf (Views npm install): chose to use an install only once it is complete for this platform (verified against package-lock.json). The checkout's install is reused when complete; otherwise npm ci runs in the copy, at most three times. ESCALATION 1: this fix lives in module.concorde's scripts/development/check-docsite-types.py, its test and one new scenario in specs/concorde/development.md, outside the task's Modules. I recommend approving; rejecting means reverting 8e410f67e.
- I-2d958da3: wording fixed as the Issue suggested.
- New Issues for the same /proc race elsewhere: I-069a8e8f (module.execution pid_alive + runner test) and I-4898cef0 (module.workers timeout test).
I am running the full suite twice now; delivery (task-validation, then delivery) follows your answer.

Escalation 1 rendered:

It carries escalation(s) 1.

## Answer to report(s) 1 of the task session, 2026-10-13T15:57:23Z

Escalation 1 change_outside_task_modules (main agent): Approve — deliver with commit 8e410f67e; the fix of I-ade0efbf can only live in module.concorde's development script, no other task touches it, and it is self-contained. The two new /proc-race Issues (I-069a8e8f, I-4898cef0) are fine to leave for a follow-up.
- Full suite on the final input (head 8e410f67e), twice: 1582 passed, 6 skipped each time.

## Report 2 to the main agent (Review流程), 2026-10-13T16:18:22Z

Report 2 (flaky-and-wording): delivered as 546e04c4b (run r-20261013T160857-delivery-c963edbe), as approved in the answer to report 1. task-validation: ready. Full suite on the final input, twice: 1582 passed, 6 skipped each time. The task resolves I-2d958da3, I-4bb624fc, I-566e82f1 and I-ade0efbf; the merge closes them. Decisions made on the main agent's behalf are in the decision log. In brief: the register_wait flake was a test bug (it counted state X as alive), so the server code is unchanged. The owners flake was a second race in the refusal's evidence path, fixed in owners.py's run_folder. The Views check uses an npm install only once it is complete for this platform, with at most three npm ci attempts. Still open, left for a follow-up as you said: I-069a8e8f (module.execution) and I-4898cef0 (module.workers), the same /proc race in other places.

## Closed: merged, 2026-10-13T16:18:31Z

The merge answered report(s) 2 of the task session, unanswered until then: The task ended before the main agent answered: `concorde task merge` merged its delivery commit 546e04c4bad0b4bab5ed1bea5b36023048046036 into main and closed it as merged. Nobody answers a report after that.
