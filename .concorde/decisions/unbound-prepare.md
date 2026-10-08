# Decision log: unbound-prepare

Goal: The project configuration declares preparation commands that Execution runs in an unbound run's checkout before any step, so configured checks there see the project's build output

## Task brief (main agent, 2026-10-08)

Resolves I-93a34180 (read it with `concorde issues show`). The first full project_review,
r-20261008T024839-project_review-a7857ff6 (unbound), ran every configured check in its unbound
checkout; that checkout has no build output (`generated/`), so 20 of 26 checks failed with
"no build found" and became false Issues (closed by hand as not-actionable).

Developer decision (2026-10-08), chosen over linking the primary's build output and over skipping
checks unbound: **the project configuration declares preparation commands, and Execution runs
them in the unbound checkout before any step of an unbound run** (checks, workers). For this
checkout the declared command is `python3 scripts/concorde.py build`; add it to this checkout's
configuration in this task.

Left to the session: where the declaration lives (the project configuration
`.concorde/config.json` or another file, and which Module owns its schema), its shape (argv list,
time limit), whether the commands run inside the read-only check boundary or with write access to
the throwaway checkout only (they must never write the primary worktree), how a failing
preparation fails the run (error code, chain), whether bound runs use it too (a task session
prepares its own worktree today; keep that unless it is clearly better otherwise), and the guidance
text. Keep the runtime-path links as they are.

After merging, the main agent reruns project_review. Deliver with `task-validation` then `delivery`;
run the full suite once on the final input.

## Task session decisions (2026-10-08)

- **Where the declaration lives: `.concorde/preparation.json`, owned by Execution
  (`contract.execution.preparation`).** Spec core owns `.concorde/config.json` and refuses every
  other field there; the earlier profiles moved checks and runtime paths out to their owners'
  files for that reason, and Execution depends on the kernel alone, so it must not read Spec
  core's file. The file stays under `.concorde/` with the other trusted host configuration, so the
  work a run examines cannot change the command except by a commit. Only the committed file in the
  checkout counts, like the worker configuration. A missing file means nothing to prepare.
- **Shape:** `{"commands": [{"argv": [...], "timeout_seconds": <positive>}]}`, run in order; no
  other field (no `{python}` substitution: that is Method's, from Spec core's `python`; no `env`).
  This checkout declares `["python3", "scripts/concorde.py", "build"]`, 600 s.
- **Boundary:** each command runs in Check execution's read-only check boundary with one more
  writable mount, the unbound checkout itself (`execute_check(..., writable=True)`). The rest of
  the host, the primary worktree and the origin's runtime paths, which the checkout only links,
  stay read-only at the system call. So a preparation can never write the primary worktree.
- **When:** after the admission, before the first step (a new runner row `preparation`), so a
  run refused for its Modules or inputs costs no build. Bound runs do not use it: a task session
  prepares its own worktree, as now.
- **Failure:** the run ends `failed` before any step. `preparation_invalid` (reason `input`) for a
  file that breaks its contract; `preparation_failed` (reason `environment`) for a command that
  exits non-zero, times out or cannot get its boundary. The cause is the `component` link of
  `Execution (unbound preparation)` with the command, its exit, its log path and the log's tail
  (and Check execution's `check_sandbox_unavailable` link below it for a boundary failure). Each
  command's log is kept in the run's node as `preparation/<n>.log`, with `preparation` host
  evidence.
- **Refinement of the failure reason:** the run's link takes its cause's reason: `input` for an
  invalid file (`invalid_preparation`) and for a command that exited non-zero or ran out of time
  (`preparation_command_failed`, `preparation_timed_out`: the command and the commit are the
  project's to repair), `environment` for a boundary that could not be set up
  (`preparation_sandbox_unavailable` over Check execution's `check_sandbox_unavailable`).
- `contract.execution.run-result` goes to version 5 (schema unchanged): the runner gains the
  evidence kind `preparation`. New `contract.execution.preparation` version 1.
- The boundary variant is Check execution's `execute_check(..., writable_project=True)`
  (`req.checks.writable-project-only`); no configured check uses it.
- Also documented the file in `docs/using-concorde.md` (user guide, bound to no Module) and the
  execution guidance (`prompts/guidance/execution/skill.md`).

## Report 1 to the main agent (concorde-d4), 2026-10-08T05:58:17Z

Delivered unbound-prepare: delivery commit 3b0702cc (delivery run r-20261008T054903-delivery-5e700c43; task-validation r-20261008T054012-task_validation-eaf0e6fa ready; full suite 1316 passed, 5 skipped). Resolves I-93a34180 (added with task resolve).

What it does: a project commits .concorde/preparation.json, {"commands": [{"argv": [...], "timeout_seconds": N}]} (contract.execution.preparation v1, owned by Execution). After the admission and before the first step of an unbound run, the runner runs the commands in order in the checkout, inside Check execution's boundary with the checkout as the only writable place besides the scratch (new execute_check(writable_project=True), req.checks.writable-project-only): the primary worktree, the origin and the linked runtime paths (.venv, node_modules) stay read-only at the system call. A non-zero exit, a timeout or no boundary ends the run failed with preparation_failed before any step (cause: Execution (unbound preparation) preparation_command_failed / preparation_timed_out / preparation_sandbox_unavailable, with the command, exit, log and log tail); an invalid file ends it with preparation_invalid. Logs: .concorde/unbound/<run-id>/preparation/<n>.log, plus preparation host evidence. This checkout declares python3 scripts/concorde.py build (600 s); probed in the boundary it builds in about 0.5 s.

Decisions I took (all in the decision log): the file is Execution's own .concorde/preparation.json, not Spec core's config.json (that file refuses other fields, and Execution depends on the kernel only); only the copy committed in the checkout counts; argv is taken literally (no {python}, no env); preparation runs after the admission so a refused run builds nothing; bound runs are not prepared (task sessions prepare their worktrees, as before); the run's reason is its cause's (input for a bad file or a failing command, environment for a missing boundary); run-result contract bumped to v5 for the new evidence kind. I also documented the file in docs/using-concorde.md and the execution guidance.

Open: nothing for the developer. I did not push the task branch. After the merge, project_review's unbound checks will build first, so rerunning it should no longer produce the 'no build found' Issues.

## Answer to report(s) 1 of the task session, 2026-10-08T06:13:53Z

Accepted; the main agent merges the task now.

## Closed: merged, 2026-10-08T06:14:25Z
