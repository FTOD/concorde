# Main session scenarios

Situations the [main-session guidance](module.md) prepares the
[main agent](../../glossary.json#concept.main-agent) for, and what holds for the sessions it
guides.

## Working method

### scenario.main-session.project-terms — Every session starts with the project's terms

- GIVEN a project whose root Module declares a glossary that can be read, with Concorde installed
- WHEN the main agent's session or a task session starts in one of its worktrees
- THEN the Concorde block of that worktree's `CLAUDE.md` imports the glossary, so Claude Code loads every term with its identity, owner and definition at launch
- AND the rest of `CLAUDE.md` is kept

### scenario.main-session.project-terms-missing — A session without a declared glossary starts without terms

- GIVEN a project whose root Module declares no glossary yet, with Concorde installed
- WHEN the main agent's session or a task session starts in one of its worktrees
- THEN the Concorde block of `CLAUDE.md` imports no glossary, and the session starts without terms and without an error

### scenario.main-session.change-through-task — The guidance routes an agreed change through a task session

- GIVEN the rendered [main-session guidance](../../glossary.json#concept.main-session-guidance)
- WHEN a main agent reads how to carry out a change agreed with the developer
- THEN it is told to open a task with its own branch and worktree for the Modules involved and to hand it to a [task session](../../glossary.json#concept.task-session), even when it is the only task
- AND never to work inside a task worktree itself
- AND the task-session guidance tells the session to make the change inside that worktree, directly or with [Operations](../../glossary.json#concept.operation) and the [execution commands](../../glossary.json#concept.execution-command) `task-validation` and `delivery`, running every `concorde` command that works on the task's workspace with the worktree's own copy
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
- THEN it is told to start one [task session](../../glossary.json#concept.task-session) per task, even for a single task, as a background Claude Code session with `concorde task session` naming its own session with `--main`
- AND to record the task's brief in its [decision log](../../glossary.json#concept.decision-log) before starting the session
- AND to stay in the primary worktree
- AND to answer a task session's escalation or pass it to the developer with its own link on top

### scenario.main-session.batched-decisions — Decisions travel up together and come back together

- GIVEN the rendered main-session and task-session guidance
- WHEN a task session meets decisions its task needs that are not its own
- THEN it is told not to wait in the middle of its work, but to carry on with what does not depend on them and then escalate all of them together in one report
- AND the main agent is told to decide those its authority covers, to put all the others to the developer at once and to answer the session once with every answer

### scenario.main-session.task-session-role — The task-session guidance keeps a session within its task

- GIVEN the rendered task-session guidance
- WHEN a task session reads how to work
- THEN it is told to read the task's decision log first and to work only inside its task worktree with the worktree's own `concorde`
- AND to escalate beyond its task's goal or Modules with `concorde task escalate --by task-session`, recording every escalation first and then sending them together with SendMessage
- AND to report to the main agent when the task is delivered or cannot go further without decisions that are not its own
- BUT never to merge the task branch into the primary branch or close the task

### scenario.main-session.task-session-prepares-workers — The task session creates and binds new files before a worker fills them

- GIVEN the rendered task-session guidance and the main agent's skill
- WHEN a task's work needs a new file outside the directories its Modules bind, such as one an `understand` plan lists in `new_files`
- THEN the task-session guidance tells the session to create the file with the least content its format needs to be valid, to add it to the `entries` of the right realization and to commit both together, before it launches the worker that fills it
- AND the main agent's skill says the task session prepares the workers' environment this way
- AND both name the [delivery commit](../../glossary.json#concept.delivery-commit) as what `delivery` creates, the only commit that marks the task delivered

### scenario.main-session.task-session-workflow — A task session runs its workflow in its brief's mode

- GIVEN the rendered task-session guidance
- WHEN a task session reads how to run a task that follows a known procedure
- THEN it is told to start the [workflow](../../glossary.json#concept.workflow) in its task worktree in the [mode](../../glossary.json#concept.workflow-mode) its brief names, interactive when it names none
- AND to escalate every pending [decision point](../../glossary.json#concept.decision-point) of a workflow that ended `awaiting_decision` at once, with the report as `--error-file`, and to start the same workflow again with every answer given so far
- AND to read the [workflow result](../../glossary.json#concept.workflow-result) like a [run result](../../glossary.json#concept.run-result), copying its decisions and problems into the task's [decision log](../../glossary.json#concept.decision-log)
- AND to give the workflow's decisions in its own report to the main agent, naming those of major impact for the developer
- AND to escalate a workflow result that is not `ok` and that it cannot repair within the task with `concorde task escalate --by task-session` and the report as `--error-file`
- AND to escalate a decision of major impact a no-ask workflow took, which carries no error, with `concorde task escalate --by task-session` naming no run or file

### scenario.main-session.claude-sees-by-query — A main session sees another session's work by asking

- GIVEN two main sessions of the same project, the second of which started a run of the task `t1` in background Bash and a task session of `t1` naming itself with `--main`, while the first registered no wait for that run
- WHEN that run ends
- THEN the first main session is not woken, since nothing it did not ask for is pushed into it
- AND `concorde task show t1`, when it asks, lists the run with its status and the task session with the main session it reports to

### scenario.main-session.merge-delivered — The guidance merges delivered work without asking

- GIVEN the rendered main-session guidance
- WHEN a main agent reads what to do after `delivery` committed a task's change
- THEN it is told to merge the task from the primary worktree without asking the developer, with the project MCP server's `task_merge` or with `concorde task merge <task>` in background Bash
- AND never to merge with `git merge` itself, because other main sessions may be merging, and that the merge runs `concorde spec-validation` unless it names other checks

### scenario.main-session.merge-command — The guidance runs the merge command in the background

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to merge a delivered task with `concorde task merge <task>`
- THEN it is told that the command waits up to `--wait` seconds for the task's run and for other merges, so that it runs in background Bash
- AND to run the command again on `merge_busy`
- AND to run `merge` or `close` again with a longer `--wait` on `workspace_busy`

### scenario.main-session.merge-through-server — The guidance retries a busy `task_merge` after a registered wait

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to merge a delivered task with the project MCP server's `task_merge`
- THEN it is told that `task_merge` never waits for a lock: it returns at once with the merge it started, or is refused at once with `workspace_busy` or `merge_busy` naming the holder
- AND on such a refusal to register a wait for the busy lock with `register_wait`, or to run the `concorde task wait` command it returns in background Bash without a channel, and to call `task_merge` again once woken, which may be refused again

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
- AND a task session is told to send a `merge_incomplete` or `merge_busy` refusal of its escalation to the main agent

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
- THEN it is told that workers run on pi unless the tracked `.concorde/workers.json` chooses Claude Code for them, and take their models and limits from that file by [worker id](../../glossary.json#concept.worker-id), which a task carries from its base commit
- AND to edit the JSON directly, preserving unrelated overrides, since there is no editor
- AND to commit a change of that file alone directly on the primary branch for future tasks, never while a merge is unfinished
- AND that a task may change its own copy, which reaches the primary branch when the task merges
- AND that separate `scripts/available_models.py` discovery supplies advisory configured candidates without inference API probes, while custom/offline names require no discovery
- AND to set the JSON backend to `claude` when asked, with program installation required at launch rather than at configuration time, an entry that only chooses a backend keeping the model and level it inherits
- BUT to change worker models only when the developer asks

### scenario.main-session.worker-configuration-required — The guidance runs workers only on the configured models

- GIVEN the rendered main-session guidance
- WHEN a main agent is about to run an Operation in a project
- THEN it is told that every worker runs only on what the tracked `.concorde/workers.json` enables and chooses, never on anyone's own pi or Claude Code settings, and that only credentials and provider definitions come from those
- AND that no worker runs without the file, which the installer does not write, so when the project has none it asks the developer for the enabled models and the default, writes the file and commits it alone on the primary branch before any Operation runs
- AND that the file's required `enabled_models` lists every model an entry may name by its project model name, each with an optional level of its own, that a model outside it is refused with `model_not_enabled` and a worker without a model with `model_unresolved`
- AND that the developer's untracked [model map](../../glossary.json#concept.model-map) gives each project model name its local id per program, that a worker it cannot resolve is refused with `model_unmapped`, `model_map_missing` or `model_map_invalid`, and that the main agent changes the map only when the developer asks or agrees, telling the developer the entry a new model needs
- AND which level a worker takes: its model's entry's or a more specific one's, otherwise the model's own, otherwise a less specific entry's, otherwise its program's built-in default
- BUT a model the developer adds for a worker goes into `enabled_models` too

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
- AND to escalate with `concorde task escalate`, adding its own link on top of the [error chain](../../glossary.json#concept.error-chain) instead of replacing it with a summary

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

## The project MCP server

### scenario.main-session.project-mcp-session — The server declares its tools and the channel capability

- GIVEN a Claude Code session that starts the [project MCP server](../../glossary.json#concept.project-mcp-server), `concorde project-mcp`
- WHEN it initializes the session and lists the tools
- THEN the server answers with a protocol version it supports, the tools capability and the experimental `claude/channel` capability
- AND it lists `task_list`, `task_show`, `trace_show`, `run_result`, `workflow_report`, `locks`, `task_open`, `task_escalate`, `task_close`, `task_merge` and `register_wait`

### scenario.main-session.project-mcp-queries — Queries answer the project from any worktree

- GIVEN a project with an open task `t1`, and a server started in the task's worktree
- AND no process holds the merge lock or the workspace lock of `t1` while the calls run
- WHEN the session calls `task_list`, `task_show`, `trace_show` and `locks`
- THEN each answers from the primary worktree's records as `concorde task list`, `task show` and `trace show` do, and `locks` says that nobody holds the merge lock or the workspace lock of `t1`

### scenario.main-session.project-mcp-refusals — Refusals are error links

- GIVEN a running server
- WHEN a call names an unknown task, lacks a required argument or names no tool of the server
- THEN each is refused with an error link: Tasks' own `unknown_task` link for the unknown task, and the server's own `invalid_input` link otherwise

### scenario.main-session.project-mcp-short-writes — Short writes take structured arguments

- GIVEN a running server
- WHEN the session opens a task with `task_open`, escalates in it with `task_escalate` as a task session with two options, and closes it with `task_close` as completed with a note
- THEN the task is opened, the escalation is recorded as number 1 with the level `task-session`, and the task ends closed, each as the matching `concorde task` command does

### scenario.main-session.project-mcp-lock-busy — A busy lock is refused at once, naming its holder

- GIVEN a delivered task `t1` whose workspace lock another session's process holds for task `t1`
- WHEN the session calls `task_merge` for `t1`
- THEN the call is refused at once with `workspace_busy`, whose detail names the other session and the task and whose evidence carries the holder line with its process
- AND once that lock is free but another process holds the merge lock, `task_merge` is refused with `merge_busy` naming that holder, and the workspace lock it had taken is free again
- AND the task is still delivered

### scenario.main-session.project-mcp-lock-handover — The merge process owns the locks it was granted

- GIVEN a delivered task `t1` and a merge check that waits for a signal
- WHEN the session calls `task_merge` for `t1` and the check has started
- THEN the holder lines of the [merge lock](../../glossary.json#concept.merge-lock) and the task's [workspace lock](../../glossary.json#concept.workspace-lock) name the merge process, the session and the task, the merge process has both lock files open and the server has neither
- AND when the server is killed the locks stay held, and once the check ends the merge closes the task and releases both

### scenario.main-session.project-mcp-merge-wakes — The end of a merge wakes the session

- GIVEN a server whose session listens to it as a channel, and a delivered task
- WHEN the session calls `task_merge` and the merge succeeds
- THEN the answer says the session will be woken, and a `merge_ended` event with exit code 0 arrives whose content carries the merge's output

### scenario.main-session.project-mcp-wait-channel — A registered wait wakes the session

- GIVEN a server whose session listens to it as a channel, and an open task whose workspace lock another process holds
- WHEN the session registers a wait for that lock and the holder dies
- THEN a `wait_done` event for the lock arrives naming the holder it waited for
- AND a wait registered for the task becoming delivered is woken by a `wait_done` event once a delivery made under the workspace lock releases it
- AND registering the same wait again answers at once that the task is delivered and registers nothing

### scenario.main-session.project-mcp-wait-fallback — Without a channel the wait names its command

- GIVEN a server whose session does not listen to it as a channel, and a held workspace lock of task `t1`
- WHEN the session registers a wait for that lock, or for `t1` becoming closed or failed
- THEN nothing is registered, the answer says there is no channel, and it returns `concorde task wait t1 --lock workspace` or `concorde task wait t1 --until closed,failed` to run in background Bash

### scenario.main-session.project-mcp-channel-detection — The server reads its channel from the session's command line

- GIVEN the command lines of the server's ancestor processes
- WHEN one is a `claude` on a terminal started with `--dangerously-load-development-channels server:concorde` or with `server:concorde` among the entries of `--channels`
- THEN the server knows it has a channel
- BUT the same command line of a `claude` without a terminal, a background session, does not give it one, nor does `server:concorde` as the value of another option or another server's entry
- AND `CONCORDE_CHANNEL` `0` or `1` decides instead when it is set

### scenario.main-session.project-mcp-guidance — The guidance says how to start with the server and when to use it

- GIVEN the rendered main-session guidance
- WHEN a main agent reads how to merge a task and how to wait for a task, run or lock
- THEN it is told to start its session with `--dangerously-load-development-channels server:concorde`, to use `task_merge` and `register_wait`, and, without a channel, to run the `concorde task wait` command they return in background Bash
- AND that a woken session is never handed a lock and asks again, and that the `concorde` commands stay the source of truth
- AND the task-session guidance tells a task session that, as a background session, it is never woken by channel events and waits with `concorde task wait` in background Bash
