# Decision log: drop-pi-workflows

Goal: Stop rendering workflows for pi main sessions, which no longer exist: remove the pi-subagents workflow scripts and the pi step and report agents from the build, the --stdin forms of workflow step and workflow report, the pi wording of the glossary's step-agent and workflow entries, and "pi" from concorde.json clients; move the E2E deterministic driver and the workflow tests to the Claude Code rendering

## Brief (main agent, 2026-09-29)

Follow-up of task drop-pi-main-session (merged at b59c7127), which made the main agent and task
sessions Claude Code only while keeping pi as a worker backend. That task's escalation #1 left the
pi workflow rendering to this task (main agent's decision, recorded in its decision log).

Developer's decisions this task carries out: the main-session side supports Claude Code only for
now; pi stays a worker backend; no backward compatibility or migration shims.

Scope:

- Workflows: stop rendering workflow scripts for pi-subagents and the pi step and report agents
  (`generated/workflows/pi/` and their sources/templates), remove the `--stdin` forms of
  `concorde workflow step` and `concorde workflow report` if pi was their only user, and update
  the Workflows Spec, scenarios and contracts. The Claude Code rendering stays.
- Glossary: rewrite `concept.step-agent`, `concept.workflow`, `concept.workflow-script` and any
  other entry that still names pi or pi-subagents as a place workflows run.
- `concorde.json`: remove `"pi"` from `clients`, and whatever reads that list.
- E2E: move the deterministic driver and the workflow tests that run the pi rendering under a
  stand-in to the Claude Code rendering.
- Keep worker-side pi support untouched (permission extension, pi runtime, `backend: "pi"`, pi as
  the default worker backend). Escalate if a removal would reach it.

Left to the session: exact wording, test restructuring. Escalate anything that would change a
promise outside this scope. Do not start the project-level MCP server work; it is the next task.

## Task session decisions (2026-09-29)

- **Report request contract removed.** `contract.workflows.report-request` existed only for
  `concorde workflow report --stdin` (pi's `concorde-report` agent); with `--stdin` gone the report
  takes only `--lost`, so the contract section was deleted rather than kept unused. The step
  request contract stays (version unchanged): `--json` still takes it and its semantics never
  named `--stdin`.
- **`run_step(wait=None)` kept.** The Python API still accepts `wait=None` (wait until the run
  ends); only the CLI's `--stdin` used it. Left in place as an internal option; no promise names it.
- **Stand-in harness in execute mode.** `tests/concorde/workflows/run_script.mjs` now runs only the
  Claude Code render. With `execute: {cwd}` each stand-in step agent runs, through `/bin/sh`, the
  command line its relay prompt names (the line after "Run exactly this command…") in that
  directory and returns the JSON it printed, as a real step subagent would with Bash. The driver
  and the acceptance test pass the worktree's (or project's) `concorde` via the script's existing
  `args.concorde`, so the step commands are the real ones.
- **`req.workflows.one-source` kept its id**, retitled "One procedure, rendered for Claude Code".
- **Also updated beyond the named files**, within module.concorde: the levels-of-work table row of
  `specs/concorde/module.md` ("renders for Claude Code and for pi") and the `concorde.json`
  description ("for a Claude Code or pi main agent" → "for a Claude Code main agent").
- **Left untouched, for the main agent to consider:** the reference submodule
  `references/pi-subagents` (`.gitmodules`, `specs/concorde/development.md`) is no longer used by
  any Module now that no pi workflow is rendered; removing a submodule needs `.git/config`, which
  the task sandbox keeps read-only, and it is outside the brief. `docsite/tests/repository/run-checks.py`
  also lists a `pi` directory that no longer exists (unrelated to workflows).
- Lint note: the uvx ruff version reports pre-existing findings (RUF100, PLW1510, ISC004, I001) in
  untouched lines of `scripts/e2e/e2e.py`, `tests/…` and `src/concorde/workflows/step.py`; not
  addressed here.
- **Delivered** (2026-09-29): task-validation ready (24 checks, 0 warnings), delivery commit
  ce43f5abc093 on `concorde/drop-pi-workflows` with `.concorde/evidence/drop-pi-workflows/1.json`.
  Full suite before delivery: 763 passed, 4 skipped (live worker tests).

## Closed: merged, 2026-09-29T14:27:18Z
