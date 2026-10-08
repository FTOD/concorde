# End-to-end testing

## Purpose

End-to-end testing is how the Concorde project tests itself on real codebases with real agents.
It takes a project from the Python repositories SWE-bench draws from.
It sets the project up exactly as a user would.
It runs a workflow in the project with real workers.
It lets the developer watch every run.
It exists for the people developing Concorde.
Nothing of it is installed into a project.
A Concorde user never meets it.
Its second job separates problems caused only by testing conditions from problems users would
meet, so that the first are solved here.
They are not solved in what users get.
Testing conditions include a headless main session or an untrusted scratch project.

End-to-end runs are not in the test suite. They have these properties:

- They clone from the network.
- They spend real model tokens.
- They take tens of minutes.
- Their outcome depends on the model.

The suite keeps the deterministic acceptance test.
That test runs the same workflow with fake workers.
After a change to the following, the developer runs this Module by hand:

- Adoption.
- Workflows.
- The worker harness.

Its findings become ordinary tasks.

## Core concepts

<a id="concept.test-project"></a>

**[Test project](../glossary.json#concept.test-project).** A test project is a real codebase set up
the way a user's project is set up. It has these properties:

- Its repository is one SWE-bench names, or another that `--any` admits.
- It is fetched at a pinned revision into the **end-to-end root**.
- The Concorde of this checkout is installed and initialized in it.
- A [worker configuration](../glossary.json#concept.worker-configuration) is written in it.
- A task is open, bound to the root [Module](../glossary.json#concept.module).

When `CONCORDE_E2E_ROOT` is set, it names the end-to-end root.
Otherwise, the root is `concorde-e2e` in the system's temporary directory, wherever that directory
lies.
On Linux, this is `/tmp/concorde-e2e`.
Each test project is the directory `test-<name>` directly there.
`<name>` is the repository's name or the one `--name` gives.
A `<name>` must be one directory name: not empty, not `.` or `..`, and without `/`.
So no test project lies outside the end-to-end root.
A test project is its own repository, so its workers run in its own `.claude/worktrees/`.
Wherever its Git metadata lies, the Harness hides it from them.
Since Claude Code loads every `CLAUDE.md` above a session's working directory, the tool refuses a
root inside this checkout.
This applies to the default or `CONCORDE_E2E_ROOT`.
Each session of a test project there would receive Concorde's own development instructions.
Test projects are throwaway. The developer reads these:

- A test project's [Specs](../glossary.json#concept.spec).
- Its runs.
- Its records.

When the test is done, the developer removes its directory, or prepares the next one under another
name.

**Headless run and driver run.** A test project runs a workflow in one of two ways.
The two ways answer different questions. A **headless run** is what a user's task session does.
A real [headless session](../glossary.json#concept.headless-session) runs the installed workflow.
This includes Claude Code's workflow runtime and its [step agents](../glossary.json#concept.step-agent).
A **driver run** removes the session's model and Claude Code's workflow runtime from between the
steps. Its [Operations](../glossary.json#concept.operation) still launch real workers, so a failure
there lies on Concorde's side. The failure is in one of these:

- Its commands.
- Its Operations.
- Its workers.

**Testing conditions.** A user's main session is interactive and its project trusted.
A test runs headless in a scratch project, so two things differ:

- `claude -p` stops a background workflow after ten idle minutes.
- An untrusted project ignores its allow rules.

Together with its child [Headless sessions](sessions/module.md), this Module handles both for tests.
It changes nothing a user gets.

## Overview

### Children and providers

Three children carry parts of End-to-end testing:

- [Headless sessions](sessions/module.md) drives any real headless Claude Code main session.
- [SWE-bench cases](cases/module.md) repairs and grades cases worked on real issues.
- [Dogfood scenarios](dogfood/module.md) tests a
  [develop install](../glossary.json#concept.develop-install)'s
  [main agent](../glossary.json#concept.main-agent) against a known
  [Concorde defect](../glossary.json#concept.concorde-defect).

Each reaches a different part of Concorde:

- A headless session wakes on the runs of Execution.
- A case is set up through Distribution.
- A dogfood scenario drives headless sessions against a develop install that Dogfooding describes.

The parent itself sets test projects up through Distribution's installer and `concorde` command.
Spec core's initialization carries out its `init`.
Tasks carries out its `task open`.
With Workers, the parent checks their worker configuration.
The check covers every worker the Operations' catalog lists.
The parent runs the workflows of Workflows in the workspaces Execution runs.
With the owners case, it checks Main session's promise about who a run wakes ([Around it](#around-it)).

```d2
e2e: End-to-end testing {
  sessions: Headless sessions
  cases: SWE-bench cases
  dogfood: Dogfood scenarios
  dogfood -> sessions
}
execution: Execution
distribution: Distribution
dogfooding: Dogfooding
workflows: Workflows
spec: Spec core
tasks: Tasks
workers: Workers
operations: Operations
main_session: Main session
e2e -> workflows
e2e -> execution
e2e -> distribution
e2e -> spec
e2e -> tasks
e2e -> workers
e2e -> operations
e2e -> main_session
e2e.sessions -> execution
e2e.cases -> distribution
e2e.dogfood -> distribution
e2e.dogfood -> dogfooding
```

### A test project from preparation to removal

The developer handles a test project in these steps:

- Prepare the test project.
- Run a workflow in it, headless or through the driver.
- Watch its runs while it runs or afterwards.

Every step is one command of the end-to-end tool, described under [The commands](#the-commands).
The two kinds of run differ only in what sits between the
[workflow steps](../glossary.json#concept.workflow-step).
Both execute the real `concorde workflow step` command lines in the task's worktree.
Both reach real workers.

```d2 illustrative
direction: down
developer: Developer {shape: person}
tool: "End-to-end tool" {
  prepare: "prepare: fetch the revision, install,\ninit, worker configuration,\ncommit, open the task"
  run: "run" {shape: diamond}
  watch: "watch: runs and\nworkflow steps"
}
headless: "Headless run (--via claude)" {
  session: "Headless session in the\ntask worktree, as its task session"
  runtime: "Claude Code's workflow runtime\nand step agents"
}
driver: "Driver run (--via driver)" {
  script: "Rendered workflow script under\nthe Workflows tests' stand-in runtime"
  agents: "Step agents without a model"
}
project: "Test project" {
  wstep: "concorde workflow step\nin the task's workspace"
  workers: "Operations with real workers"
  result: "Workflow result in\nthe workflow record"
}
developer -> tool.prepare
tool.prepare -> tool.run
tool.run -> headless.session: headless
tool.run -> driver.script: driver
headless.session -> headless.runtime
headless.runtime -> project.wstep
driver.script -> driver.agents
driver.agents -> project.wstep
project.wstep -> project.workers
project.workers -> project.result
project.result -> tool.run: "printed" {style.stroke-dash: 3}
project.result -> tool.watch: "read" {style.stroke-dash: 3}
developer -> tool.watch
```

## The commands

The tool is one command of this checkout, `scripts/e2e/e2e.py`.
Each command prints one JSON object.
On failure, it prints `{"error": …}` with the failed command and its output instead.
Its exit statuses are:

- 0 when it prints its result.
- 1 when it prints `{"error": …}`.
- 2 for a malformed command line, such as a `--restart` that is not `<key>=<label>`, or a
  `session start` without exactly one of `--prompt` and `--prompt-file`.

Exit status 0 also covers these results, since they are the test's findings:

- A workflow result whose status is not `ok`.
- An owners case that ended `failed`.

For a malformed command line, the tool prints its usage to standard error.
For that command line, it does nothing.
When no step names a code for a failure, the tool prints it as an error too, never as a traceback.
For a command it cannot start at all, it prints `command_failed`, naming the command, its working
directory and the operating system's refusal.
This holds for every command it starts, a setup step's, the driver's `node` and the owners case's
own launch alike.
For anything else it did not foresee, it prints `unexpected_error` with the traceback beside its
detail. The commands are:

```text
python3 scripts/e2e/e2e.py repos
python3 scripts/e2e/e2e.py prepare <owner/name> --rev <tag|branch|commit> [--name <dir>] [--python <interpreter>] [--task <task>] [--any] [--worker-model <model>]
python3 scripts/e2e/e2e.py trust <project>…
python3 scripts/e2e/e2e.py run <project> [--via claude|driver] [--workflow brownfield] [--task <task>] [--module <id>] [--mode no-ask|interactive] [--retry <key>]… [--restart <key>=<label>]…
python3 scripts/e2e/e2e.py watch <project>
python3 scripts/e2e/e2e.py owners <project> [--task t1] [--claude 2] [--claude-model <model>] [--wake 180] [--grace 20]
```

Its children add these commands:

- `session` ([Headless sessions](sessions/module.md)).
- `repair-specs` and `grade` ([SWE-bench cases](cases/module.md)).
- `dogfood` ([Dogfood scenarios](dogfood/module.md)).

**A worked example.** The developer prepares `psf/requests` at its tag `v2.31.0`.
The developer runs the [brownfield workflow](../glossary.json#concept.brownfield-workflow) in it as
a headless run.
From another terminal while it runs or afterwards, the developer watches its runs.
Shortened, the three commands print:

```text
$ python3 scripts/e2e/e2e.py prepare psf/requests --rev v2.31.0
{"project": "/tmp/concorde-e2e/test-requests", "repository": "psf/requests", "revision": "v2.31.0",
 "task": "adopt", "worktree": "/tmp/concorde-e2e/test-requests/.claude/worktrees/adopt"}

$ python3 scripts/e2e/e2e.py run /tmp/concorde-e2e/test-requests --via claude
{"workflow": "brownfield", "workspace": "adopt", "mode": "no-ask", "status": "ok",
 "steps": [{"key": "survey", "status": "ok", …}, {"key": "scaffold", …}, …,
           {"key": "delivery", "status": "ok", …}],
 "decisions": […], "open_questions": […], "problems": […], …}

$ python3 scripts/e2e/e2e.py watch /tmp/concorde-e2e/test-requests
{"runs": [{"run": "r-…-survey-…", "workspace": "adopt", "phase": "finished", "status": "ok", …}, …],
 "workflows": {"adopt": [{"key": "survey", "run": "r-…-survey-…", "superseded": false}, …]}}
```

The project is then a throwaway. The developer reads these:

- Its Specs.
- Its runs.
- Its records.

The developer removes the directory, or prepares the next one under another `--name`.

The [owners case](#owners-case) plays its runs on a task of its own, `t1` by default.
So the developer prepares a project for it with that task and then runs it there:

```text
$ python3 scripts/e2e/e2e.py prepare psf/requests --rev v2.31.0 --name owners --task t1
{"project": "/tmp/concorde-e2e/test-owners", "task": "t1", …}

$ python3 scripts/e2e/e2e.py owners /tmp/concorde-e2e/test-owners
{"task": "t1", "status": "passed",
 "phases": [{"phase": "unowned", "owner": null, …}, {"phase": "owned-by-claude", "owner": "claude-1", …}],
 "problems": []}
```

### Preparing a test project

`repos` lists the repositories SWE-bench's harness names, read from the vendored
`references/swe-bench/`.
`prepare psf/requests --rev v2.31.0` makes a test project through these steps:

- Fetch that revision without earlier commits into the end-to-end root, under `--name` or the
  repository's name.
- Check it out as a `main` branch.
- Install Concorde from this checkout without `d2`.
- Initialize it.
- Write its worker configuration.
- Commit.
- Open a task bound to the root Module.

The revision is one of these:

- A tag.
- A branch.
- A commit.

The task is `--task` (default `adopt`).

Before anything else, the tool resolves the end-to-end root to an absolute path.
So a relative `CONCORDE_E2E_ROOT` names the same directory for every command `prepare` runs,
whichever directory that command runs in.

It initializes the project as a user does, in the two steps of Spec core's
[initialization](../spec-tooling/spec/contracts.md#initialization):

- `concorde init --propose` with the project directory's name.
  When `--python` is given, this step also uses `--python <interpreter>`.
- `concorde init --apply` of that proposal.

Initialization creates the root Module, `module.project`.
It records the interpreter in the project configuration, where the project's
[configured checks](../glossary.json#concept.configured-check) take it for `{python}`.
`prepare` writes neither itself.

When `--worker-model` is given, the [worker configuration](../glossary.json#concept.worker-configuration)
runs every worker on that project model name.
It enables only that model.
Otherwise, it takes this checkout's own `.concorde/workers.json` without its `runtime` paths,
which name this checkout's directories.
The test project's sessions and workers run in the developer's own environment.
So the developer's [model map](../glossary.json#concept.model-map) resolves its models as it does
the developer's own projects'.
No map is written for it.
First, `prepare` loads the Operations this checkout's parts register, as the `concorde` command
loads them.
Before anything is cloned, `prepare` hands the configuration it built to Workers' check of a
configuration.
That check validates it.
Through that map, the check resolves the model of every worker of every Operation the
[Operation catalog](../glossary.json#concept.operation-catalog) lists.
`prepare` enumerates no worker itself.
It passes Workers' refusal on with its code ([Around it](#uses-workers)).

Before anything is cloned, `prepare` refuses each of these:

- An end-to-end root inside this checkout, with `root_inside_checkout`
  ([Test project](#core-concepts)).
- Unless `--any` is given, a repository SWE-bench does not name, with `unknown_repository` naming
  the known ones.
- Without `--worker-model`, this checkout's own worker configuration when it cannot be read as a JSON
  object, with `worker_configuration_unreadable`.
  The tool takes fields out of that object to build the configuration it hands Workers.
  So the object shape is the tool's own condition for reading the file.
- A worker configuration Workers refuses, with Workers' own code.
- A `--name` that is not one directory name, with `invalid_name`.
- A project directory that already exists, with `project_exists`.
  A symbolic link in its place counts as one, whether or not its target exists.

Workers' own codes are:

- `config_invalid` for a JSON object its contract does not admit.
- `model_map_missing` or `model_map_invalid` for the map.
- `model_unmapped` naming each entry the map lacks.

Each of `prepare`'s choices has its reason:

- It fetches only the revision, because SWE-bench's base commits are commits, which
  `git clone --branch` does not accept. Nothing in a test project needs earlier commits.
- It checks the revision out on a branch, because tasks are merged into the project's primary
  branch. A merge refuses a primary worktree on a detached `HEAD`.
  The branch is named `main` because, unless `--ref` names another,
  [SWE-bench cases](cases/module.md)' `grade` grades `main`.
- It installs without `d2`, which only renders the Specs' diagrams for a docsite a test project
  never publishes. Every preparation would otherwise download it again.
- It writes the worker configuration, because no worker runs without one. Neither the installer
  nor `init` writes it, because the models are the developer's choice.
  A user writes the models into the file by hand. This checkout's models are the ones its developer
  already uses.
  So a test project runs its workers as this checkout's own tasks do.
- It commits the installed and initialized project before it opens the task, because the task's
  branch starts from the committed head. A merge refuses a primary worktree with uncommitted paths.
- It binds the task to the root Module, because the brownfield workflow a test project first runs
  describes the whole project from it.

When a step fails, `prepare` stops with `command_failed`. Possible failing steps include:

- The fetch.
- The install.
- Either step of `init`.
- `task open`.

The error names these:

- The command.
- Its exit status.
- Its output.

`prepare` removes nothing it made.
It leaves the partial project directory for the developer to read.
Until the developer removes it, a later `prepare` under the same name refuses it with `project_exists`.

### Trusting test projects

Claude Code applies a project's `.claude/settings.json` allow rules only once that exact
repository is trusted. The installer writes these rules for its workflows.
Trust is keyed on the git repository root.
A parent folder's trust does not count.
A headless session never shows the trust dialog.
After one backup of the file, `trust` marks each named project's repository root trusted in Claude
Code's configuration.
That configuration is `~/.claude.json` (or under `CLAUDE_CONFIG_DIR`).
It changes the developer's own configuration, so the developer runs it.
A headless run does not need it.

Before opening an interactive Claude Code session in a test project, the developer trusts it so
that the installer's allow rules apply as in a user's trusted project.
The session can, for example, watch or continue a task by hand.
The project's workflow and commands then run without a prompt each.
`trust` prints these:

- Its configuration file.
- Under `trusted`, the repository roots it newly marked trusted.
- Under `already`, those that were trusted before.

When a project is already trusted, trusting it again changes nothing.
It names the root under `already` alone.

### Running a workflow

`run` runs a workflow to its end in the worktree of the test project's task `--task`.
The default task is `adopt`.
The workflow works on that worktree's [workspace binding](../glossary.json#concept.workspace-binding).
Every run it starts works on that binding too.
So neither the workflow's arguments nor any command names the task.
It prints the [workflow result](../glossary.json#concept.workflow-result) the workflow saved last in
its [workflow record](../glossary.json#concept.workflow-record).
That record is under `.concorde/tasks/<task>/workspace/workflow/` of the project.
It logs the session under `.concorde/runs/e2e/`.
Unless `--via driver` is given, a run is headless:

- A **headless run** (`--via claude`, the default) runs a headless session kept under
  `.concorde/runs/e2e/<task>-claude/`.
  The session starts in the task's worktree.
  It works there as the task's [task session](../glossary.json#concept.task-session), since running
  a task's workflow is its task session's work.
  The main agent never works inside a task worktree.
  The session is asked to run the installed workflow there.
  It is asked to report with `concorde workflow report`.
  The tool handles both testing conditions for it.
  The session keeps `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, so that `claude -p` does not stop the
  background workflow after ten idle minutes.
  Since the untrusted project ignores its allow rules, the tool grants these with `--allowedTools`:

  - The workflow.
  - The project MCP server's `workflow_step`, through which its step agents start every step.
  - Its report command.

  For the same reason, the tool gives the session the
  [project MCP server](../glossary.json#concept.project-mcp-server) itself with `--mcp-config`.
  It starts the server as the installer registers it.
  Without an approval, the untrusted project's `.mcp.json` entry is not loaded.
- A **driver run** (`--via driver`) runs the workflow's rendered Claude Code script from the runtime
  the installer places under `.concorde/framework/`.
  Every install carries that runtime.
  When that script is absent, it refuses with `script_missing`.
  It runs the script under the Workflows tests' stand-in for Claude Code's workflow runtime.
  Without a model, its step agents execute the real `concorde workflow step` command that the
  script's `workflow_step` call would run.
  They execute the real `concorde workflow report` command line too.
  Both execute in the task's worktree, so every workflow step is a real one.
  The step command is the worktree's own, run without a shell.
  The report's command line names it relative to the worktree, its working directory.
  So a project path holding spaces or shell syntax is never split or interpreted.
  It has no model between steps.
  Its Operations still launch real workers.
  So it tests Concorde's side without Claude Code's workflow runtime.

The options name these:

- `--workflow`: the workflow (default `brownfield`).
- `--module`: the Module it works on (default the root Module, `module.project`).
- `--mode`: its [workflow mode](../glossary.json#concept.workflow-mode) (default `no-ask`).

An `interactive` run ends at its first [decision point](../glossary.json#concept.decision-point).
`run` passes no answers to continue it.
When a run continues a task, `--retry <key>` becomes the workflow's own `retry` list.
When a run continues a task, `--restart <key>=<label>` becomes its `restart` map.

A workflow result whose status is not `ok` is printed like any other.
When a task's record cannot be read or names no worktree, `run` refuses it with `no_task`.
It fails instead in these cases:

- When the headless session ends `exited` or `no_session`
  ([how a headless session ends](sessions/module.md#overview)), it fails with `run_failed`.
  That error names its `session.json`.
- When the driver exits with a non-zero status, it fails with
  `run_failed`, with the driver's standard error and log.
- When `node` cannot be started for the driver, it fails with `command_failed`.
- When the session fails, it fails with the session's own error, such as `wait_exceeded`, naming
  its `session.json`.
- When the run saves no workflow result of its own, it fails with `no_result`.

Before it starts, `run` counts the saved results of the workflow record.
It takes only a result saved since.
When the record holds no more saved results after the run than before it, the tool fails with
`no_result` naming both counts.
When the newest saved result is missing, it fails with `no_result` naming the missing file.
So a result an earlier run of the task saved is never printed as this run's
([requirements](requirements.md#req.e2e.own-result)).

A saved result carries nothing that names the `run` that caused it.
Workflows lets anyone report in the workspace at any time.
Only when nobody else saves a result meanwhile does a result saved since the run started belong to
that run.
Therefore, one `run` at a time drives a test project.
While it runs, nobody else reports a workflow there:

- No second `run`.
- No session of the developer running or reporting the task's workflow.
- No `concorde workflow report` by hand.

The tool does not detect a breach.
During a run that saves none, a result someone else saves is printed as the run's.

### Watching

`watch` lists every run of the project's [run store](../glossary.json#concept.run-store) with these
fields:

- Its workspace.
- Its phase.
- Its step.
- Its outcome.

From each workspace's workflow record, it lists the workflow steps with their runs.
It also lists whether each step was superseded.

### The owners case

<a id="owners-case"></a>

`owners` uses real sessions to check the promise of [Main
session](../coordination/main-session/module.md#owners).
A run wakes only its owner.
Every other main session may see it.
The case keeps `--claude` Claude Code main sessions running at once in the test project's primary
worktree.
The default is two sessions.
The minimum is two.
Each is a live session of [Headless
sessions](sessions/module.md) whose wakes are its own program's.
The case plays two phases on the project's task `--task` (default `t1`).
That task must have a worktree.
`--claude-model` names the model every session runs on.
The case passes it unchanged to Claude Code's `--model`.
It is a Claude Code model id or alias, not a project model name, because the model map does not
concern main sessions.
Without it, each session runs on Claude Code's own default model.
The phases are:

1. **unowned**: the case itself starts `concorde task-validation` in the task worktree, a run of
   nobody's tool.
2. **owned by Claude Code**: the first session starts `task-validation` of the task in background
   Bash.

The case starts each run while it holds the task's [workspace
lock](../glossary.json#concept.workspace-lock).
The **launcher** of a run is the process that starts it:

- For the unowned run, the process the case itself starts.
- For the owned run, the first session's `claude` process.

The case judges only the run its own launch started.
It finds that run in the [run store](../glossary.json#concept.run-store) as the new run of the task
whose runner descends from the launcher.
The runner is the process the [run progress file](../glossary.json#concept.run-progress-file)'s
`host_pid` names.
Another run of the same workspace, launched by any other process, is never taken for it.
So the case reads the process tree of the operating system, Linux's `/proc`.
It must share the launcher's PID namespace.
A launcher whose commands run in a PID namespace of their own, such as a sandbox's, never has its run
found. The case then stops with `live_timeout`.
So the run cannot start its work before the case sees its launch completed.
The case takes that lock as Execution's runs take it.
The case holds an exclusive file lock on `locks/workspaces/<task>.lock`.
That path is under the `.concorde` named by the task worktree's
[workspace binding](../glossary.json#concept.workspace-binding).
When a run still holds the lock, the case waits at most the case's limit.
When the case leaves the phase, however the phase ends, it releases the lock.
For an owned run, the case first waits until the owner ends the turn in which it launched the run.
The case still holds the lock during this wait.
For either run, the case then waits until the run is in the
[run store](../glossary.json#concept.run-store), waiting in its lobby.
Only then does it release the lock.
The launching turn and the run's arrival share one deadline: the case's limit counted from the
launch.
So the case holds the lock at most that long after the launch.
The run therefore ends only after the launching turn ends.
Within the time the case judges, the run's end reaches the owner as a wake, never as the launching
tool's own answer.

The run queues for the lock as Execution's
[`--wait <seconds>`](../execution/module.md#waiting-for-a-busy-workspace) lets it.
Its wait is twice the case's limit, 1200 seconds, so it outlasts every hold of the case.
When the case holds the lock, the run's wait never expires
([requirements](requirements.md#req.e2e.owners-queue)).
Another run can take the lock after the case releases it and hold it past the run's wait.
If this causes a refusal with `workspace_busy`, the run does no work, so there is no run end to
judge.
In that case, the case stops with `workspace_busy` naming that run's result.

After the release, the case waits for the run's result at most the run's wait, 1200 seconds.
That wait always outlasts what remains of the run's own wait for the lock.
So a refusal for a busy workspace always arrives before the case's deadline.

Once the run writes its result, the case observes the sessions for a bounded window.
For an owned run, the case waits until the owner is woken and ends the turn it was woken into.
This wait lasts at most `--wake` seconds (180 by default) after the result.
Then it waits `--grace` seconds more (20 by default), so that it still sees a late wake of another
session.
For the unowned run, the case starts that additional wait at once.
Whether or not the owner was woken, the window ends then.
The case judges the phase over the time from the end of the owner's launching turn until the
window's end.
That end is the moment the turn's last event, Claude Code's `result`, was read from the session.
It is not the later moment at which the case noticed it.
For the unowned run, this time starts at the phase's start.
During this time, the case prompts no session.
The owner must begin a turn or receive a notification, Claude Code's `task_notification`.
No other session may do either.
Then the case asks every session that does not own the run to run `concorde task show <task>`.
Nothing is pushed into those sessions.
Each must find the run with the status of its result
([requirements](requirements.md#req.e2e.owners-case)).

```d2 illustrative
direction: down
hold: "The case holds the task's workspace lock"
start: "The launcher starts task-validation with --wait:\nthe case itself (unowned) or the first session (owned)"
turn: "Owned run: the owner's launching turn ends"
store: "The run enters the run store,\nwaiting for the lock"
release: "The case releases the lock"
result: "The run works and writes its result"
wake: "Owned run: wait until the owner is woken and its turn ends,\nat most --wake seconds after the result"
grace: "The case waits --grace seconds more"
judge: "Judge the wakes since the launching turn ended:\nthe owner woken, no other session woken"
ask: "Ask every other session to run task show:\neach must find the run with its result's status"
verdict: "Phase verdict, into owners.json" {shape: oval}
hold -> start -> turn -> store -> release -> result -> wake -> grace -> judge -> ask -> verdict
start -> store: "unowned run" {style.stroke-dash: 3}
result -> grace: "unowned run" {style.stroke-dash: 3}
```

The case prints its record.
It keeps the record as `owners.json` beside every session's events under
`.concorde/runs/e2e/owners/<time>/`.
The record contains these items:

- The sessions.
- Every phase with its owner.
- Every phase's run.
- Every phase's status.
- Each session's verdict.
- What each other session saw.
- The case's outcome: `passed`, or `failed` with every problem.

Problems include `claude-2 was woken by a run it does not own` or `the owner claude-1 was not woken
when its run ended` ([requirements](requirements.md#req.e2e.owners-deadline)).
A contradicted promise is the case's verdict, not an error.
Only what keeps the case from observing stops it with an error:

- Fewer than two sessions (`invalid_input`).
- A missing task (`no_task`).
- A session that cannot start or ends (`session_failed`).
- The unowned run's launch that cannot be started (`command_failed`).
- Another run holding the task's workspace lock for the case's whole limit.
- The case's own run refused because another run held the lock.
- The infrastructure's deadline, `live_timeout`.

Both lock failures use `workspace_busy`.
`live_timeout` covers these cases:

- A session does not end a turn the case prompted within the case's limit of 600 seconds.
- The launching turn and the run's arrival in the run store together take longer than that limit.
- The run writes no result within the run's wait, 1200 seconds, after the release.

The case spends real model turns.
Like every end-to-end run, the developer runs it by hand.

## Why it is built this way

**Two kinds of run, to locate a failure.** When a headless run fails, a driver run of the same task
with `--retry` for the failed step's key runs that step again.
It omits Claude Code's workflow runtime.
It reuses the earlier steps that succeeded.
So it points to whether Concorde or that runtime is at fault.
Without `--retry`, it would only find the failed run recorded.
As [Workflows](../workflows/module.md#steps-and-their-keys) says, a retry supersedes the retried step.
It also supersedes every step recorded after it.
So every later step runs anew too, including those that succeeded.
Each incurs its cost again.
Each has new evidence.
Since the workers are real, one such comparison is evidence, not proof.

**The driver reuses the Workflows tests' runtime.** The driver run does not have a runtime of its
own.
It runs the Workflows tests' JavaScript sandbox, `tests/concorde/workflows/run_script.mjs`, with
step agents that execute the real commands.
This couples End-to-end testing to a test file of Workflows.
The coupling is accepted because a second stand-in runtime would need to follow every change of
the rendered script's step adapter.
The Workflows tests already follow those changes.
A second runtime could drift from them.
The file stays Workflows'.
Both Modules list it, so a change to it concerns the driver run too.

**The testing conditions stay here.** Since a user's main session is interactive and its project
trusted, neither the wait ceiling nor the trust keying reaches the user-facing guidance.
This Module handles both for tests.
It changes nothing a user gets.

## Files

<a id="realization.e2e.tool"></a>

The **End-to-end tool** realization is `scripts/e2e/e2e.py`.
It handles these actions on test projects:

- Preparing.
- Trusting.
- Running.
- Watching.

It also provides the command line of its children's commands:

- `session`.
- `repair-specs`.
- `grade`.
- `dogfood`.

`scripts/e2e/common.py` holds what the tools share:

- The checkout.
- The end-to-end root.
- The error type.
- Running a command.
- Cloning a revision.

The realization also lists `tests/concorde/workflows/run_script.mjs` as a file it shares with
Workflows.
This JavaScript sandbox of the Workflows tests stands in for Claude Code's workflow runtime.
A driver run runs it.

<a id="realization.e2e.tests"></a>

The **End-to-end tool tests**, `tests/concorde/e2e/test_e2e.py`, check the tool's pure parts.
They use local repositories only, without the network or agents.

<a id="realization.e2e.owners"></a>

The **owners case** is `scripts/e2e/owners.py`.
It handles these actions:

- Playing the phases.
- Holding the workspace lock.
- Judging who was woken.
- Asking the others what they see.

Its tests, `tests/concorde/e2e/test_owners.py`, run the whole case with stand-ins for `claude` and
`concorde`.
Real sessions and runs would spend model turns and take minutes, so deterministic stand-ins play
them.
The `claude` stand-in speaks the live sessions' protocol.

## The children

<a id="contains-sessions"></a>

**Headless sessions** drives a real headless Claude Code main session.
It performs these actions:

- Grants the session its tools.
- Tells it the conditions of running headless.
- Wakes it when a run it left behind ends.
- Keeps every round's log.

The headless runs of workflows are headless sessions.
So are the [dogfood scenarios](../glossary.json#concept.dogfood-scenario)' sessions.

<a id="contains-cases"></a>

**SWE-bench cases** holds the steps that exist only for a case worked on a real issue.
It repairs the Specs adoption left in one bounded round.
That round changes Specs and never code.
It grades the merged change with the case's own tests in a throwaway worktree, the way SWE-bench
grades it.
A case's project is a test project prepared here at the case's base commit.

<a id="contains-dogfood"></a>

**Dogfood scenarios** performs these steps:

- Injects a known fault into a clone of this checkout's Concorde.
- Makes a develop install of a real project from it.
- Runs a headless session with an ordinary request.
- Evaluates whether the main agent reported the defect as Dogfooding requires without working
  around it or changing Concorde.

## Around it

To set a test project up, End-to-end testing relies on these Modules:

- Distribution.
- Spec core.
- Tasks.
- Workers.
- Operations.

It relies on Workflows and Execution to run the project and follow it.
It relies on Main session for the promise the owners case checks.

<a id="uses-distribution"></a>

**Distribution** provides the installer and the `concorde` command.
They set a test project up the way a user's project is set up, with every
[part](../glossary.json#concept.part) installed.
Distribution routes each command to the part that registered it.
A test project always runs the Concorde of this checkout.
Before checking a worker configuration, `prepare` loads its parts' registrations as the `concorde`
command loads them.
It checks the configuration against the Operations they register.
When any of these fails, `prepare` stops with `command_failed`:

- The installer.
- `concorde init`.
- `concorde task open`.

The error names these:

- That command.
- Its exit status.
- Its output.

`prepare` leaves the partial project directory as it is
(see [Preparing a test project](#preparing-a-test-project)).
End-to-end testing never repairs a failed setup, since the failure is the finding.

<a id="uses-spec"></a>

**Spec core** carries out `concorde init`.
`prepare` runs it as a propose followed by an apply of that proposal.
This is the envelope
[req.spec.init-explicit-envelope](../spec-tooling/spec/requirements.md#req.spec.init-explicit-envelope)
checks.
Its [initialization contract](../spec-tooling/spec/contracts.md#initialization) creates the root
Module.
Unless named otherwise, that Module is `module.project`.
`prepare` binds the task to that Module.
The contract also records the interpreter `--python` names.
When either step fails, `prepare` stops with `command_failed`.

<a id="uses-workers"></a>

**Workers** owns the [worker configuration](../glossary.json#concept.worker-configuration) that
`prepare` writes.
It owns the [model map](../glossary.json#concept.model-map) by which the developer's machine reaches
each model.
Its [contracts](../worker-harness/workers/contracts.md) define both.
Workers' check of a whole configuration against the map validates it
([scenario.workers.model-map-checked](../worker-harness/workers/scenarios.md#scenario.workers.model-map-checked)).
It resolves the model of every worker of every Operation.
It refuses with these codes:

- `config_invalid`.
- `model_map_missing`.
- `model_map_invalid`.
- `model_unmapped`.

The last code names every model and backend the map lacks with the workers that would take them.
`prepare` builds the configuration as a developer writes it.
Before anything is cloned, it hands the configuration to that check.
On refusal, it passes on the code and the map's path.
On that refusal, it prepares nothing.

<a id="uses-operations"></a>

**Operations** assembles its [Operation catalog](../glossary.json#concept.operation-catalog) from
what the installed parts register, in Concorde Method's Operations.
It lists every Operation with the ids of the workers it may launch.
Workers' check resolves those workers' models for `prepare`, so that a test project's first
workflow finds a model for each of them.

<a id="uses-workflows"></a>

**Workflows** runs the workflows a test project runs, such as Method's
[brownfield workflow](../glossary.json#concept.brownfield-workflow).
It renders their scripts.
It also renders the stand-in runtime of its tests that a driver run reuses.
It provides the workflow result a run ends with.
It provides the workflow record of each workspace.
In that record, `run` finds the latest saved result.
In that record, `watch` finds the steps.
End-to-end testing relies on the record listing the saved results in order and each step with its
run.

<a id="uses-execution"></a>

**Execution** runs these in the workspace the test project's task worktree is bound as:

- Every workflow step.
- Every Operation.
- Every [execution command](../glossary.json#concept.execution-command).

When `prepare` opens the task, Tasks writes that workspace binding.
End-to-end testing never writes it.
For each run, `watch` reads the run store's
[run progress files](../glossary.json#concept.run-progress-file).
It relies on them to name these fields:

- Workspace.
- Phase.
- Step.
- Status.

When a run lacks a run progress file, `watch` leaves it out of the list rather than failing.
The developer may run `watch` at any moment.
The file can be absent for either reason:

- The runner did not write it yet.
- The runner died before writing it.

If the runner dies before writing the file, a run left out stays out.

<a id="uses-kernel"></a>

**Kernel** defines the [workspace binding](../glossary.json#concept.workspace-binding) that names
each test project's task workspace.
End-to-end testing reads it.
End-to-end testing never writes it.
Kernel also defines the [workspace lock](../glossary.json#concept.workspace-lock).
The owners case holds it to prevent a run from starting its work before the case looks.
The case relies on a run waiting for it.

<a id="uses-main-session"></a>

**Main session** makes the promise the owners case checks: a run wakes only its owner main
session.
Every other main session may see that run.

<a id="uses-tasks"></a>

**Tasks** carries out `concorde task open`, by which `prepare` opens the test project's task.
It creates these:

- The task's branch and worktree.
- The [workspace binding](../glossary.json#concept.workspace-binding) that every run there reads.
- The task's folder, whose workspace folder holds the workflow record `run` reads.

Tasks provides the [task record](../glossary.json#concept.task-record) in that folder.
`run` works in the worktree the record names.
The owners case runs its unowned run there too.
Tasks also provides `concorde task show`, which a Claude Code session asks.
When `task open` fails, `prepare` stops with `command_failed` as for every other setup step.

SWE-bench is included as external material.
Its harness names the Python projects it draws from, such as `psf/requests` and `pallets/flask`.
These are existing codebases of known size and quality to test on.
