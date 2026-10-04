# End-to-end testing

## Purpose

End-to-end testing is how the Concorde project tests itself on real codebases with real agents. It
takes a project from the Python repositories SWE-bench draws from, sets it up exactly as a user
would, runs a workflow in it with real workers, and lets the developer watch every run. It exists
for the people developing Concorde: nothing of it is installed into a project, and a Concorde user
never meets it. Its second job is to keep apart the problems that only testing conditions cause,
such as a headless main session or an untrusted scratch project, from the problems a user would
meet, so that the first are solved here rather than in what users get.

End-to-end runs are not in the test suite. They clone from the network, spend real model tokens
and take tens of minutes, and their outcome depends on the model. The suite keeps the
deterministic acceptance test, which runs the same workflow with fake workers; this Module is
what the developer runs by hand, after a change to Adoption, Workflows or the worker harness, and
whose findings become ordinary tasks.

## Core concepts

<a id="concept.test-project"></a>

**[Test project](../glossary.json#concept.test-project).** A test project is a real codebase set up
the way a user's project is set up: a repository SWE-bench names, or another that `--any` admits,
fetched at a pinned revision into the **end-to-end root**, with the Concorde of this checkout
installed and initialized, a [worker configuration](../glossary.json#concept.worker-configuration)
written and a task open, bound to the root [Module](../glossary.json#concept.module). The end-to-end root is `CONCORDE_E2E_ROOT` when it
is set, and otherwise `concorde-e2e` in the system's temporary directory (`/tmp/concorde-e2e` on
Linux), wherever that directory lies; each test project is the directory `test-<name>` there,
`<name>` being the repository's name or the one `--name` gives. A test project is its own
repository, so its workers run in its own `.claude/worktrees/`, and the Harness hides its Git
metadata from them wherever it lies. The tool refuses a root, the default or `CONCORDE_E2E_ROOT`,
that lies inside this checkout, since Claude Code loads every `CLAUDE.md` above a session's working
directory and would give each session of a test project there Concorde's own development
instructions. Test projects are throwaway: the developer reads a test project's Specs, runs and
records, and removes its directory when the test is done, or prepares the next one under another
name.

**Headless run and driver run.** A test project runs a workflow in one of two ways, which answer
different questions. A **headless run** is what a user's task session does: a real
[headless session](../glossary.json#concept.headless-session) runs the installed workflow, Claude
Code's workflow runtime and its [step agents](../glossary.json#concept.step-agent) included. A
**driver run** removes the session's model and Claude Code's workflow runtime from between the
steps, while its [Operations](../glossary.json#concept.operation) still launch real workers, so a
failure there lies on Concorde's side, in its commands, Operations or workers.

**Testing conditions.** A user's main session is interactive and its project trusted. A test runs
headless in a scratch project, so two things differ: `claude -p` stops a background workflow after
ten idle minutes, and an untrusted project ignores its allow rules. This Module handles both for
tests, together with its child [Headless sessions](sessions/module.md), and changes nothing a user
gets.

## Overview

### Children and providers

Three children carry parts of End-to-end testing. [Headless sessions](sessions/module.md) drives
any real headless Claude Code main session, [SWE-bench cases](cases/module.md) repairs and grades
cases worked on real issues, and [Dogfood scenarios](dogfood/module.md) tests a
[develop install](../glossary.json#concept.develop-install)'s
[main agent](../glossary.json#concept.main-agent) against a known
[Concorde defect](../glossary.json#concept.concorde-defect). Each reaches a different part of
Concorde: a headless session wakes on the runs of Execution, a case is set up through Distribution,
and a dogfood scenario drives headless sessions against a develop install that Dogfooding describes.
The parent itself sets test projects up through Distribution's installer and `concorde` command,
whose `init` Spec core's initialization carries out and whose `task open` Tasks carries out,
checks their worker configuration with Workers over every worker the Operations' catalog lists,
runs the workflows of Workflows in the workspaces Execution runs, and checks with the owners case
the promise Main session makes about who a run wakes ([Around it](#around-it)).

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

The developer prepares a test project, runs a workflow in it, headless or through the driver, and
watches its runs while it runs or afterwards; every step is one command of the end-to-end tool,
described under [The commands](#the-commands). The two kinds of run differ only in what sits
between the [workflow steps](../glossary.json#concept.workflow-step): both execute the real
`concorde workflow step` command lines in the task's worktree, and both reach real workers.

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

The tool is one command of this checkout, `scripts/e2e/e2e.py`, printing one JSON object per
command and `{"error": …}` with the failed command and its output otherwise. It exits 0 when it
prints its result, also a workflow result whose status is not `ok` and an owners case that ended
`failed`, since those are the test's findings; 1 when it prints `{"error": …}`; and 2, printing its
usage to standard error and doing nothing, for a malformed command line, such as a `--restart`
that is not `<key>=<label>`. A failure none of its steps names a code for, such as a command that
cannot be started at all, is printed as an error too, never as a traceback: a command it cannot
start as `command_failed`, and anything else it did not foresee as `unexpected_error` with the
traceback beside its detail:

```text
python3 scripts/e2e/e2e.py repos
python3 scripts/e2e/e2e.py prepare <owner/name> --rev <tag|branch|commit> [--name <dir>] [--python <interpreter>] [--task <task>] [--any] [--worker-model <model>]
python3 scripts/e2e/e2e.py trust <project>…
python3 scripts/e2e/e2e.py run <project> [--via claude|driver] [--workflow brownfield] [--task <task>] [--module <id>] [--mode no-ask|interactive] [--retry <key>]… [--restart <key>=<label>]…
python3 scripts/e2e/e2e.py watch <project>
python3 scripts/e2e/e2e.py owners <project> [--task t1] [--claude 2] [--claude-model <model>] [--wake 180] [--grace 20]
```

Its children add `session` ([Headless sessions](sessions/module.md)), `repair-specs` and `grade`
([SWE-bench cases](cases/module.md)) and `dogfood` ([Dogfood scenarios](dogfood/module.md)).

**A worked example.** The developer prepares `psf/requests` at its tag `v2.31.0`, runs the
[brownfield workflow](../glossary.json#concept.brownfield-workflow) in it as a headless run and,
from another terminal while it runs or afterwards, watches its runs. Shortened, the three commands
print:

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

The project is then a throwaway: the developer reads its Specs, runs and records, and removes the
directory, or prepares the next one under another `--name`.

The [owners case](#owners-case) plays its runs on a task of its own, `t1` by default, so the
developer prepares a project for it with that task and then runs it there:

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
`references/swe-bench/`. `prepare psf/requests --rev v2.31.0` fetches that revision, a tag, a
branch or a commit, without earlier history into the end-to-end root, under `--name` or the
repository's name, checks it out as a `main` branch, installs Concorde from this checkout without
`d2`, initializes it, writes its worker configuration, commits and opens a task bound to the root
Module, which makes a test project. The task is `--task` (default `adopt`).

The end-to-end root is resolved to an absolute path before anything else, so a relative
`CONCORDE_E2E_ROOT` names the same directory for every command `prepare` runs, whichever directory
that command runs in.

It initializes the project as a user does, in the two steps of Spec core's
[initialization](../spec-tooling/spec/contracts.md#initialization): `concorde init --propose` with
the project directory's name and, when `--python` is given, `--python <interpreter>`, then
`concorde init --apply` of that proposal. Initialization creates the root Module, `module.project`,
and records the interpreter in the project configuration, where the project's
[configured checks](../glossary.json#concept.configured-check) take it for `{python}`; `prepare`
writes neither itself.

The [worker configuration](../glossary.json#concept.worker-configuration) runs every worker on
`--worker-model`, a project model name, when it is given, enabling only that model, and otherwise
takes this checkout's own `.concorde/workers.json` without its `runtime` paths, which name this
checkout's directories. The test project's sessions and workers run in the developer's own
environment, so the developer's [model map](../glossary.json#concept.model-map) resolves its models
as it does the developer's own projects', and no map is written for it. Before anything is cloned,
`prepare` hands the configuration it built to Workers' check of a configuration, which validates it
and resolves through that map the model of every worker of every Operation the
[Operation catalog](../glossary.json#concept.operation-catalog) lists, having loaded the Operations
this checkout's parts register as the `concorde` command loads them; `prepare` enumerates no
worker itself and passes Workers' refusal on with its code ([Around it](#uses-workers)).

`prepare` refuses, each time before anything is cloned:

- an end-to-end root inside this checkout, with `root_inside_checkout`
  ([Test project](#core-concepts));
- a repository SWE-bench does not name, unless `--any` is given, with `unknown_repository` naming
  the known ones;
- without `--worker-model`, this checkout's own worker configuration when it cannot be read as JSON,
  with `worker_configuration_unreadable`;
- a worker configuration Workers refuses, with Workers' own code: `config_invalid` for a
  configuration its contract does not admit, `model_map_missing` or `model_map_invalid` for the map,
  and `model_unmapped` naming each entry the map lacks;
- a project directory that already exists, with `project_exists`.

Each of `prepare`'s choices has its reason:

- It fetches only the revision, because SWE-bench's base commits are commits, which
  `git clone --branch` does not accept, and nothing in a test project needs earlier history.
- It checks the revision out on a branch, because tasks are merged into the project's primary
  branch, and a merge refuses a primary worktree on a detached `HEAD`; the branch is named `main`
  because [SWE-bench cases](cases/module.md)' `grade` grades `main` unless `--ref` names another.
- It installs without `d2`, which only renders the Specs' diagrams for a docsite a test project
  never publishes, and which every preparation would otherwise download again.
- It writes the worker configuration, because no worker runs without one and neither the
  installer nor `init` writes it: the models are the developer's choice, which a user writes into
  the file by hand. This checkout's models are the ones its developer already uses, so a test
  project runs its workers as this checkout's own tasks do.
- It commits the installed and initialized project before it opens the task, because the task's
  branch starts from the committed head, and a merge refuses a primary worktree with uncommitted
  paths.
- It binds the task to the root Module, because the brownfield workflow a test project first runs
  describes the whole project from it.

A step that fails, such as the fetch, the install, either step of `init` or `task open`, stops
`prepare` with `command_failed`, naming the command, its exit status and its output. `prepare`
removes nothing it made: the partial project directory is left for the developer to read, and a
later `prepare` under the same name refuses it with `project_exists` until the developer removes it.

### Trusting test projects

Claude Code applies a project's `.claude/settings.json` allow rules, which the installer writes for
its workflows, only once that exact repository is trusted: trust is keyed on the git repository
root, a parent folder's trust does not count, and a headless session never shows the trust dialog.
`trust` marks each named project's repository root trusted in Claude Code's configuration,
`~/.claude.json` (or under `CLAUDE_CONFIG_DIR`), after backing the file up once. It changes the
developer's own configuration, so the developer runs it; a headless run does not need it.

The developer trusts a test project before opening an interactive Claude Code session in it, such as
to watch or continue a task by hand, so that the installer's allow rules apply there as in a user's
trusted project and its workflow and commands run without a prompt each. `trust` prints its
configuration file, under `trusted` the repository roots it newly marked trusted and under `already`
those that were trusted before; trusting a trusted project again changes nothing and names its root
under `already` alone.

### Running a workflow

`run` runs a workflow to its end in the worktree of the test project's task `--task` (default
`adopt`), whose [workspace binding](../glossary.json#concept.workspace-binding) the workflow and
every run it starts work on, so neither the workflow's arguments nor any command names the task. It
prints the [workflow result](../glossary.json#concept.workflow-result) the workflow saved last in
its [workflow record](../glossary.json#concept.workflow-record), under
`.concorde/tasks/<task>/workspace/workflow/` of the project, and logs the session under
`.concorde/runs/e2e/`. A run is headless unless `--via driver` is given:

- A **headless run** (`--via claude`, the default) runs, as a headless session kept under
  `.concorde/runs/e2e/<task>-claude/`, a session started in the task's worktree that works there as
  the task's [task session](../glossary.json#concept.task-session), since running a task's
  workflow is its task session's work and the main agent never works inside a task worktree, and is
  asked to run the installed workflow there and report with `concorde workflow report`. Both
  testing conditions are handled for it: the session keeps
  `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, so that `claude -p` does not stop the background
  workflow after ten idle minutes, and the workflow, the project MCP server's `workflow_step`, through
  which its step agents start every step, and its report command are granted with
  `--allowedTools`, since the untrusted project ignores its allow rules. For the same reason the
  session is given the [project MCP server](../glossary.json#concept.project-mcp-server) itself with
  `--mcp-config`, started as the installer registers it: the untrusted project's `.mcp.json` entry
  is not loaded without an approval.
- A **driver run** (`--via driver`) runs the rendered Claude Code script of the workflow from the
  runtime the installer places under `.concorde/framework/`, which every install carries, and
  refuses with `script_missing` when that script is absent. It runs the script under the stand-in
  for Claude Code's workflow runtime of the Workflows tests, whose step agents execute, without a
  model, the real `concorde workflow step` command that the `workflow_step` call the script hands
  them would run, and the real `concorde workflow report` command line, in the task's worktree, so
  every workflow step is a real one. The step command is the worktree's own, run without a shell,
  and the report's command line names it relative to the worktree, its working directory, so a
  project path holding spaces or shell syntax is never split or interpreted. It has no model between
  steps, while its Operations still launch real workers, so it tests Concorde's side without Claude
  Code's workflow runtime.

`--workflow` names the workflow (default `brownfield`), `--module` the Module it works on (default
the root Module, `module.project`) and `--mode` its
[workflow mode](../glossary.json#concept.workflow-mode) (default `no-ask`); an `interactive` run
ends at its first [decision point](../glossary.json#concept.decision-point), and `run` passes no
answers to continue it. `--retry <key>` and `--restart <key>=<label>` become the workflow's own
`retry` list and `restart` map, for a run that continues a task.

A workflow result whose status is not `ok` is printed like any other. `run` refuses a task whose
record cannot be read or names no worktree with `no_task`. It fails instead with
`run_failed` when the headless session ends `exited` or `no_session`
([how a headless session ends](sessions/module.md#overview)), naming its `session.json`,
or when the driver exits with a non-zero status, with its standard error and log; with the
session's own error, such as `wait_exceeded`, when the session fails, naming its `session.json`;
and with `no_result` when the run saved no workflow result of its own. `run` counts the saved results
of the workflow record before it starts and takes only a result saved since: a record that holds no
more saved results after the run than before it, or whose newest saved result is missing, fails with
`no_result` naming both counts or the missing file, so a result an earlier run of the task saved is
never printed as this run's ([requirements](requirements.md#req.e2e.own-result)).

A saved result carries nothing that names the `run` that caused it, and Workflows lets anyone report
in the workspace at any time, so a result saved since the run started is the run's own only when
nobody else saves one meanwhile. A test project is therefore driven by one `run` at a time, and
while it runs nobody else reports a workflow there: no second `run`, no session of the developer
running or reporting the task's workflow, and no `concorde workflow report` by hand. The tool does
not detect a breach; a result someone else saved during a run that saved none would be printed as
the run's.

### Watching

`watch` lists every run of the project's [run store](../glossary.json#concept.run-store) with its
workspace, phase, step and outcome, and, from each workspace's workflow record, its workflow steps
with their runs and whether they were superseded.

### The owners case

<a id="owners-case"></a>

`owners` checks, with real sessions, the promise of [Main
session](../coordination/main-session/module.md#owners) that a run wakes only its owner while every
other main session may see it: it keeps `--claude` Claude Code main sessions running at once in the
test project's primary worktree, two by default and at least two, each a live session of [Headless
sessions](sessions/module.md) whose wakes are its own program's, and plays two phases on the
project's task `--task` (default `t1`), which must have a worktree. `--claude-model` names the model
every session runs on, passed unchanged to Claude Code's `--model`, so it is a Claude Code model id
or alias, not a project model name: the sessions are main sessions, which the model map does not
concern. Without it each session runs on Claude Code's own default model.

1. **unowned**: the case itself starts `concorde task-validation` in the task worktree, a run of
   nobody's tool;
2. **owned by Claude Code**: the first session starts `task-validation` of the task in background
   Bash.

Each run is started while the case holds the task's [workspace
lock](../glossary.json#concept.workspace-lock), so that the run cannot start its work before the
case has seen its launch completed. The case takes that lock as Execution's runs take it, an
exclusive file lock on `locks/workspaces/<task>.lock` of the `.concorde` the task worktree's
[workspace binding](../glossary.json#concept.workspace-binding) names, waiting for a run that still
holds it at most the case's limit, and releases it when it leaves the phase, however the phase ends.
For an owned run the case, still holding the lock, first waits until the owner has ended the turn
in which it launched the run; for either run it then waits until the run is in the
[run store](../glossary.json#concept.run-store), waiting in its lobby, and only then releases the
lock. The launching turn and the run's arrival share one deadline, the case's limit counted from
the launch, so the case holds the lock at most that long after the launch. The run therefore ends
only after the launching turn did, and its end reaches the owner as a wake, never as the launching
tool's own answer, within the time the case judges.

The run queues for the lock as Execution's
[`--wait <seconds>`](../execution/module.md#waiting-for-a-busy-workspace) lets it, with twice the
case's limit, 1200 seconds, so its wait outlasts every hold of the case and never expires while the
case holds the lock ([requirements](requirements.md#req.e2e.owners-queue)). Should it still be
refused with `workspace_busy`, because another run took the lock after the case released it and held
it past the run's wait, the run did no work and there is no run end to judge: the case stops with
`workspace_busy` naming that run's result.

Once the run has written its result, the case observes the sessions for a bounded window. For an
owned run it waits until the owner has been woken and has ended the turn it was woken into, but at
most `--wake` seconds (180 by default) after the result; then, and for the unowned run at once, it
waits `--grace` seconds more (20 by default), so that a wake of another session that comes late is
still seen. The window ends then, whether or not the owner was woken, and the phase is judged over
the time since the owner's launching turn ended (the phase's start for the unowned run) until the
window's end, in which the case prompts no session: the owner must have begun a turn or received a
notification, Claude Code's `task_notification`, and no other session may have done either. Then
every session that does not own the run, into which nothing is pushed, is asked to run
`concorde task show <task>` and must find the run with the status of its result
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

The case prints, and keeps as `owners.json` beside every session's events under
`.concorde/runs/e2e/owners/<time>/`, the sessions, every phase with its owner, run, status, each
session's verdict and what each other session saw, and its outcome: `passed`, or `failed` with every
problem, such as `claude-2 was woken by a run it does not own` or `the owner claude-1 was not woken
when its run ended` ([requirements](requirements.md#req.e2e.owners-deadline)). A contradicted
promise is the case's verdict, not an error. What stops the case with an error is only what keeps it
from observing: fewer than two sessions (`invalid_input`), a missing task (`no_task`), a session
that cannot start or ends (`session_failed`), another run holding the task's workspace lock for the
case's whole limit, or the case's own run refused because another run held it (`workspace_busy`),
and `live_timeout`, the infrastructure's deadline, when within the case's limit of 600 seconds a
session does not end a turn the case prompted, the launching turn and the run's arrival in the run
store together take longer, or the run writes no result. The case spends real model turns and is run
by hand, like every end-to-end run.

## Why it is built this way

**Two kinds of run, to locate a failure.** When a headless run fails, a driver run of the same task
with `--retry` for the failed step's key runs that step again without Claude Code's workflow
runtime, reusing the steps before it that succeeded, and so points to whether Concorde or that
runtime is at fault; without `--retry` it would only find the failed run recorded. A retry
supersedes the retried step and every step recorded after it, as
[Workflows](../workflows/module.md#steps-and-their-keys) says, so every later step runs
anew too, those that had succeeded included, at their cost again and with new evidence. Since the
workers are real, one such comparison is evidence, not proof.

**The driver reuses the Workflows tests' runtime.** The driver run does not have a runtime of its
own: it runs the JavaScript sandbox of the Workflows tests, `tests/concorde/workflows/run_script.mjs`,
with step agents that execute the real commands. This couples End-to-end testing to a test file of
Workflows, and the coupling is accepted: a second stand-in runtime would have to follow every change
of the rendered script's step adapter that the Workflows tests already follow, and could drift from
them. The file stays Workflows' and is listed by both Modules, so a change to it concerns the driver
run too.

**The testing conditions stay here.** Since a user's main session is interactive and its project
trusted, neither the wait ceiling nor the trust keying reaches the user-facing guidance; this Module
handles both for tests, and changes nothing a user gets.

## Files

<a id="realization.e2e.tool"></a>

The **End-to-end tool** realization is `scripts/e2e/e2e.py`: preparing, trusting, running and
watching test projects, and the command line of its children's `session`, `repair-specs`, `grade`
and `dogfood` commands; `scripts/e2e/common.py` holds what the tools share, the checkout, the
end-to-end root, the error type, running a command and cloning a revision. It also lists
`tests/concorde/workflows/run_script.mjs`, the JavaScript sandbox of the Workflows tests that
stands in for Claude Code's workflow runtime and that a driver run runs, as a file it shares with
Workflows.

<a id="realization.e2e.tests"></a>

The **End-to-end tool tests**, `tests/concorde/e2e/test_e2e.py`, check the tool's pure parts, the
repository list, trust, the headless command, cloning a revision, watching and the result `run`
takes, on local repositories only, without the network or agents.

<a id="realization.e2e.owners"></a>

The **owners case** is `scripts/e2e/owners.py`: the phases, holding the workspace lock, judging
who was woken and asking the others what they see. Its tests,
`tests/concorde/e2e/test_owners.py`, run the whole case with stand-ins for `claude` and
`concorde`, the first speaking the live sessions' protocol, among them a `claude` stand-in that is
also woken for every run it does not own, one never woken by its own run, and a `concorde`
stand-in whose run waits in the lobby for the lock, as Execution's does, or is refused there.

## The children

<a id="contains-sessions"></a>

**Headless sessions** drives a real headless Claude Code main session: it grants the session its
tools, tells it the conditions of running headless, wakes it when a run it left behind ends and
keeps every round's log. The headless runs of workflows are headless sessions, and so are
the [dogfood scenarios](../glossary.json#concept.dogfood-scenario)' sessions.

<a id="contains-cases"></a>

**SWE-bench cases** holds the steps that exist only for a case worked on a real issue: repairing
the Specs adoption left in one bounded round that changes Specs and never code, and grading the
merged change with the case's own tests in a throwaway worktree, the way SWE-bench grades it. A
case's project is a test project prepared here at the case's base commit.

<a id="contains-dogfood"></a>

**Dogfood scenarios** injects a known fault into a clone of this checkout's Concorde, makes a
develop install of a real project from it, runs a headless session with an ordinary request and
evaluates whether the main agent reported the defect as Dogfooding requires without working around
it or changing Concorde.

## Around it

End-to-end testing relies on Distribution, Spec core, Tasks, Workers and Operations to set a test
project up, on Workflows and Execution to run it and follow it, and on Main session for the promise
the owners case checks.

<a id="uses-distribution"></a>

**Distribution** provides the installer and the `concorde` command that set a test project up the
way a user's project is set up, with every [part](../glossary.json#concept.part) installed, routing
each command to the part that registered it; a test
project always runs the Concorde of this checkout. Its parts' registrations are what `prepare`
loads, as the `concorde` command loads them, before it checks a worker configuration against the
Operations they register. When the installer, `concorde init` or
`concorde task open` fails, `prepare` stops with `command_failed`
naming that command, its exit status and its output, and leaves the partial project directory as it
is (see [Preparing a test project](#preparing-a-test-project)); End-to-end testing never repairs a
failed setup, since the failure is the finding.

<a id="uses-spec"></a>

**Spec core** carries out `concorde init`, which `prepare` runs as a propose followed by an apply of
that proposal, the envelope
[req.spec.init-explicit-envelope](../spec-tooling/spec/requirements.md#req.spec.init-explicit-envelope)
checks; its [initialization contract](../spec-tooling/spec/contracts.md#initialization) creates the
root Module, `module.project` unless named otherwise, to which `prepare` binds the task, and records
the interpreter `--python` names. `prepare` stops with `command_failed` when either step fails.

<a id="uses-workers"></a>

**Workers** owns the [worker configuration](../glossary.json#concept.worker-configuration) that
`prepare` writes and the [model map](../glossary.json#concept.model-map) by which the developer's
machine reaches each model, both defined by its [contracts](../worker-harness/workers/contracts.md).
Workers' check of a whole configuration against the map
([scenario.workers.model-map-checked](../worker-harness/workers/scenarios.md#scenario.workers.model-map-checked))
validates it and resolves the model of every worker of every Operation, refusing with
`config_invalid`, `model_map_missing`, `model_map_invalid` or `model_unmapped`, the last naming
every model and backend the map lacks with the workers that would take them. `prepare` builds the
configuration as a developer writes it, hands it to that check before anything is cloned, and passes
a refusal on with its code and the map's path, preparing nothing.

<a id="uses-operations"></a>

**Operations** lists in its [Operation catalog](../glossary.json#concept.operation-catalog), assembled
from what the installed parts register, in Concorde Method's Operations, every Operation with the
ids of the workers it may launch, the workers whose models Workers' check
resolves for `prepare`, so that a test project's first workflow finds a model for each of them.

<a id="uses-workflows"></a>

**Workflows** runs the workflows a test project runs, such as Method's
[brownfield workflow](../glossary.json#concept.brownfield-workflow), renders their scripts and the stand-in
runtime of its tests that a driver run reuses, the workflow result a run ends with, and the
workflow record of each workspace, where `run` finds the latest saved result and `watch` the steps.
End-to-end testing relies on the record listing the saved results in order and each step with its
run.

<a id="uses-execution"></a>

**Execution** runs every workflow step, Operation and
[execution command](../glossary.json#concept.execution-command) of a test project in the workspace
its task worktree is bound as: Tasks writes that workspace binding when `prepare` opens the task,
and End-to-end testing never writes it. `watch` reads the run store's
[run progress files](../glossary.json#concept.run-progress-file) for each run's workspace, phase,
step and status, relying on them to name those fields. A run without a run progress file, whether
its runner has not written it yet or died before writing it, is left out of the list rather than
failing `watch`, which the developer may run at any moment; a run left out for the second reason
stays out.

<a id="uses-kernel"></a>

**Kernel** defines the [workspace binding](../glossary.json#concept.workspace-binding) that names
each test project's task workspace, which End-to-end testing reads and never writes, and the
[workspace lock](../glossary.json#concept.workspace-lock), which the owners case holds to keep a run
from starting its work before the case has looked, relying on a run waiting for it.

<a id="uses-main-session"></a>

**Main session** makes the promise the owners case checks: a run wakes only its owner main
session, while every other main session may see it.

<a id="uses-tasks"></a>

**Tasks** carries out `concorde task open`, by which `prepare` opens the test project's task: the
task's branch and worktree, the [workspace binding](../glossary.json#concept.workspace-binding) that
every run there reads, and the task's folder whose workspace folder holds the workflow record `run`
reads. It provides the [task record](../glossary.json#concept.task-record) in that folder, whose
worktree `run` works in and the owners case runs its unowned run in, and `concorde task show`, which
a Claude Code session asks. When `task open` fails, `prepare` stops with `command_failed` as for
every other setup step.

SWE-bench is included as external material: its harness names the Python projects it draws from,
such as `psf/requests` and `pallets/flask`, existing codebases of known size and quality to test on.
