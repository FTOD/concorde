# Decision log: panel-larger-decisions

Goal: Carry out the developer's 2026-09-29 decisions on the panel review's open items: name the runner's rows and cite them by name (Execution F19), document --stop's no_session refusal (Task session), and widen req.scaffold.no-overwrite to name the existing file or the child's folder, which refuses even when it holds no file (Scaffold)

## 2026-09-29 — The developer's decisions (options as presented by the main agent)

- Execution F19: option A. The runner's seven rows are named parse, binding check, lock,
  admission, execution, composition and finish; the table keeps the numbers only as order, and the
  prose cites the rows by name ("stage" and "runner step" were rejected; "phase" is the run
  progress file's field).
- Task session `--stop`: option A. Document the code's behaviour: `--stop` on a task with no pi
  session is refused with `no_session`, like `--answer` and `--wait` (contract, state diagram,
  a scenario with a test).
- Scaffold: option A. Widen req.scaffold.no-overwrite to name the existing file or the folder of
  the child that would hold it, and state that an existing child folder is refused even when it
  holds no file the scaffold would create (the recheck's current behaviour).
- E2E F14: option A. Keep `prepare` leaving the partial project directory after a failed step, as
  e2e/module.md now states; no change.
- Distribution F3's interpreter probe: no decision needed. installer-uv-python removed the user
  interpreter checks and checks uv and npm before the first write; the remaining probe tests the
  environment uv has just created, which cannot exist before the write.

## 2026-09-29 — Main agent's own choices while carrying out the decisions

- Runner (f8fb3308): the table's column is "Name", not a new count noun; a sentence above it says
  the prose cites each row by name and the number gives only the order. "Each step returns …"
  now says "Each of the definition's steps", so the only steps left in runner.md are the
  definition's. No other Spec, code or test cited the row numbers (checked by search).
- Task session (643b86bf): widened scenario.task-session.pi-no-session to `--answer` or `--stop`
  (same outcome) instead of adding a scenario; its test checks both and that the record is
  unchanged.
- Scaffold (5918fb93): one requirement statement (the Protocol allows exactly one SHALL) covering
  the file and the existing child folder; target-exists names the folder again; new scenario
  scaffold.target-folder-exists with a test for an empty existing folder; the step-2 row and the
  error table say that an existing child folder is a mismatch.

## 2026-09-29 — Independent review of delivery 1

- Independent review MERGE-WITH-NOTES: all three decisions carried out correctly, nothing narrowed.
  Applied its notes in f873c647 (mine): the parse and finish rows name the run lock the activity
  view already shows; "refused in the lock row, where an unbound run creates its checkout" (an
  unbound run takes no workspace lock); the scaffold requirement's reason says it creates files
  only in folders it creates (it still updates the parent entry and the registry); the
  empty-folder test compares the worktree status before and after.

## Closed: merged, 2026-09-29T04:09:59Z
