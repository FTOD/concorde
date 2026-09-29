# Decision log: close-warnings-guidance

Goal: The main-session guidance says that closing a task removes its Claude Code task sessions from Claude's session list, and that the main agent acts on every warning of task close and task merge, each naming a task session that could not be kept or removed and the command to remove it by hand

## Brief (main agent, 2026-09-29)

Follows task `task-session-cleanup` (merged at 6eb07bd8): ending a task now copies each Claude
Code task session's transcript into its trace node and removes the session with `claude rm`; a
close without a merge first stops it with `claude stop`; `task close` now prints
`{"record": …, "warnings": […]}` like `task merge`, and both carry a warning for each session it
could not keep or remove, naming the session, the reason and `claude rm <id>`.

The developer asked for the guidance sentence that task's session proposed. In the main-session
guidance (`prompts/main-session/skill.md` and whatever renders from it, module.main-session):

- in "Task sessions" (Claude Code part, where `claude agents` / `claude stop` are named), say that
  ending the task (merge or close) stops and removes its Claude Code task sessions from Claude's
  session list, keeping their transcripts in the task's trace, so the main agent does not remove
  them itself;
- in "Merge delivered work", say the main agent acts on every warning of `task close` and
  `task merge`; a session warning names a task session it could not keep or remove and the
  command to remove it by hand.

Keep the wording short and consistent with the Main session Spec; change the Spec only where its
promises about the guidance's content require it. Do not edit `docs/using-concorde.md`: the open
task `worker-config-followups` is changing that file; the main agent will handle the user document
after it merges.

## Task session (2026-09-29)

- Changed `prompts/main-session/skill.md` ("Task sessions", Claude Code part; "Merge delivered
  work", after the close paragraph) and the matching bullets of the Main session Spec
  (`specs/concorde/coordination/main-session/module.md`, "Hand every task to a task session" and
  "Merge delivered work"): the Spec lists what the guidance tells the main agent, so the two new
  instructions are promises about its content and belong there too.
- The warning sentence also names the other `task merge` warning (a decision log nobody wrote in),
  so "act on every warning" covers every warning the Tasks contract lists, not only session ones.
- Left `prompts/development/skill.md` (owned by module.concorde, outside this task) unchanged: its
  step 6 still says `task merge`'s warnings name a decision log nobody wrote in, without the
  session warnings. Open point for the main agent.
- `docs/using-concorde.md` untouched, as the brief says.
- Verified: build, build --check, spec-validation (0 findings), tests/concorde/main_session/
  test_guidance.py and tests/concorde/distribution/test_distribution.py (58 passed).
- task-validation ok (ready, no blocking findings); delivery ok, delivery commit 0be198f5, bundle
  `.concorde/evidence/close-warnings-guidance/1.json`.

## Closed: merged, 2026-09-29T12:49:32Z
