# Decision log: pi-drain-own-work

Goal: The pi main-session extension reports to pi-subagents as this session's background work only the runs and task-session rounds this session started, so a headless pi -p main session no longer waits (up to pi-subagents' 30-minute auto-drain) for runs other sessions started; the run view still shows every running run and round.

## Decisions taken without the developer

- **"Own" means started by this session's `concorde_run` or `concorde_task_session` tool.**
  Options: (a) tool-started only; (b) also runs this session started with bash, by having the
  extension put a session marker in the environment and the runner record it in the progress
  file. Chose (a): it needs no change in Execution or Task sessions (outside this task's Module),
  and the guidance already tells pi main agents to start runs and sessions with the tools. A run
  started with bash is still shown and woken for, but a `pi -p` session no longer drains it.
- **`bg_wait` without an id now waits only for the session's own runs and rounds**, since it and
  pi-subagents' auto-drain read the same provider. The Main session Spec said it "waits for the
  running ones"; reworded in module.md and the `concorde_run` tool description. The run view,
  the wake messages and `/concorde` still cover every run, as req.main-session.pi-run-follow
  requires.
- Kept the new wording off the glossary term "Headless session" (the e2e tool's sessions),
  writing "`pi -p` session" instead; spec-validation had flagged the unlinked term.

## Non-ok results

- Live A/B check in a scratch directory holding a fake running run of "another session" (a live
  `sleep` as its runner): main's extension kept `pi -p` from exiting until the 150 s timeout
  (exit 124); this branch's extension exited in 7 s, and 4 s on the final source.

## Closed: merged, 2026-09-28T18:11:24Z
