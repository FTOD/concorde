# Main session scenarios

Situations the [main-session guidance](module.md) prepares the
[main agent](../../glossary.json#concept.main-agent) for, and what the pi
[run view](../../glossary.json#concept.run-view) does in them.

## Working method

### scenario.main-session.pi-task-worktree — pi runs a task's work with its worktree's copy

- GIVEN a pi main session in the primary worktree and a task whose record names an existing worktree
- WHEN the main agent starts an [Operation](../../glossary.json#concept.operation) or an [execution command](../../glossary.json#concept.execution-command) of that task with the `concorde_run` tool
- THEN the run view starts the task worktree's own `concorde`, with the task worktree as working directory, as `concorde run <operation>` or `concorde <command>` without naming the task
- AND the run works on the workspace the worktree's binding names
- BUT for a task whose record names no existing worktree the tool is refused before anything starts, naming the task

### scenario.main-session.pi-run-view — pi shows every run and its worker's progress

- GIVEN a pi main session with the run view and an Operation run whose worker is in its second round
- WHEN the run view reads the [progress files](../../glossary.json#concept.progress-file) of the [run store](../../glossary.json#concept.run-store)
- THEN it shows the run with its workspace, Operation, step, the worker's round and latest tool call
- AND a worker of another run is not attributed to it, even when that run's runner recorded the same process identifier in another PID namespace
- AND an execution command's run is shown the same way without a worker, and an [unbound run](../../glossary.json#concept.unbound-run) with `unbound` in place of the workspace
- AND a finished run shows `completed`, `stopped` or `failed` for `ok`, `blocked` or `failed` with the result's summary
- AND a run whose runner ended without finishing, so that nobody holds its [run lock](../../glossary.json#concept.run-lock), shows `failed` and is not counted as running, even when the process identifier it recorded names a living process
- AND the message the main agent is given for a finished run names the run, its workspace and name, its status and summary, and its [run result](../../glossary.json#concept.run-result)'s file, followed by the result's whole [error chain](../../glossary.json#concept.error-chain) when it carries one
- AND a run started after the session started by a command run with bash or by another session, even one that already ended, is shown and reported the same way
- BUT a run that had already ended before the session started is not reported, and a run whose runner `concorde_run` is still starting is left to that tool

### scenario.main-session.pi-owned-work — A `pi -p` session waits only for its own runs

- GIVEN a pi main session with the run view that started one run with `concorde_run` and one round with `concorde_task_session`, while another session's run and a run started with bash are running
- WHEN pi-subagents asks the run view for the session's background work, as `bg_wait` and `pi -p` do before the session ends
- THEN it lists the unfinished run and round the session started with its tools
- AND it lists neither the other session's run nor the run started with bash, which the view still shows and reports
- AND a finished run of the session is no longer listed

### scenario.main-session.project-terms — Every session starts with the project's terms

- GIVEN a project whose root Module declares a glossary that can be read
- WHEN the main agent's session or a task session, in Claude Code or pi, starts in one of its worktrees
- THEN the session holds every term of that worktree's glossary with its identity, owner and definition
- AND the guidance tells it to use each term exactly as defined, with the developer and in task goals, decision logs, escalations, commit messages and Specs
- BUT a project that declares no glossary, or whose declared glossary cannot be read, starts the session without terms and without an error

### scenario.main-session.change-through-task — The guidance routes an agreed change through a task

- GIVEN the rendered [main-session guidance](../../glossary.json#concept.main-session-guidance)
- WHEN a main agent reads how to carry out a change agreed with the developer
- THEN it is told to open a task with its own branch and worktree for the Modules involved
- AND to work inside that worktree, entering it in Claude Code and addressing its path in pi, and make the change there, directly or with Operations and the execution commands `task-validation` and `delivery` run in the background
- AND to run every `concorde` command that works on the task's workspace with the worktree's own copy
- AND that `concorde task open` bound the worktree as the task's workspace, whose binding every run reads without naming the task, and that a second run while one runs is refused with `workspace_busy`
- BUT it is told never to change Specs or code in the primary worktree

### scenario.main-session.parallel-tasks — The guidance allows parallel work only between worktrees

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to plan several changes
- THEN it is told to run tasks in parallel only in separate worktrees whose Modules and shared files do not overlap
- BUT to run tasks that write the same [Module](../../glossary.json#concept.module) or shared file one after another

### scenario.main-session.split-into-sessions — The guidance hands split work to task sessions

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to carry out work it split into several tasks
- THEN it is told to start one [task session](../../glossary.json#concept.task-session) per task on its own program: in Claude Code with `concorde task session` naming its own session, in pi with the `concorde_task_session` tool, answering a round with its `answer`
- AND to stay in the primary worktree while they run, being inside at most one task at a time itself
- AND to answer a task session's escalation or pass it to the developer with its own link on top

### scenario.main-session.task-session-role — The task-session guidance keeps a session within its task

- GIVEN the rendered Claude Code task-session guidance
- WHEN a Claude Code task session reads how to work
- THEN it is told to work only inside its task worktree with the worktree's own `concorde`
- AND to escalate beyond its task's goal or Modules with `concorde task escalate --by task-session` and SendMessage
- AND to report to the main agent when the task is delivered or cannot go further
- BUT never to merge the task branch or close the task

### scenario.main-session.pi-task-session-role — The pi task-session guidance ends each round with a report

- GIVEN the rendered pi task-session guidance
- WHEN a pi task session reads how to report
- THEN it is told to run Operations with the worktree's own `concorde` in the foreground
- AND to end every round by calling `concorde_report`, always supplying `status`, `summary`, `commit`, `escalations`, `decisions` and `open`, with the [delivery commit](../../glossary.json#concept.delivery-commit) and an empty escalation array when delivered, or after `concorde task escalate --by task-session` with a null commit and the unique escalation numbers
- AND that the main agent's answer arrives as the prompt of the next round
- BUT never to merge the task branch or close the task

### scenario.main-session.task-session-workflow — A task session runs its workflow in no-ask mode

- GIVEN the rendered Claude Code and pi task-session guidance
- WHEN a task session reads how to run a task that follows a known procedure
- THEN it is told to start the [workflow](../../glossary.json#concept.workflow) in its task worktree only in no-ask [mode](../../glossary.json#concept.workflow-mode), since nobody answers it at a [decision point](../../glossary.json#concept.decision-point)
- AND to read the [workflow result](../../glossary.json#concept.workflow-result) like a run result, copying its decisions and problems into the task's [decision log](../../glossary.json#concept.decision-log)
- AND to give the workflow's decisions in its own report to the main agent, naming those of major impact for the developer
- AND to escalate a workflow result that is not `ok` and that it cannot repair within the task with `concorde task escalate --by task-session` and the report as `--error-file`
- AND to escalate a decision of major impact the workflow took, which carries no error, with `concorde task escalate --by task-session` naming no run or file

### scenario.main-session.pi-task-session-view — pi shows task-session rounds and wakes on their end

- GIVEN a pi main session that started a task session with `concorde_task_session`
- WHEN the round's status file changes and the round ends
- THEN the run view shows the task, the round and the session's latest tool call
- AND the main agent is woken with the recorded outcome: the report's summary, decisions and open points with the delivery commit or the escalation numbers, or the failed round's [error chain](../../glossary.json#concept.error-chain)
- AND a pi main session that starts again follows the rounds still running

### scenario.main-session.merge-delivered — The guidance merges delivered work without asking

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do after `delivery` committed a task's change with its evidence
- THEN it is told to leave the task worktree if it is in it and merge the task with `concorde task merge <task>` without asking the developer
- AND never to merge with `git merge` itself, because other main sessions may be merging, and that the merge runs `concorde spec-validation` unless it names other checks
- AND to run the command again on `merge_busy`, and to resolve a `merge_conflict` in the task worktree and deliver again
- AND that the merge waits for the task's run and other merges itself, so that in Claude Code it runs in background Bash and in pi in bash without a timeout

### scenario.main-session.merge-interrupted — The guidance finishes an interrupted merge first

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do when a task command is refused with `merge_incomplete`
- THEN it is told to finish that merge before anything else with `concorde task merge <task> --resume`, without asking the developer
- AND to use `--abort` when the merge commit is no longer the primary branch's head or `--resume` answers `not_resumable`, and to bring `merge_diverged` to the developer
- AND to run `merge` or `close` again with a longer `--wait` on `workspace_busy`
- AND a task session is told to send a `merge_incomplete` or `merge_busy` refusal of its escalation to the main agent

### scenario.main-session.no-polling — Every wait wakes the agent or blocks once

- GIVEN the rendered main-session and task-session guidance
- WHEN an agent reads how to wait for a run, a busy workspace, a task session or a merge
- THEN it is told never to wait by polling with `sleep` loops
- AND to queue a run behind a running one with `--wait <seconds>`
- AND in pi without the run view to wait for a task-session round with `concorde task session <task> --wait`
- AND a task session is told to run long `concorde` commands in background Bash in Claude Code, and in pi in bash without a timeout

## Worker models

### scenario.main-session.choose-models — The guidance lets the developer choose worker models

- GIVEN the rendered main-session guidance
- WHEN a developer asks the main agent to change the models workers use
- THEN it is told that workers run on pi unless the tracked `.concorde/workers.json` chooses Claude Code for them, and take their models and limits from that file by [worker id](../../glossary.json#concept.worker-id), which a task carries from its base commit
- AND to edit the JSON directly, preserving unrelated overrides, since there is no editor
- AND to commit a change of that file alone directly on the primary branch for future tasks, never while a merge is unfinished
- AND that a task may change its own copy, which reaches the primary branch when the task merges
- AND that separate `scripts/available_models.py` discovery supplies advisory configured candidates without inference API probes, while custom/offline names require no discovery
- AND to set the JSON backend to `claude` when asked, with program installation required at launch rather than at configuration time
- BUT to change worker models only when the developer asks

### scenario.main-session.no-task-operations — The guidance runs questions and reviews without a task

- GIVEN the rendered main-session guidance
- WHEN a main agent needs to understand or review a Module without changing it
- THEN it is told that `understand`, `survey`, `spec_review`, `spec_panel` and `code_review` also run unbound, in a worktree without a [workspace binding](../../glossary.json#concept.workspace-binding) such as the primary worktree, with `workspace` null in their result
- AND that such a run examines an [unbound checkout](../../glossary.json#concept.unbound-checkout) of that worktree's `HEAD`, not its uncommitted changes, and names that commit as `commit` in its result
- AND that such a run changes no [Spec](../../glossary.json#concept.spec) or code, since it launches only reading workers
- BUT every change still runs in a task, and an `--input` of an unbound run must be unbound too

### scenario.main-session.brownfield — The guidance adopts existing code through the brownfield workflow

- GIVEN the rendered main-session guidance
- WHEN a main agent has just initialized a project whose code came before its Specs
- THEN it is told to open a task bound to the root Module and start the [brownfield workflow](../../glossary.json#concept.brownfield-workflow) inside its worktree, which never names the task
- AND to ask the developer for interactive or no-ask mode unless the developer already said
- AND to put every pending [decision point](../../glossary.json#concept.decision-point) to the developer when the workflow ends `awaiting_decision`, then start the workflow again with every answer given so far, keyed by each step's base key, its [step key](../../glossary.json#concept.step-key) without a restart label or answer digest
- AND to read the [workflow result](../../glossary.json#concept.workflow-result) saved beside the workspace's [workflow record](../../glossary.json#concept.workflow-record) like a run result, copy its decisions and problems into the task's [decision log](../../glossary.json#concept.decision-log) itself, and merge the delivered task

## Escalation

### scenario.main-session.ordinary-decision — The guidance decides ordinary questions and reports them

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle a run result blocked on a choice of ordinary scope, such as a name or an internal structure
- THEN it is told to decide, to record the decision and its reason in the task's decision log and to report it at the end
- BUT not to stop and ask the developer

### scenario.main-session.major-decision — The guidance escalates major decisions with their evidence

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle a result whose options would change what a Module promises to its users
- THEN it is told to ask the developer before acting
- AND to escalate with `concorde task escalate`, adding its own link on top of the error chain instead of replacing it with a summary

### scenario.main-session.read-error-chain — The guidance reads the whole error chain

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to handle a result that is not `ok`
- THEN it is told that the result carries an error chain in `error`, what each link holds, and to read the whole chain before deciding

### scenario.main-session.unbound-failure — The guidance brings a failed unbound run to the developer whole

- GIVEN the rendered main-session guidance
- AND an [unbound run](../../glossary.json#concept.unbound-run) of `spec_review` in the primary worktree that ended `failed`
- WHEN a main agent reads how to handle its result
- THEN it is told that the decision log and `concorde task escalate` cover the runs of a task, and that an unbound run belongs to none
- AND to show the developer the run's whole rendered error chain, never a summary of it
- AND when the failure leads to work, to open a task for that work and escalate in it with `--error-file .concorde/runs/<run-id>/result.json`, which records the run's chain under its own link
- BUT not to name the unbound run with `--run`, which names only runs of the task's own workspace

## Issues

### scenario.main-session.record-issue — The guidance records a deferred problem deliberately

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to retain a worker finding or Operation error that the current task will not fix
- THEN it is told to inspect `issues list` and `show` for existing open or closed matches before recording
- AND to decide whether to create an [Issue](../../glossary.json#concept.issue), append to an open one at its current revision, or reopen a closed one
- AND to run the writing command in a task worktree, with `--task` on `report`, and keep the receipt
- BUT it is told that neither the worker nor the Operation records the Issue automatically

This illustrates [recording decisions](requirements.md#req.main-session.issues-recording) and
[task-local writes](requirements.md#req.main-session.issues-worktree).

### scenario.main-session.solve-issue — The guidance solves Issues through tasks

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to solve an open Issue owned by a Module
- THEN it is told to open a task for that Module and run the Operations that fix the problem
- AND to close the Issue on the task branch with the evidence, so the closure is merged with the fix
- BUT starting or delivering the task does not itself close the Issue

This illustrates [ordinary repair](requirements.md#req.main-session.issues-by-operations) and
[closure with the fix](requirements.md#req.main-session.issues-close-with-fix).

### scenario.main-session.unmerged-issue — The guidance preserves an unmerged observation

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to end a task without merging its Issue records
- THEN it is told to carry worthwhile reports into a subsequent task or record a handoff in the task's decision log
- AND to preserve the identity, branch and commit when available, remaining work, report and evidence locations before worktree removal
- AND that committed records remain on the retained branch but are absent from the primary branch's Issue list
- BUT it is told that forced removal can discard uncommitted material and that a log entry does not publish an Issue

This illustrates [handoff before closure](requirements.md#req.main-session.issues-unmerged).

### scenario.main-session.issue-conflict — The guidance reconciles competing Issue histories

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to resolve a Git conflict in an Issue record
- THEN it is told to resolve it in the task worktree, preserving accepted reports and documenting the disposition decision with its evidence
- AND to run `issues check` explicitly before validation and delivery
- BUT it is told not to concatenate incompatible closes or invent reopenings to satisfy the state rules
- AND that a passing store check does not establish that the disposition is justified

This illustrates [conflict handling](requirements.md#req.main-session.issues-conflicts) and the
[store check](requirements.md#req.main-session.issues-store-check).
