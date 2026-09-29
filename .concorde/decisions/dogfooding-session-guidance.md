# Decision log: dogfooding-session-guidance

Goal: Developer-approved panel-review decisions for Dogfooding, Main session and Task sessions: (dogfooding F5) a defect seen in a run that ended ok is reported with the main agent's own link, without causes, as the whole chain, written by hand in the error contract's shape and citing the run in evidence; (dogfooding F6) a defect seen outside a task gets the same hand-written link and is kept only under .concorde/runs/defects/ and named to the developer, no task opened for it; (dogfooding F7) after opening the task, the Concorde repository session appends a report naming the at-fault Module as owner_target_id (DEVELOPING.md step 1 and Dogfooding's 'Fixing it'); (main-session F9) decision-log and extend-chain apply to task runs; for a failed unbound run the guidance shows the developer the whole rendered chain, and opens a task and escalates with --error-file .concorde/runs/<run-id>/result.json when the failure leads to work, with a scenario; (pi run view) the pi run view also follows runs started elsewhere (e.g. by bash or another session) by watching the run store, as Usage says, with tests; (task session and workflow decision points) a task session runs workflows only in no-ask mode, whose decisions reach its report, and escalates to the main agent what needs the developer; update the task-session guidance and Specs. Update prompts (then build), Specs and tests.

## Task session decisions (2026-09-29)

- **F6, the hand-written link's cause outside a task.** Options: no causes at all; the failure's
  own error as its only cause. Chose the latter (the refusal's `error`, or the `error` of the
  unbound run's `result.json`), keeping the existing guidance sentence and never dropping a
  child's chain; a run that ended `ok` still gets the cause-less link of F5.
- **F9 scope "failed".** Options: only `failed` unbound runs; every unbound run that is not `ok`.
  Chose "not `ok`": a `blocked` unbound result carries an error chain and belongs to no task's
  decision log just the same.
- **F9 in pi.** The guidance says to show the developer the rendered chain "from the message that
  wakes you" in pi, so the pi run view's wake message (and `concorde_run`'s answer for a run that
  ended at once) now appends the result's whole error chain, rendered like a failed round's.
- **pi run view: which runs are followed.** Options: runs of this session only; every run of the
  project. Chose every run, as Usage says, including a pi task session's runs: every run still
  running at session start and every run started since (also one that ended between two looks);
  a run that had ended before the session started is only listed by `/concorde`. A run whose
  runner `concorde_run` is still starting is left to that tool, so none is reported twice.
- **Requirement and scenario identities.** Added `req.dogfooding.ok-run-defect`,
  `req.dogfooding.defect-outside-task`, `req.dogfooding.owner-assigned`,
  `req.main-session.unbound-failure`, `req.main-session.pi-run-follow`,
  `req.main-session.task-session-no-ask`, `scenario.main-session.unbound-failure` and
  `scenario.main-session.task-session-workflow`; extended `scenario.dogfooding.guidance`,
  `scenario.dogfooding.concorde-instructions` and `scenario.main-session.pi-run-view`.
- **A no-ask workflow decision of major impact in an `ok` result.** `concorde task escalate`
  needs a cause (`--run`, `--error-file` or `--escalation`) and an `ok` workflow report carries no
  error, so such a decision cannot be escalated with the command. Chose to have the task session
  name it in its report (pi: `open`; Claude Code: the SendMessage report) with its step, options
  and recommendation, for the main agent to put to the developer; a not-`ok` workflow result is
  escalated with the report as `--error-file`. Open point for the main agent: letting Tasks
  record a cause-less escalation would be a change to Tasks, outside this task's Modules.

## Closed: merged, 2026-09-28T17:32:47Z
