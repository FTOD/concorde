# Decision log: brownfield-workflow

Goal: Add the code-to-spec task type, the survey/scaffold/code_to_spec Operations and a Workflows layer (preset tasks) with a brownfield workflow for adopting existing projects

## Design decisions (main agent, 2026-09-25)

Developer decisions, recorded for reference:
- Spec-driven stays the norm; brownfield is the rare code-first case.
- New Protocol task type `code-to-spec` (reads code, writes the Module's Specs, never code); it
  describes behaviour as it is; doubtful intent becomes an open question, never a promise.
- Brownfield is split into Operations composed by a new workflow layer; a workflow is a preset
  task (same level as a task), run as a Claude Code Workflow script or a pi-subagents workflowScript.
- A task runs several Operations, never two at once.
- Workflows have two modes: interactive (a decision point ends the run so the developer decides
  now) and no-ask (decide, continue, report every decision and problem at the end).
- The error chain must be complete through workflow, Operations and workers.

Choices made by the main agent without the developer:
- Protocol 13.0.0 -> 13.1.0: adding a task type is additive; no existing Spec becomes invalid.
- `survey` runs under task type `code-to-spec` with SpecScope withheld (the Protocol lets a harness
  give less), so it reads code but writes nothing; it may run with or without a task.
- `scaffold` is a deterministic host step (no worker): adding Modules is a project-level step that
  writes the registry and the parent's `contains`, as the Protocol requires.
- New provider Module Adoption (`module.adoption`, under Operations) owns survey, scaffold and
  code_to_spec; new Module Workflows (`module.workflows`, a child of the root beside Tasks and
  Operations) owns workflow steps, the workflow result and the brownfield script.
- Steps are idempotent by step key (`concorde workflow step`), which starts `concorde run --detach`
  and waits at most ~9 minutes per call, so a Claude step agent stays under Bash's 10-minute limit
  and a relaunched workflow returns finished steps at once. Answers change the step key, so an
  interactive rerun with answers runs that step again.
- The workflow result is assembled deterministically by `concorde workflow report` from the
  host-saved Operation results, never from what a step agent relayed, so the error chain cannot
  be paraphrased on the way.
- `code_to_spec` has no resume round for structural errors (a failed Spec check waits for a
  decision); in no-ask mode the workflow continues with the next Module and reports it.

Later choices (main agent, after the Spec review):
- Proposed checks are never configured by the scaffold: a check is a command the host runs, and a
  model chose it after reading unvetted code. The workflow result lists them for the developer.
- Interactive mode also ends at any step that did not end ok (the developer is present); no-ask
  continues past a non-ok code_to_spec and stops only where the procedure cannot go on.
- Answers are cumulative, keyed by base step key; an answered step admits the asking run with
  --input; retried or answered steps supersede every later step.
- Refused steps are recorded without a run; lost steps are detected from the host's pid.
- pi needs a second command-runner agent, concorde-report, because a runner has one fixed command.
- Claude step commands quote only the JSON request, so the installed prefix permission rule
  Bash(.concorde/bin/concorde workflow step:*) matches.
- The installer adds only missing permission rules and removes only rules its receipt recorded.

## Closed: merged, 2026-09-25T11:51:43Z
