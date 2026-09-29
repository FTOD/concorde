# Decision log: todo-to-issue

Goal: Record the still-valid note .concorde/todos/pytest-plugin-subtest-counting.md as an Issue owned by module.concorde and remove the .concorde/todos folder

## Brief (main agent, 2026-09-29)

The developer asked: check whether the leftover note `.concorde/todos/pytest-plugin-subtest-counting.md`
is still valid; if it is, move it into Issues, otherwise delete it; and check code and Specs for
residue of the retired todo system.

The main agent already checked, at 7c997504:
- The problem is still valid. `tests/concorde/support/pytest_timing.py` still counts a unit per
  collected test (a failed subtest makes the unit fail, subtest reports carry no verdict of their
  own), while neither its docstring nor the JSON summary states that this differs from pytest's
  terminal line; there is no `counting` field and `tests/concorde/development/test_pytest_timing.py`
  has no subtest-failing case.
- The note's references are stale: `tests/concorde/distribution/test_outer_agents.py` no longer
  exists; the current test is `tests/concorde/development/test_pytest_timing.py`
  (`test_runner_fingerprints_and_default_cli`) and the scenario is `scenario.concorde.test-timing`
  (`specs/concorde/development.md`). The file is listed by `module.concorde`.
- No residue of the todo system was found in `src/`, `scripts/`, `prompts/`, `specs/`, `docs/`
  (the `{"type": "todo"}` in `tests/concorde/issues/test_store.py` is a deliberately invalid value
  and stays).

To do:
1. Record one Issue with `python3 scripts/concorde.py issues report --file <report.json> --task todo-to-issue`,
   owner `module.concorde`, carrying the note's observation, agreed behavior and non-goals with the
   current references (not the stale ones). Do not fix the plugin in this task.
2. Remove `.concorde/todos/` entirely (git rm).
3. Re-check for any residue (including `.gitignore`, `AGENTS.md`, `generated/` after build) and
   remove any you find that refers to the retired todo system.
4. `task-validation`, `delivery`, and report to the main agent.

## Task session (2026-09-29)

- Recorded Issue `I-207f3d582e635d60a1a5409d91b4fbfb` (report `sha256:9bba171c…`), owner
  `module.concorde`, type `limitation` (subtype null): the behaviour is consistent but undocumented,
  not a defect. Its description carries the note's observation, agreed behaviour and non-goals with
  current references (`tests/concorde/development/test_pytest_timing.py`,
  `scenario.concorde.test-timing`); the stale tester run path under `/tmp` and the related note
  `slow-test-semantic-audit.md` (no longer present) were left out, since evidence paths must exist.
- Removed `.concorde/todos/` with `git rm`. Re-checked tracked files, `generated/` after build,
  `.gitignore`, `AGENTS.md` and `CLAUDE.md`: no other residue of the todo system; the
  `{"type": "todo"}` in `tests/concorde/issues/test_store.py` stays as brief said.
- Committed as 97f0e47f.
- `task-validation` run `r-20260929T123306-task_validation-77dc0c90` ended `failed`
  (`check_sandbox_unavailable`): the check log says `bwrap: execvp .venv/bin/python: No such file
  or directory`. Cause: the session had not run `uv sync --locked --group dev` in the worktree.
  Ran it and validated again.
- `task-validation` `r-20260929T123341-task_validation-dd5ba5f4` ready (check.concorde.tests passed);
  `delivery` `r-20260929T123415-delivery-9c48e9c3` committed `708cc112` on `concorde/todo-to-issue`.

## Closed: merged, 2026-09-29T12:35:14Z
