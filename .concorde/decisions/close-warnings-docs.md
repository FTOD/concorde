# Decision log: close-warnings-docs

Goal: The user document and the concorde-development skill say that ending a task stops and removes its Claude Code task sessions from Claude's session list, keeping their transcripts in the task's trace, and that task close and task merge print warnings, a session warning naming a task session to remove by hand with claude rm

## Brief (main agent, 2026-09-29)

The developer asked to fix the user document after tasks `task-session-cleanup` (6eb07bd8) and
`close-warnings-guidance` (db0d23a4) merged. Behaviour now: ending a task (merge, `--completed`,
`--failed`) copies each Claude Code task session's transcript into its trace node
(`sessions/<id>/transcript.jsonl`) and removes the session from Claude's session list with
`claude rm`; a close without a merge first stops it with `claude stop`; `task close` prints
`{"record": …, "warnings": […]}` like `task merge`, and both warn about each session whose
transcript could not be kept or that could not be removed, naming the reason and `claude rm <id>`.
The main-session guidance (`prompts/main-session/skill.md`) already says this; mirror it, briefly:

- `docs/using-concorde.md`: where it describes task sessions and closing/merging a task, say that
  ended tasks' Claude Code task sessions leave Claude's session list on their own (transcripts kept
  in the task's history), and what the new `task close` output and session warnings mean.
- `prompts/development/skill.md` step 6 (concorde-development skill): its sentence that
  `task merge`'s warnings name a decision log nobody wrote in should also name the task-session
  warnings; rebuild so the rendered skill follows.

Wording and placement are yours. No Spec promise should change; if one must, say why in the log.

## Task session (2026-09-29)

- `docs/using-concorde.md`: "3. Merge and close" now says closing also ends the task's Claude Code
  task sessions (pointing to "Task sessions"), and a new paragraph after the close paragraph says
  that `task merge` and `task close` both print the record with `warnings` and what the decision
  log and task-session warnings mean (reason plus `claude rm <id>`; a session whose transcript
  could not be kept stays listed so nothing is lost). The Claude Code bullet of "Task sessions"
  says ending the task copies each transcript into the task's trace and removes the session with
  `claude rm`, stopping it first with `claude stop` on a close without a merge. Wording taken from
  `src/concorde/tasks/session.py` warnings and `prompts/main-session/skill.md`.
- `prompts/development/skill.md` step 6: closing stops and removes the task sessions keeping their
  transcripts; `warnings`, like `task close`'s, name the decision log and each task session not kept
  or not removed with the reason and `claude rm <id>`. Rebuilt; `build --check` and
  `spec-validation` succeed.
- No Spec promise changed (user document and development skill only, both already matching the
  Specs' behaviour).
- `task-validation` failed with `check_sandbox_unavailable` for `check.concorde.tests`: the worktree
  had no `.venv` because the session had not run `uv sync --locked --group dev` (development skill
  step 3). Ran it and validated again.
- `task-validation` `r-20260929T125417-task_validation-705c3f6f` ready (no blocking findings);
  `delivery` `r-20260929T125450-delivery-1c7e4998` committed `2a809059` on
  `concorde/close-warnings-docs` with `.concorde/evidence/close-warnings-docs/1.json`.

## Closed: merged, 2026-09-29T12:56:01Z
