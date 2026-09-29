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

### scenario.main-session.pi-task-worktree-missing — pi refuses a task without a worktree

- GIVEN a pi main session in the primary worktree and a task that has no record, or whose record names no existing worktree
- WHEN the main agent starts an Operation or an execution command of that task with the `concorde_run` tool
- THEN the tool is refused before anything starts, naming the task

### scenario.main-session.pi-run-view — pi shows every run and its worker's progress

- GIVEN a pi main session with the run view and an Operation run whose worker is in its second round
- WHEN the run view reads the [progress files](../../glossary.json#concept.progress-file) of the [run store](../../glossary.json#concept.run-store)
- THEN it shows the run with its workspace, Operation, step, the worker's round and latest tool call
- AND a worker of another run is not attributed to it, even when that run's runner recorded the same process identifier in another PID namespace

### scenario.main-session.pi-run-lock-file — pi tells a live run by its run lock file

- GIVEN a pi main session with the run view, a run of a task's workspace whose runner holds `.concorde/locks/runs/<run-id>.lock`, and a run without a result whose lock file is missing or held by nobody
- WHEN the run view refreshes
- THEN it shows the first running and the second `failed`, since its runner ended without a result
- AND a run `concorde_run` starts is started with `--detach`, its output kept in `host.out` of the run's node, and no `launch-*.log` is written

### scenario.main-session.pi-run-view-command — pi shows an execution command's run without a worker

- GIVEN a pi main session with the run view and a running `task-validation` run of the task `t1`
- WHEN the run view reads the run's [run progress file](../../glossary.json#concept.run-progress-file)
- THEN it shows the run as `t1 · task-validation` with its step, as it shows an Operation's run
- AND it pairs no worker with the run, even while an Operation's worker is running

### scenario.main-session.pi-run-view-unbound — pi shows an unbound run without a workspace

- GIVEN a pi main session with the run view and an [unbound run](../../glossary.json#concept.unbound-run) of `understand`
- WHEN the run view reads the run's run progress file
- THEN it shows the run as `unbound · understand`, with `unbound` in place of the workspace

### scenario.main-session.pi-run-finished — pi shows a finished run and wakes its owner

- GIVEN a pi main session with the run view and a run it started with `concorde_run` that has finished with the status `ok`, `blocked` or `failed`
- WHEN the run view reads its run progress file
- THEN it shows the run `completed`, `stopped` or `failed` respectively, with the result's summary
- AND the message the main agent is given names the run, its workspace and name, its status and summary, and its [run result](../../glossary.json#concept.run-result)'s file
- AND for a result that carries an [error chain](../../glossary.json#concept.error-chain) the message is followed by that whole chain, and for a result without one by none

### scenario.main-session.pi-run-lost — pi shows a run whose runner ended without finishing as failed

- GIVEN a pi main session with the run view and a run that has no result and whose runner ended without finishing, so that nobody holds its [run lock](../../glossary.json#concept.run-lock)
- WHEN the run view reads its run progress file
- THEN it shows the run `failed` and does not count it as running, even when the process identifier it recorded names a living process
- AND the message the main agent is given says that the runner ended without finishing the run
- BUT a run whose runner holds its run lock, or whose result has been written, is not taken for a lost one

### scenario.main-session.pi-run-discovered — pi follows runs it did not start

- GIVEN a pi main session with the run view, and runs of the project started before and after the session started, by a command run with bash or by another session
- WHEN the run view looks in the [run store](../../glossary.json#concept.run-store) for runs to follow
- THEN it follows every run still running when the session started and every run started since, even one that already ended, and shows them as it does the runs of `concorde_run`
- BUT it does not follow a run that had already ended before the session started, and leaves a run `concorde_run` started and is still waiting to be announced to that tool

### scenario.main-session.pi-wake-owner-only — pi wakes a session only for the runs it owns

- GIVEN a pi main session with the run view that started one run with `concorde_run`, while a run another main session started, a run a task session started and a run started with bash are running
- WHEN all four runs end
- THEN the run view shows each of them ended
- AND the main agent is woken once, with the result of the run it started
- AND it is not woken for the other three

### scenario.main-session.pi-owner-resumed — A resumed pi session keeps owning its runs

- GIVEN a pi main session that started a run with `concorde_run`, recorded in its session file, and was closed before the run ended
- WHEN the same session is resumed after the run ended
- THEN the run view wakes the main agent once with the run's result
- BUT a run whose end the session was already given, recorded in its session file too, does not wake it again, and a new session with another identity is woken for neither

### scenario.main-session.pi-owned-work — A `pi -p` session waits only for its own runs

- GIVEN a pi main session with the run view that started one run with `concorde_run` and one task session with `concorde_task_session`, while another session's run and a run started with bash are running
- WHEN pi-subagents asks the run view for the session's background work, as `bg_wait` and `pi -p` do before the session ends
- THEN it lists the unfinished run and round the session owns
- AND it lists neither the other session's run nor the run started with bash, which the view still shows
- AND a finished run of the session is no longer listed

### scenario.main-session.project-terms — Every session starts with the project's terms

- GIVEN a project whose root Module declares a glossary that can be read
- WHEN the main agent's session or a task session, in Claude Code or pi, starts in one of its worktrees
- THEN the session holds every term of that worktree's glossary with its identity, owner and definition
- AND the guidance tells it to use each term exactly as defined, with the developer and in task goals, decision logs, escalations, commit messages and Specs

### scenario.main-session.project-terms-missing — A session without a readable glossary starts without terms

- GIVEN a project whose root Module declares no glossary, or declares one that cannot be read
- WHEN the main agent's session or a task session, in Claude Code or pi, starts in one of its worktrees
- THEN the session starts without terms and without an error

### scenario.main-session.change-through-task — The guidance routes an agreed change through a task session

- GIVEN the rendered [main-session guidance](../../glossary.json#concept.main-session-guidance)
- WHEN a main agent reads how to carry out a change agreed with the developer
- THEN it is told to open a task with its own branch and worktree for the Modules involved and to hand it to a [task session](../../glossary.json#concept.task-session), even when it is the only task
- AND never to work inside a task worktree itself
- AND the task-session guidance tells the session to make the change inside that worktree, directly or with Operations and the execution commands `task-validation` and `delivery`, running every `concorde` command that works on the task's workspace with the worktree's own copy
- AND that `concorde task open` bound the worktree as the task's workspace, whose binding every run reads without naming the task, and that a second run while one runs is refused with `workspace_busy`
- BUT it is told never to change Specs or code in the primary worktree beyond a small change the developer approved

### scenario.main-session.small-change — The guidance makes a small change only with the developer's approval

- GIVEN the rendered main-session guidance
- WHEN a main agent reads whether it may fix a typo or a one-line defect directly in the primary worktree
- THEN it is told that such a small change may be made there only after it told the developer what it would change and why it is small, and the developer approved that specific change
- AND that without that approval the change runs in a task

### scenario.main-session.parallel-tasks — The guidance allows parallel work only between worktrees

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to plan several changes
- THEN it is told to run tasks in parallel only in separate worktrees whose Modules and shared files do not overlap
- BUT to run tasks that write the same [Module](../../glossary.json#concept.module) or shared file one after another

### scenario.main-session.split-into-sessions — The guidance hands every task to a task session

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to carry out the tasks it opened
- THEN it is told to start one [task session](../../glossary.json#concept.task-session) per task, even for a single task, on its own program: in Claude Code with `concorde task session` naming its own session, in pi with the `concorde_task_session` tool, answering a round with its `answer`
- AND to record the task's brief in its [decision log](../../glossary.json#concept.decision-log) before starting the session
- AND to stay in the primary worktree
- AND to answer a task session's escalation or pass it to the developer with its own link on top

### scenario.main-session.batched-decisions — Decisions travel up together and come back together

- GIVEN the rendered main-session and task-session guidance
- WHEN a task session meets decisions its task needs that are not its own
- THEN it is told not to wait in the middle of its work, but to carry on with what does not depend on them and then escalate all of them together in one report
- AND the main agent is told to decide those its authority covers, to put all the others to the developer at once and to answer the session once with every answer

### scenario.main-session.task-session-role — The task-session guidance keeps a session within its task

- GIVEN the rendered Claude Code task-session guidance
- WHEN a Claude Code task session reads how to work
- THEN it is told to read the task's decision log first and to work only inside its task worktree with the worktree's own `concorde`
- AND to escalate beyond its task's goal or Modules with `concorde task escalate --by task-session`, recording every escalation first and then sending them together with SendMessage
- AND to report to the main agent when the task is delivered or cannot go further without decisions that are not its own
- BUT never to merge the task branch into the primary branch or close the task

### scenario.main-session.pi-task-session-role — The pi task-session guidance ends each round with a report

- GIVEN the rendered pi task-session guidance
- WHEN a pi task session reads how to report
- THEN it is told to run Operations with the worktree's own `concorde` in the foreground
- AND to end every round by calling `concorde_report`, always supplying `status`, `summary`, `commit`, `escalations`, `decisions` and `open`, with the [delivery commit](../../glossary.json#concept.delivery-commit) and an empty escalation array when delivered, or after recording every escalation it needs with `concorde task escalate --by task-session` with a null commit and all their unique numbers
- AND that the main agent's answer arrives as the prompt of the next round
- BUT never to merge the task branch into the primary branch or close the task

### scenario.main-session.task-session-workflow — A task session runs its workflow in its brief's mode

- GIVEN the rendered Claude Code and pi task-session guidance
- WHEN a task session reads how to run a task that follows a known procedure
- THEN it is told to start the [workflow](../../glossary.json#concept.workflow) in its task worktree in the [mode](../../glossary.json#concept.workflow-mode) its brief names, interactive when it names none
- AND to escalate every pending [decision point](../../glossary.json#concept.decision-point) of a workflow that ended `awaiting_decision` at once, with the report as `--error-file`, and to start the same workflow again with every answer given so far
- AND to read the [workflow result](../../glossary.json#concept.workflow-result) like a run result, copying its decisions and problems into the task's [decision log](../../glossary.json#concept.decision-log)
- AND to give the workflow's decisions in its own report to the main agent, naming those of major impact for the developer
- AND to escalate a workflow result that is not `ok` and that it cannot repair within the task with `concorde task escalate --by task-session` and the report as `--error-file`
- AND to escalate a decision of major impact a no-ask workflow took, which carries no error, with `concorde task escalate --by task-session` naming no run or file

### scenario.main-session.pi-task-session-view — pi shows task-session rounds and wakes on their end

- GIVEN a pi main session that started a task session with `concorde_task_session`
- WHEN the round's status file changes while the round runs
- THEN the run view shows the task, the round and the session's latest tool call
- AND a pi main session that starts again follows the rounds still running, from their status files

### scenario.main-session.pi-task-session-wake — pi wakes the main agent with a round's recorded outcome

- GIVEN a pi main session following a round of a task session it started
- WHEN the round ends and its outcome is recorded in the round's [trace node](../../glossary.json#concept.trace-node)
- THEN the run view shows the round finished with its outcome
- AND the main agent is woken with the recorded outcome: the report's summary, decisions and open points with the delivery commit or the escalation numbers, or the failed round's [error chain](../../glossary.json#concept.error-chain)

### scenario.main-session.pi-round-owner — The rounds of a task session wake the session it was started for

- GIVEN two pi main sessions of one project, the first of which started a task session with `concorde_task_session`, so that the session's [trace node](../../glossary.json#concept.trace-node) names it as its `main`
- WHEN the second answers the task session's round and the next round ends
- THEN both show the round, and only the first is woken with its outcome
- AND the second's tool result names the first as the owner that alone will be woken
- AND a round of a task session started without `--main` wakes neither

### scenario.main-session.claude-sees-by-query — A Claude Code main session sees another session's work by asking

- GIVEN a Claude Code main session and another main session of the same project that owns a run of the task `t1` or a round of its task session
- WHEN that run or round ends
- THEN the Claude Code main session is not woken, since nothing is pushed into it
- AND `concorde task show t1`, when it asks, lists the run with its status and the task session with its `main` and the round's outcome

### scenario.main-session.merge-delivered — The guidance merges delivered work without asking

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do after `delivery` committed a task's change with its evidence
- THEN it is told to merge the task with `concorde task merge <task>` from the primary worktree without asking the developer
- AND never to merge with `git merge` itself, because other main sessions may be merging, and that the merge runs `concorde spec-validation` unless it names other checks
- AND to run the command again on `merge_busy`
- AND that the merge waits for the task's run and other merges itself, so that in Claude Code it runs in background Bash and in pi in bash without a timeout

### scenario.main-session.merge-conflict — A merge conflict goes back to the task session

- GIVEN the rendered main-session and task-session guidance
- WHEN merging a delivered task fails with `merge_conflict`
- THEN the main agent is told to answer the task's session, starting one again if it has ended, to merge the primary branch into its task branch, resolve the conflicts, run `task-validation` and `delivery` again and report
- AND the task session is told to make that merge in its task worktree and that it is the only merge it makes

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
- THEN it is told to open a task bound to the root Module and have its task session run the [brownfield workflow](../../glossary.json#concept.brownfield-workflow) inside its worktree, which never names the task
- AND to ask the developer for interactive or no-ask mode unless the developer already said, and to name it in the task's brief
- AND when the task session escalates the pending [decision points](../../glossary.json#concept.decision-point) of a workflow that ended `awaiting_decision`, to decide those its authority covers, put the rest to the developer at once and answer the session with every answer, with which it starts the workflow again
- AND to read the [workflow result](../../glossary.json#concept.workflow-result) saved beside the workspace's [workflow record](../../glossary.json#concept.workflow-record) like a run result, whose decisions and problems the task session copies into the task's [decision log](../../glossary.json#concept.decision-log), and merge the delivered task

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
- AND when the failure leads to work, to open a task for that work and escalate in it with `--error-file .concorde/unbound/<run-id>/result.json`, which records the run's chain under its own link
- BUT not to name the unbound run with `--run`, which names only runs of the task's own workspace

## Issues

### scenario.main-session.record-issue — The guidance records a deferred problem deliberately

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to retain a worker finding or Operation error that the current task will not fix
- THEN it is told to inspect `issues list` and `show` for existing open or closed matches before recording
- AND to decide whether to create an [Issue](../../glossary.json#concept.issue), append to an open one at its current revision, or reopen a closed one
- AND to have the writing command run in a task worktree by the task's session, with `--task` on `report`, and keep the receipt
- BUT it is told that neither the worker nor the Operation records the Issue automatically

This illustrates [recording decisions](requirements.md#req.main-session.issues-recording) and
[task-local writes](requirements.md#req.main-session.issues-worktree).

### scenario.main-session.solve-issue — The guidance solves Issues through tasks

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to solve an open Issue owned by a Module
- THEN it is told to open a task for that Module whose session runs the Operations that fix the problem
- AND to have the Issue closed on the task branch with the evidence, so the closure is merged with the fix
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
- THEN it is told that the task's session resolves it in the task worktree, and to tell it to preserve accepted reports and document the disposition decision with its evidence
- AND to run `issues check` explicitly before validation and delivery
- BUT not to concatenate incompatible closes or invent reopenings to satisfy the state rules
- AND that a passing store check does not establish that the disposition is justified

This illustrates [conflict handling](requirements.md#req.main-session.issues-conflicts) and the
[store check](requirements.md#req.main-session.issues-store-check).
