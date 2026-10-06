# Main session scenarios

Situations the [main-session guidance](module.md) prepares the
[main agent](../../glossary.json#concept.main-agent) for, and what holds for the sessions it
guides.

## Working method

### scenario.main-session.project-terms — Every session starts with the project's terms

- GIVEN a project whose root Module declares a glossary that can be read, with Concorde installed
- WHEN the main agent's session or a task session starts in one of its worktrees
- THEN the Concorde block of that worktree's `CLAUDE.md` imports the glossary
- AND because the block imports the glossary, Claude Code loads every term with its identity, owner
  and definition at launch
- AND the rest of `CLAUDE.md` is kept

### scenario.main-session.project-terms-missing — A session without a declared glossary starts without terms

- GIVEN a project whose root Module declares no glossary yet, with Concorde installed
- WHEN the main agent's session or a task session starts in one of its worktrees
- THEN the Concorde block of `CLAUDE.md` imports no glossary
- AND the session starts without terms and without an error

### scenario.main-session.change-through-task — The guidance routes an agreed change through a task session

- GIVEN the rendered [main-session guidance](../../glossary.json#concept.main-session-guidance)
- WHEN a main agent reads how to carry out a change agreed with the developer
- THEN the main agent is told to open a task with its own branch and worktree for the Modules
  involved
- AND the main agent is told to hand it to a
  [task session](../../glossary.json#concept.task-session), even when it is the only task
- AND the main agent is told never to work inside a task worktree itself
- AND the task-session guidance tells the session to make the change inside that worktree, directly
  or with [Operations](../../glossary.json#concept.operation) and the
  [execution commands](../../glossary.json#concept.execution-command) `task-validation` and
  `delivery`
- AND the guidance tells the session to run every `concorde` command that works on the task's
  workspace with the worktree's own copy
- AND the task-session guidance tells the session that `concorde task open` bound the worktree as
  the task's workspace
- AND that every run reads that workspace's binding without naming the task
- AND that a second run while one runs is refused with `workspace_busy`
- BUT the main agent is told never to change Specs or code in the primary worktree beyond a small
  change the developer approved

### scenario.main-session.small-change — The guidance makes a small change only with the developer's approval

- GIVEN the rendered main-session guidance
- WHEN a main agent reads whether it may fix a typo or a one-line defect directly in the primary
  worktree
- THEN it is told that such a small change may be made there only after it told the developer what
  it would change and why it is small
- AND that the developer must have approved that specific change first
- AND the main agent is told that without that approval the change runs in a task

### scenario.main-session.parallel-tasks — The guidance allows parallel work only between worktrees

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to plan several changes
- THEN it is told to run tasks in parallel only in separate worktrees whose Modules and shared files
  do not overlap
- BUT it is told to run tasks that write the same [Module](../../glossary.json#concept.module) or
  shared file one after another

### scenario.main-session.split-into-sessions — The guidance hands every task to a task session

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to carry out the tasks it opened
- THEN the main agent is told to start one [task session](../../glossary.json#concept.task-session)
  per task, even for a single task, as a background Claude Code session
- AND the main agent is told to start that session with `concorde task session` naming its own
  session with `--main`
- AND the main agent is told to record the task's
  [task brief](../../glossary.json#concept.task-brief) in its
  [decision log](../../glossary.json#concept.decision-log) before starting the session
- AND the main agent is told to stay in the primary worktree
- AND the main agent is told to answer a task session's escalation or pass it to the developer with
  its own link on top

### scenario.main-session.batched-decisions — Decisions travel up together and come back together

- GIVEN the rendered main-session and task-session guidance
- WHEN a task session meets decisions its task needs that are not its own
- THEN the task session is told not to wait in the middle of its work
- AND the task session is told to carry on with what does not depend on those decisions and then
  escalate all of them together in one report
- AND the main agent is told to decide those its authority covers
- AND the main agent is told to put all the others to the developer at once
- AND the main agent is told to answer the session once with every answer

### scenario.main-session.task-session-role — The task-session guidance keeps a session within its task

- GIVEN the rendered task-session guidance
- WHEN a task session reads how to work
- THEN the task session is told to read the task's decision log first
- AND the task session is told to work only inside its task worktree with the worktree's own
  `concorde` command
- AND the task session is told to escalate beyond its task's goal or Modules with
  `concorde task escalate --by task-session`
- AND the task session is told to record every escalation first and then send them together with
  SendMessage
- AND the task session is told to report to the main agent when the task is delivered or cannot go
  further without decisions that are not its own
- BUT the task session is told never to merge the task branch into the primary branch or close the
  task

### scenario.main-session.task-session-report — A task session records its report and follows a rebind

- GIVEN the rendered task-session guidance
- WHEN a task session has delivered its task or escalated every decision it needs
- THEN the task session is told to record the report first with `concorde task report`, naming the
  escalations it carries
- AND the task session is told then to send the report with SendMessage to the `main` that command
  prints
- AND when SendMessage reaches no session of that name, the task session is told to run
  `concorde task wait <task> --rebound <that name>` in background Bash
- AND in that case, the task session is told to send the same report to the name the wait command
  returns
- AND the task session is told that an answer names the reports it answers
- AND the task session is told that an answer to a report it already acted on, matched by that
  number, changes nothing

This illustrates
[recording a report first](requirements.md#req.main-session.task-session-report-recorded) and
[its addressee](requirements.md#req.main-session.task-session-report-addressee). It also illustrates
[sending it again](requirements.md#req.main-session.task-session-report-resent) and
[an answer acted on once](requirements.md#req.main-session.task-session-answer-once).

### scenario.main-session.reconcile-after-restart — The main agent rebinds its tasks after its session name changed

- GIVEN the rendered main-session guidance
- WHEN ListAgents reports for the main agent's session a name other than the one it gave its tasks,
  as after a resume
- THEN the main agent is told to run
  `concorde task list --main <former> --state open,active,delivered,merging`, which lists only the
  tasks not ended
- AND to rebind each task listed with `concorde task rebind <task> --main <current>`
- AND to read the reports `concorde task show` lists without an answer
- AND to do these three things before anything else
- AND to send again the latest recorded answer of each listed task whose last report has one, naming
  the reports it answers, since the restart may have come between recording it and sending it
- AND to record each answer with `concorde task answer` before sending it, naming in it the reports
  it answers

This illustrates [listing the tasks](requirements.md#req.main-session.reconcile-after-restart) and
[rebinding them](requirements.md#req.main-session.reconcile-rebind). It also illustrates
[reading their unanswered reports](requirements.md#req.main-session.reconcile-unanswered) and
[sending a recorded answer again](requirements.md#req.main-session.reconcile-resend-answer). It also
illustrates [answers naming their reports](requirements.md#req.main-session.answers-name-reports).

### scenario.main-session.task-session-unrestricted — The task-session guidance gives one rule and no restriction besides

- GIVEN the rendered task-session guidance
- WHEN a task session reads what it may do
- THEN the task session is told that its one rule is to change nothing outside its task worktree,
  the task's [decision log](../../glossary.json#concept.decision-log) excepted
- AND the task session is told that nothing else about it is restricted
- AND the task session is told that because its commands run under no sandbox, it prepares its own
  worktree: dependencies, submodules and build outputs
- AND the task session is told that because its commands run under no sandbox, it probes the machine
  it runs on itself
- AND the task session is told that `concorde task merge` audits at the end that nothing outside the
  task worktree changed
- AND the task session is told to let every run of its workspace finish and to stop every other
  background command it started, confirming each ended, before `task-validation` and `delivery`
- AND the task session is told to edit and commit nothing in its worktree while a run of it runs,
  since the run's [write audit](../../glossary.json#concept.write-audit) attributes every change to
  its workers
- BUT the task session is told that Edit and Write still refuse every path outside the task worktree
  and its decision log

This illustrates
[the task session's one rule](requirements.md#req.main-session.task-session-guidance) and
[runs in the background](requirements.md#req.main-session.task-session-background-runs). It also
illustrates
[the quiet before validating](requirements.md#req.main-session.task-session-quiet-before-validation)
and
[the worktree left alone during a run](requirements.md#req.main-session.task-session-still-during-runs).

### scenario.main-session.task-session-prepares-workers — The task session creates and binds new implementation files before a worker fills them

- GIVEN the rendered task-session guidance and the main agent's skill
- WHEN a task's work needs a new implementation file outside the directories its Modules bind, such
  as one an `understand` plan lists in `new_files`
- THEN the task-session guidance tells the session to create the file with the least content its
  format needs to be valid
- AND to add it to the `entries` of the right realization and to commit both together
- AND to do all this before it launches the worker that fills the file
- AND the main agent's skill says the task session prepares the workers' environment this way
- AND both name the [delivery commit](../../glossary.json#concept.delivery-commit) as what
  `delivery` creates, the only commit that marks the task delivered
- BUT a new Spec document is not prepared this way
- AND both say that `specify` proposes the new Spec document
- AND both say that the Operation creates the new Spec document and registers it in its Module's
  `owns`

This illustrates [preparing the workers' environment](requirements.md#req.main-session.task-session-prepares-workers)
and [binding the files created](requirements.md#req.main-session.task-session-binds-new-files).

### scenario.main-session.task-session-plan-review — A task session leads the review of its plan

- GIVEN the rendered task-session guidance and the main agent's skill
- WHEN a task session wants its plan reviewed before it changes Specs or code
- THEN the task-session guidance tells the task session that `plan_review` is optional
- AND that the task session writes the plan itself
- AND to answer every finding with `--accept` or `--reject` in the next run, with the previous run
  as `--input`, until the verdict is `accepted`
- AND when the reviewer maintains a finding after the task session rejected it, and the session
  still rejects it, to escalate rather than run again on it
- AND the main agent's skill names `plan_review` among the Operations a task session runs
- BUT when the session now accepts a maintained finding's renewed reasoning, it answers with
  `--accept` and revises the plan, like any other finding

This illustrates
[an optional plan review](requirements.md#req.main-session.task-session-plan-review) and
[answering every finding](requirements.md#req.main-session.task-session-plan-review-iterates). It
also illustrates
[escalating a continuing disagreement](requirements.md#req.main-session.task-session-plan-review-disagreement).

### scenario.main-session.task-session-workflow — A task session runs its workflow in its brief's mode

- GIVEN the rendered task-session guidance
- WHEN a task session reads how to run a task that follows a known procedure
- THEN it is told to start the [workflow](../../glossary.json#concept.workflow) in its task worktree
  in the [mode](../../glossary.json#concept.workflow-mode) its
  [task brief](../../glossary.json#concept.task-brief) names
- AND when the task brief names no mode, to use interactive mode
- AND when a workflow ended `awaiting_decision`, to escalate every pending
  [decision point](../../glossary.json#concept.decision-point) at once, with the saved
  [workflow result](../../glossary.json#concept.workflow-result) as `--error-file`
- AND to start the same workflow again with every answer given so far
- AND to read the workflow result like a [run result](../../glossary.json#concept.run-result)
- AND to copy its decisions and problems into the task's
  [decision log](../../glossary.json#concept.decision-log)
- AND to give the workflow's decisions in its own report to the main agent, naming those of major
  impact for the developer
- AND when a workflow result is not `ok` and the task session cannot repair it within the task, to
  escalate with `concorde task escalate --by task-session` and that result as `--error-file`
- AND when a no-ask workflow took a decision of major impact that carries no error, to escalate with
  `concorde task escalate --by task-session` naming no run or file

### scenario.main-session.claude-sees-by-query — A main session sees another session's work by asking

- GIVEN two main sessions of the same project
- AND the second started a task session of the task `t1` naming itself with `--main`
- AND that task session started a run in its task worktree in background Bash
- AND the first registered no wait for that run
- WHEN that run ends
- THEN neither main session is woken by it, since its owner is the task session that started it
- AND nothing the first main session did not ask for is pushed into that main session
- AND the second hears of the run in the task session's report
- AND when the first asks, `concorde task show t1` lists the run with its status
- AND the command lists the task session with the main session it reports to

### scenario.main-session.merge-delivered — The guidance merges delivered work without asking

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do after `delivery` committed a task's change
- THEN it is told to merge the task from the primary worktree without asking the developer
- AND to use the project MCP server's `task_merge` or `concorde task merge <task>` in background
  Bash
- AND never to merge with `git merge` itself, because other main sessions may be merging
- AND that the merge runs `concorde spec-validation` unless the merge names other checks

### scenario.main-session.merge-command — The guidance runs the merge command in the background

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to merge a delivered task with `concorde task merge <task>`
- THEN it is told to run the command in background Bash because the command waits up to `--wait`
  seconds for the task's run and other merges
- AND on `merge_busy`, to run the command again
- AND on `workspace_busy`, to run `merge` or `close` again with a longer `--wait`

### scenario.main-session.merge-through-server — The guidance retries a busy `task_merge` after a registered wait

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to merge a delivered task with the project MCP server's `task_merge`
- THEN it is told that `task_merge` never waits for a lock
- AND it returns at once with the merge it started, or is refused at once with `workspace_busy` or
  `merge_busy` naming the holder
- AND on such a refusal, to register a wait for the busy lock with `register_wait`
- AND without a channel, alternatively to run the `concorde task wait` command it returns in
  background Bash
- AND once woken, to call `task_merge` again, which may be refused again

### scenario.main-session.merge-conflict — A merge conflict goes back to the task session

- GIVEN the rendered main-session and task-session guidance
- WHEN merging a delivered task fails with `merge_conflict`
- THEN the main agent is told to answer the task's session, starting one again if it has ended
- AND to tell the task's session to merge the primary branch into its task branch
- AND to tell the task's session to resolve the conflicts
- AND to tell the task's session to run `task-validation` and `delivery` again
- AND to tell the task's session to report
- AND the task session is told to make that merge in its task worktree
- AND that it is the only merge the task session makes

### scenario.main-session.update-merge — An update reaches the open tasks through their sessions

- GIVEN the rendered main-session and task-session guidance
- WHEN a `concorde update` that installed a new
  [Protocol copy](../../glossary.json#concept.protocol-copy) asks to merge the primary branch into
  each open task it lists
- THEN the main agent is told to answer each listed task's session, starting one again if it has
  ended
- AND to tell each listed task's session to merge the primary branch into its task branch
- AND to tell each listed task's session to run `task-validation` again
- AND when the task had delivered, to tell its session to run `delivery` too
- AND to tell each listed task's session to report
- AND the task session is told that a merge of the primary branch into its task branch, asked after
  a `concorde update`, is besides the one after a `merge_conflict` the only merge it makes
- BUT the task session is still told never to merge its task into the primary branch nor to rebase

### scenario.main-session.merge-interrupted — The guidance finishes an interrupted merge first

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do when a task command is refused with `merge_incomplete`
- THEN it is told to finish that merge before anything else with
  `concorde task merge <task> --resume`, without asking the developer
- AND to use `--abort` when the merge commit is no longer the primary branch's head
- AND to use `--abort` too when `--resume` answers `not_resumable`
- AND to bring `merge_diverged` to the developer
- AND a task session is told to send a `merge_incomplete` or `merge_busy` refusal of its escalation
  to the main agent

### scenario.main-session.no-polling — Every wait wakes the agent or blocks once

- GIVEN the rendered main-session and task-session guidance
- WHEN an agent reads how to wait for a run, a busy workspace, a task session or a merge
- THEN it is told never to wait by polling with `sleep` loops
- AND to queue a run behind a running one with `--wait <seconds>`
- AND a task session is told to run long `concorde` commands in background Bash

## Worker models

### scenario.main-session.choose-models — The guidance lets the developer choose worker models

- GIVEN the rendered main-session guidance
- WHEN a developer asks the main agent to change the models workers use
- THEN it is told that unless the tracked `.concorde/workers.json` chooses Claude Code for them,
  workers run on pi
- AND workers take their models and limits from that file by
  [worker id](../../glossary.json#concept.worker-id)
- AND a task carries that file from its base commit
- AND to edit the JSON directly, preserving unrelated overrides, since there is no editor
- AND to commit a change of that file alone directly on the primary branch for future tasks
- AND while a merge is unfinished, never to commit that change
- AND that a task may change its own copy
- AND when the task merges, its copy reaches the primary branch
- AND that separate `scripts/available_models.py` discovery supplies advisory configured candidates
  without inference API probes
- AND custom/offline names require no discovery
- AND when asked, to set the JSON backend to `claude`
- AND program installation is required at launch rather than at configuration time
- AND an entry that only chooses a backend keeps the model and level it inherits
- BUT to change worker models only when the developer asks

### scenario.main-session.worker-configuration-required — The guidance runs workers only on the configured models

- GIVEN the rendered main-session guidance
- WHEN a main agent is about to run an Operation in a project
- THEN it is told that every worker runs only on what the tracked `.concorde/workers.json` enables
  and chooses
- AND it is told that workers never run on anyone's own pi or Claude Code settings
- AND it is told that only credentials and provider definitions come from those settings
- AND it is told that no worker runs without the file
- AND it is told that the installer does not write the file
- AND it is told that, when the project has no file, it therefore asks the developer for the enabled
  models and the default
- AND it is told that it then writes the file and commits it alone on the primary branch before any
  Operation runs
- AND it is told that the file's required `enabled_models` lists every model an entry may name by
  its project model name, each with an optional level of its own
- AND it is told that a model outside that list is refused with `model_not_enabled`
- AND it is told that a worker without a model is refused with `model_unresolved`
- AND it is told that the developer's untracked [model map](../../glossary.json#concept.model-map)
  gives each project model name its local id per program
- AND it is told that a worker the map cannot resolve is refused with `model_unmapped`,
  `model_map_missing` or `model_map_invalid`
- AND it is told that, only when the developer asks or agrees, the main agent changes the map,
  telling the developer the entry a new model needs
- AND it is told that a worker takes its model's entry's level or a more specific one's
- AND it is told that, otherwise, the worker takes the model's own level
- AND it is told that, otherwise, the worker takes a less specific entry's level
- AND it is told that, otherwise, the worker takes its program's built-in default
- BUT a model the developer adds for a worker goes into `enabled_models` too

### scenario.main-session.no-task-operations — The guidance runs questions and reviews without a task

- GIVEN the rendered main-session guidance
- WHEN a main agent needs to understand or review a Module without changing it
- THEN it is told that `understand`, `survey`, `spec_panel` and `code_review` also run unbound
- AND it is told that such unbound runs run in a worktree without a
  [workspace binding](../../glossary.json#concept.workspace-binding), such as the primary worktree
- AND it is told that such unbound runs have `workspace` null in their result
- AND it is told that such a run examines an
  [unbound checkout](../../glossary.json#concept.unbound-checkout) of that worktree's `HEAD`, not
  its uncommitted changes
- AND it is told that such a run names that commit as `commit` in its result
- AND it is told that such a run changes no [Spec](../../glossary.json#concept.spec) or code, since
  it launches only reading workers
- BUT every change still runs in a task
- AND an `--input` of an unbound run must be unbound too

### scenario.main-session.brownfield — The guidance adopts existing code through the brownfield workflow

- GIVEN the rendered main-session guidance
- WHEN a main agent has just initialized a project whose code came before its Specs
- THEN it is told to open a task bound to the root Module
- AND it is told to have that task's session run the
  [brownfield workflow](../../glossary.json#concept.brownfield-workflow) inside that task's worktree
- AND it is told that the workflow never names the task
- AND it is told that, unless the developer already said, it asks the developer for interactive or
  no-ask mode
- AND it is told to name the mode in the task's [task brief](../../glossary.json#concept.task-brief)
- AND it is told that, when the task session escalates the pending
  [decision points](../../glossary.json#concept.decision-point) of a workflow that ended
  `awaiting_decision`, it decides those its authority covers
- AND it is told that, when the task session escalates those pending points, it puts the rest to the
  developer at once
- AND it is told that, when the task session escalates those pending points, it answers the session
  with every answer
- AND it is told that the task session starts the workflow again with those answers
- AND it is told to read the [workflow result](../../glossary.json#concept.workflow-result) saved
  beside the workspace's [workflow record](../../glossary.json#concept.workflow-record) like a run
  result
- AND it is told that the task session copies that result's decisions and problems into the task's
  [decision log](../../glossary.json#concept.decision-log)
- AND it is told to merge the delivered task

### scenario.main-session.ordinary-decision — The guidance decides ordinary questions and reports them

- GIVEN the rendered main-session and task-session guidance
- WHEN a task session reads how to handle its task's run result blocked on a choice of ordinary
  scope, such as a name or an internal structure
- THEN it is told to decide
- AND it is told to record the decision and its reason in the task's decision log
- AND it is told to record every result that is not `ok` in the task's decision log
- AND it is told to report the decision at the end
- AND the main agent is told to decide an ordinary question of a task itself
- AND the main agent is told to record that decision and its reason in the task's decision log
- AND the main agent is told to report it at the end
- BUT neither is told to stop and ask the developer

This illustrates
[the task session's records](requirements.md#req.main-session.task-session-decision-log) and
[the main agent's records](requirements.md#req.main-session.decision-log). It also illustrates
[deciding ordinary questions](requirements.md#req.main-session.ordinary-decisions).

### scenario.main-session.major-decision — The guidance escalates major decisions with their evidence

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle a result whose options would change what a Module promises
  to its users
- THEN it is told to ask the developer before acting
- AND it is told to escalate with `concorde task escalate`, adding its own link on top of the
  [error chain](../../glossary.json#concept.error-chain) instead of replacing it with a summary

### scenario.main-session.read-error-chain — The guidance reads the whole error chain

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle a result that is not `ok`
- THEN it is told that the result carries an error chain in `error`
- AND it is told what each link holds
- AND it is told to read the whole chain before deciding

### scenario.main-session.spec-tooling-error — The guidance translates a Spec tooling error before escalating it

- GIVEN the rendered main-session and task-session guidance
- AND a Spec tooling command, such as `concorde spec-validation` or `concorde registry --write`,
  that refused with Spec tooling's own
  [error record](../../spec-tooling/spec/errors.md#contract.spec.error)
- WHEN a session that cannot handle that error reads how to escalate it
- THEN it is told that the record is not a link of the
  [error chain](../../glossary.json#concept.error-chain)
- AND it is told that `concorde task escalate` refuses the record as `--error-file` with
  `invalid_error`
- AND it is told to translate the record into a `component` link of actor
  `Spec tooling (concorde <command>)`
- AND it is told that the link's detail keeps the record's message, reason, location and remediation
- AND it is told that the link's causes are the record's causes translated the same way
- AND it is told to save that link in a file and to escalate with it as `--error-file`

This illustrates [translating a Spec tooling error](requirements.md#req.main-session.spec-tooling-errors).

### scenario.main-session.unbound-failure — The guidance brings a failed unbound run to the developer whole

- GIVEN the rendered main-session guidance
- AND an [unbound run](../../glossary.json#concept.unbound-run) of `spec_panel` in the primary
  worktree that ended `failed`
- WHEN a main agent reads how to handle its result
- THEN it is told that the decision log and `concorde task escalate` cover the runs of a task
- AND it is told that an unbound run belongs to no task
- AND it is told to show the developer the run's whole rendered error chain, never a summary of it
- AND it is told that, when the failure leads to work, it opens a task for that work
- AND it is told that, when the failure leads to work, it escalates in that task with
  `--error-file .concorde/unbound/<run-id>/result.json`
- AND it is told that this escalation records the run's chain under its own link
- BUT it is told not to name the unbound run with `--run`, which names only runs of the task's own
  workspace

## Issues

### scenario.main-session.record-issue — The guidance records a problem deliberately

- GIVEN the rendered main-session and task-session guidance
- WHEN a session reads how to retain a problem the current task will not fix
- THEN it is told to read the Issues of the Module concerned before recording, never the whole
  project's list
- AND it is told to use `issue_list` filtered by `module` and `status` to read open Issues
- AND it is told that, when the problem may have been fixed before, it also reads closed Issues
- AND it is told to use `issue_show` before recording
- AND it is told to append to the matching open [Issue](../../glossary.json#concept.issue) at its
  current revision or reopen a closed one
- AND it is told to record through the project MCP server's `issue_report` or with the
  `concorde issues` command, which answers the same way
- AND it is told to record with a complete description, impact, basis, evidence, tier and severity
- BUT it is told that repeating a creation creates another Issue

This illustrates [inspecting before recording](requirements.md#req.main-session.issues-recording)
and [appending to a tracked problem](requirements.md#req.main-session.issues-append). It also
illustrates [the Issue tools](requirements.md#req.main-session.issues-through-server).

### scenario.main-session.issue-tiers — The guidance fixes Issues by their tier

- GIVEN the rendered main-session and task-session guidance
- WHEN a session reads what it may do with an Issue of each tier
- THEN a task session may fix an `obvious-fix` Issue alone
- AND a task session may fix a `preferred-fix` Issue, reporting the fix it chose
- AND a task session escalates a `decision-needed` Issue by its identity for the main agent or the
  developer to decide
- BUT a review Operation only reports
- AND a `suggestion` blocks nothing

This illustrates [tiers deciding who fixes](requirements.md#req.main-session.issues-tiers) and
[reporting a chosen fix](requirements.md#req.main-session.issues-preferred-fix-reported). It also
illustrates [escalating a decision](requirements.md#req.main-session.issues-decision-needed).

### scenario.main-session.issue-severity — The guidance rates every Issue and fixes the most severe first

- GIVEN the rendered main-session and task-session guidance
- WHEN a session reads how to record an Issue and the main agent how to choose which Issues to fix
- THEN every report is to carry a severity beside its tier
- AND each severity, `critical`, `high`, `medium` or `low`, is to come with what it means
- AND the main agent is told to choose what to fix first from the open Issues listed with
  `issue_list` sorted by `severity`
- BUT the severity is not said to decide who fixes an Issue, which stays the tier's

This illustrates [severity deciding what is fixed first](requirements.md#req.main-session.issues-severity).

### scenario.main-session.review-issues — The guidance acts on a review's Issues

- GIVEN the rendered main-session and task-session guidance
- WHEN a task session reads what to do after `spec_panel` or `code_review`
- THEN it is told that the review reported every finding as an Issue
- AND it is told that the result names those Issues with the earlier Issues that stand and those
  found resolved
- AND it is told to fix them by their tier in later `specify` or `implement` work, never in the
  review
- AND it is told to escalate a `code_review` finding that challenges the Spec rather than change the
  promise
- AND it is told to close each Issue the review found resolved, through `task resolve` when its task
  fixed it and otherwise with `issue_close`

This illustrates [a review's Issues](requirements.md#req.main-session.review-issues) and
[closing those it found resolved](requirements.md#req.main-session.review-resolved-closed).

### scenario.main-session.module-code-review — The guidance names the Module review

- GIVEN the rendered main-session and task-session guidance
- WHEN a main agent or a task session looks for a review of a Module's whole code
- THEN it is told that `code_review --scope module` judges each named Module's whole code against
  all of its Specs
- AND it is told that the review uses one reviewer per Module
- AND it is told that the review suits a whole-Module check after a large change, on code written
  before its Specs or by an earlier version, or on a project just adopted

This illustrates [the Module review](requirements.md#req.main-session.module-code-review).

### scenario.main-session.solve-issue — The guidance closes a fixed Issue with its task's merge

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to solve an open Issue owned by a Module
- THEN it is told to open a task for that Module naming the Issue with `--resolves`, or to name it
  later with `task_resolve`
- AND it is told that the task's merge closes it as `resolved` with the merge commit as evidence
- BUT starting or delivering the task does not itself close the Issue

This illustrates [closing with the merge](requirements.md#req.main-session.issues-close-with-merge).

### scenario.main-session.issue-system-failure — The guidance keeps Issue-system failures out of Issues

- GIVEN the rendered main-session and task-session guidance
- WHEN a session reads what to do when an Issue tool or command fails for a task
- THEN it is told to carry the error chain in the task's decision log and escalation, or a run's
  result
- BUT it is told never to report that failure as an Issue

This illustrates [never an Issue](requirements.md#req.main-session.issues-own-failures) and
[the task carrying the chain](requirements.md#req.main-session.issues-failure-chain).

### scenario.main-session.issue-system-failure-no-task — The guidance shows an Issue-system failure without a task to the developer whole

- GIVEN the rendered main-session guidance
- AND an `issue_report` of the main agent's own, made for no task, is refused with `commit_failed`
- WHEN the main agent reads what to do with that refusal
- THEN it is told that the decision log and escalation belong to a task
- AND it is told to show the developer the whole error chain at once, never a summary of it
- AND it is told to open a task only when the failure leads to work
- BUT it is told never to report that failure as an Issue

This illustrates [a failure without a task](requirements.md#req.main-session.issues-failure-no-task).

### scenario.main-session.issue-recovery — The guidance says how Issue records are put back

- GIVEN the rendered main-session and task-session guidance
- WHEN a session reads what to do on `recovery_failed`, `uncommitted_change` or a merge's
  `primary_dirty`
- THEN the main agent is told to run `concorde issues recover` once the cause of `recovery_failed`
  is fixed
- AND the main agent is told to inspect and revert a record no Issue write changed
- AND the main agent is told never to commit that record by hand
- AND the main agent is told that a merge first puts back what a killed Issue write left
- BUT a task session is told to leave both refusals to the main agent

This illustrates [Issue recovery](requirements.md#req.main-session.issues-recovery).

## The project MCP server

### scenario.main-session.project-mcp-session — The server declares its tools and the channel capability

- GIVEN a Claude Code session that starts the
  [project MCP server](../../glossary.json#concept.project-mcp-server), `concorde project-mcp`
- WHEN it initializes the session and lists the tools
- THEN the server answers with a protocol version it supports, the tools capability and the
  experimental `claude/channel` capability
- AND it lists `task_list`, `task_show`, `trace_show`, `run_result`, `workflow_report`, `locks`,
  `task_open`, `task_escalate`, `task_rebind`, `task_report`, `task_answer`, `task_close`,
  `task_resolve`, `task_merge`, `register_wait`, `workflow_step`, `issue_list`, `issue_show`,
  `issue_check`, `issue_report`, `issue_close` and `issue_reopen`

### scenario.main-session.project-mcp-queries — Queries answer the project from any worktree

- GIVEN a project with an open task `t1`, and a server started in the task's worktree
- AND no process holds the merge lock or the workspace lock of `t1` while the calls run
- WHEN the session calls `task_list`, `task_show`, `trace_show` and `locks`
- THEN each answers from the primary worktree's records as `concorde task list`, `task show` and
  `trace show` do
- AND `locks` says that nobody holds the merge lock or the workspace lock of `t1`

### scenario.main-session.project-mcp-refusals — Refusals are error links

- GIVEN a running server
- WHEN a call names an unknown task, lacks a required argument or names no tool of the server
- THEN each is refused with an error link
- AND for the unknown task, the refusal uses Tasks' own `unknown_task` link
- AND otherwise, the refusal uses the server's own `invalid_input` link
- AND `trace_show` of a node no reader finds is refused with the link `concorde trace show` prints,
  Tracing's own, with its explanation and options

### scenario.main-session.project-mcp-run-result — run_result answers for runs only

- GIVEN a task `t1` whose workspace holds a run with a saved result
- AND that workspace holds a run whose runner holds its
  [run lock](../../glossary.json#concept.run-lock)
- AND that workspace holds a run whose runner ended without writing a result
- WHEN the session calls `run_result` for each, for `t1` and for an identity no reader finds
- THEN the first answers `running` false with its result
- AND the second answers `running` true with its
  [run progress file](../../glossary.json#concept.run-progress-file)
- AND the third answers `running` false with no result and the run progress file its runner left
- AND `t1`, a task's node, and the unknown identity are both refused with `unknown_run`

### scenario.main-session.project-mcp-fresh-code — A call answers with the Concorde current when it arrives

- GIVEN a server whose session listens to it, in a project whose primary worktree's `concorde` runs
  one Concorde
- AND that Concorde answered a `task_list` call
- WHEN that Concorde changes while the session runs, as a merge or `concorde update` changes it, so
  that `task_list` answers otherwise and a tool is added
- AND the session calls `task_list` again
- THEN the second call answers with the changed Concorde
- AND the server tells its session that its tools changed
- AND its next `tools/list` lists the added tool, which answers
- BUT once the primary worktree's `concorde` exits without an answer, a call is refused with the
  server's own `call_failed` link naming its exit status and what it printed

This illustrates [every call answering with the current Concorde](../../distribution/requirements.md#req.distribution.mcp-current-code).

### scenario.main-session.project-mcp-short-writes — Short writes take structured arguments

- GIVEN a running server
- WHEN the session opens a task with `task_open`
- AND the session escalates in it with `task_escalate` as a task session with two options
- AND the session rebinds it with `task_rebind`
- AND the session reports with `task_report` carrying that escalation
- AND the session answers the report with `task_answer`
- AND the session closes it with `task_close` as completed with a note
- THEN the task is opened as the matching `concorde task` command does
- AND the escalation is recorded as number 1 with the level `task-session`, as the matching command
  does
- AND the record names the rebound session as the matching command does
- AND the report is recorded as number 1 addressed to the rebound session and then answered, as the
  matching command does
- AND the task ends closed as the matching command does
- AND from a session in the primary worktree, an escalation naming no `by` is recorded with the
  level `main-agent`
- AND from a session in the task's worktree, such an escalation is recorded with the level
  `task-session`

### scenario.main-session.project-mcp-issues — The Issue tools manage the project's Issues from any worktree

- GIVEN a running server in a task worktree and another in the primary worktree
- WHEN the task session checks and records a report with `issue_report`
- AND the main agent lists, checks and shows it
- AND the main agent names it with `task_resolve`
- AND the main agent closes it with `issue_close` twice
- AND the task session reopens it with `issue_reopen`
- THEN the Issue's record lies in the primary worktree
- AND its report is the task session's with its task
- AND the main agent's list shows it with its severity and tier at once
- AND the [task record](../../glossary.json#concept.task-record) names the Issue the task resolves
- AND the first close succeeds with `main-agent` as actor
- AND the second close is refused with the Issues command's own `closed_issue` link
- BUT while another process holds the merge lock, a report is refused at once with `merge_busy`
- AND that refusal is an environment failure whose options say never to report it as an Issue

This illustrates [queries and short writes answering as their commands](requirements.md#req.main-session.project-mcp-presentation).

### scenario.main-session.project-mcp-lock-busy — A busy lock is refused at once, naming its holder

- GIVEN a delivered task `t1` whose workspace lock another session's process holds for task `t1`
- WHEN the session calls `task_merge` for `t1`
- THEN the call is refused at once with `workspace_busy`, whose detail names the other session
  and the task
- AND the refusal's evidence carries the holder line with its process
- AND once that lock is free but another process holds the merge lock, `task_merge` is refused
  with `merge_busy` naming that holder
- AND in that case, the workspace lock it had taken is free again
- AND the task is still delivered

### scenario.main-session.project-mcp-lock-handover — The merge process owns the locks it was granted

- GIVEN a delivered task `t1` and a merge check that waits for a signal
- WHEN the session calls `task_merge` for `t1` and the check has started
- THEN the [merge lock](../../glossary.json#concept.merge-lock)'s holder line names the merge
  process
- AND the task's [workspace lock](../../glossary.json#concept.workspace-lock)'s holder line names
  the merge process
- AND the task's merge attempt lock's holder line names the merge process
- AND those holder lines name the session
- AND those holder lines name the task
- AND the merge process has the lock files open
- AND the server has none
- AND when the server is killed, the locks stay held
- AND once the check ends, the merge closes the task
- AND once the check ends, the merge releases the locks
- AND the merge's answer is then in `output.json` of the attempt's node in the history
- AND the merge-end wait finds the merge's answer there

### scenario.main-session.project-mcp-merge-wakes — The end of a merge wakes the session

- GIVEN a server whose session listens to it as a channel, and a delivered task
- WHEN the session calls `task_merge` and the merge succeeds
- THEN the answer says the session will be woken
- AND a `merge_ended` event with exit code 0 arrives
- AND the event's content carries the merge's output

### scenario.main-session.project-mcp-merge-fallback — Without a channel the merge's end is awaited and kept

- GIVEN a server whose session does not listen to it as a channel, and an open task `t1` not yet
  delivered
- WHEN the session calls `task_merge` for `t1`
- THEN the answer names the attempt's folder `merges/1/` of the task
- AND the answer returns `concorde task wait t1 --merge` to run in background Bash
- AND that wait answers with the attempt `failed`
- AND the attempt's `output.json` holds the merge's refusal, the error of the attempt's node
- AND once `t1` is delivered, a second `task_merge` answers with the attempt `merges/2/`
- AND the second merge's wait returns with that attempt `ok`
- AND that attempt's `output.json` in the history holds the merge's answer that closed the task as
  merged

### scenario.main-session.workflow-step-tool — A workflow step through the server

- GIVEN a server whose session started in a bound task worktree, whose `task-validation` takes
  several seconds
- WHEN a [step agent](../../glossary.json#concept.step-agent) calls `workflow_step` for the step
  `validate` with a wait of 2 seconds
- THEN while the step call waits, the server answers another call
- AND the step call answers the step outcome with state `running` and its run
- AND after the session and its server end, the run still ends and saves its result
- AND a new session's `workflow_step` for the same key answers that the run finished without
  starting another run
- BUT from a session in the primary worktree, which has no workspace binding, the same call is
  refused with `unbound_worktree`
- AND a request the step command rejects is refused with that command's own `invalid_request` link
- AND a wait above 100 seconds is refused with `invalid_input`

### scenario.main-session.project-mcp-wait-channel — A registered wait wakes the session

- GIVEN a server whose session listens to it as a channel, and an open task whose workspace lock
  another process holds
- WHEN the session registers a wait for that lock and the holder dies
- THEN a `wait_done` event for the lock arrives naming the holder it waited for
- AND once a delivery made under the workspace lock releases that lock, a `wait_done` event wakes a
  wait registered for the task becoming delivered
- AND registering the same wait again answers at once that the task is delivered
- AND registering the same wait again registers nothing
- AND when its server is killed, a wait for a lock that stays held ends, so no wait outlives its
  session

### scenario.main-session.project-mcp-wait-fallback — Without a channel the wait names its command

- GIVEN a server whose session does not listen to it as a channel, and a held workspace lock of task
  `t1`
- WHEN the session registers a wait for that lock, or for `t1` becoming closed or failed
- THEN nothing is registered
- AND the answer says there is no channel
- AND the answer returns `concorde task wait t1 --lock workspace` or
  `concorde task wait t1 --until closed,failed` to run in background Bash

### scenario.main-session.project-mcp-channel-detection — The server reads its channel from the session's command line

- GIVEN the command lines of the server's ancestor processes
- WHEN one is a `claude` on a terminal started with
  `--dangerously-load-development-channels server:concorde` or with `server:concorde` among the
  entries of `--channels`
- THEN the server knows it has a channel
- BUT the same command line of a `claude` without a terminal, a background session, does not give
  the server a channel
- AND that command line of another program on a terminal does not give the server a channel
- AND `server:concorde` as the value of another option or another server's entry does not give the
  server a channel
- AND when `CONCORDE_CHANNEL` is set, `0` or `1` decides instead

### scenario.main-session.project-mcp-guidance — The guidance says how to start with the server and when to use it

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to merge a task and how to wait for a task, run or lock
- THEN the main agent is told to start its session with
  `--dangerously-load-development-channels server:concorde`
- AND the main agent is told to use `task_merge` and `register_wait`
- AND without a channel, the main agent is told to run the `concorde task wait` command those tools
  return in background Bash
- AND the main agent is told that a woken session is never handed a lock
- AND the main agent is told that a woken session asks again
- AND the main agent is told that the `concorde` commands stay the source of truth
- AND the task-session guidance tells a task session that, as a background session, it is never woken
  by channel events
- AND the task-session guidance tells the task session that, as a background session, it waits with
  `concorde task wait` in background Bash
