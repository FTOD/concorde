# End-to-end testing

## Purpose

End-to-end testing is how the Concorde project tests itself on real codebases with real agents. It
takes a project from the Python repositories SWE-bench draws from, sets it up exactly as a user
would, runs a workflow in it with real workers, and lets the developer watch every run. It exists
for the people developing Concorde: nothing of it is installed into a project, and a Concorde user
never meets it. Its second job is to keep apart the problems that only testing conditions cause,
such as a headless main session or an untrusted scratch project, from the problems a user would
meet, so that the first are solved here rather than in what users get. Three children carry parts of
it: [Headless sessions](sessions/module.md) drives any real headless main session,
[SWE-bench cases](cases/module.md) repairs and grades cases worked on real issues, and
[Dogfood scenarios](dogfood/module.md) tests a
[develop install](../glossary.json#concept.develop-install)'s
[main agent](../glossary.json#concept.main-agent) against a known
[Concorde defect](../glossary.json#concept.concorde-defect).

## Usage

The tool is one command of this checkout, `scripts/e2e/e2e.py`, printing one JSON object per
command and `{"error": …}` with the failed command and its output otherwise:

```text
python3 scripts/e2e/e2e.py repos
python3 scripts/e2e/e2e.py prepare <owner/name> --rev <tag|branch|commit> [--name <dir>] [--python <interpreter>] [--task <task>] [--any] [--pi]
python3 scripts/e2e/e2e.py trust <project>…
python3 scripts/e2e/e2e.py run <project> [--via claude|driver] [--workflow brownfield] [--task <task>] [--module <id>] [--mode no-ask|interactive] [--retry <key>]… [--restart <key>=<label>]…
python3 scripts/e2e/e2e.py watch <project>
python3 scripts/e2e/e2e.py owners <project> [--task t1] [--claude 2] [--pi 2] [--claude-model <model>] [--pi-model <model>] [--grace 20]
```

Its children add `session` ([Headless sessions](sessions/module.md)), `repair-specs` and `grade`
([SWE-bench cases](cases/module.md)) and `dogfood` ([Dogfood scenarios](dogfood/module.md)).

**A worked example.** The developer prepares `psf/requests` at its tag `v2.31.0`, runs the
[brownfield workflow](../glossary.json#concept.brownfield-workflow) in it as a headless run and,
from another terminal while it runs or afterwards, watches its runs. Shortened, the three commands
print:

```text
$ python3 scripts/e2e/e2e.py prepare psf/requests --rev v2.31.0
{"project": "/tmp/concorde-e2e/requests", "repository": "psf/requests", "revision": "v2.31.0",
 "task": "adopt", "worktree": "/tmp/concorde-e2e/requests/.claude/worktrees/adopt"}

$ python3 scripts/e2e/e2e.py run /tmp/concorde-e2e/requests --via claude
{"workflow": "brownfield", "workspace": "adopt", "mode": "no-ask", "status": "ok",
 "steps": [{"key": "survey", "status": "ok", …}, {"key": "scaffold", …}, …,
           {"key": "delivery", "status": "ok", …}],
 "decisions": […], "open_questions": […], "problems": […], …}

$ python3 scripts/e2e/e2e.py watch /tmp/concorde-e2e/requests
{"runs": [{"run": "r-…-survey-…", "workspace": "adopt", "phase": "finished", "status": "ok", …}, …],
 "workflows": {"adopt": [{"key": "survey", "run": "r-…-survey-…", "superseded": false}, …]}}
```

The project is then a throwaway: the developer reads its Specs, runs and records, and removes the
directory, or prepares the next one under another `--name`. The sections below explain each
command.

<a id="concept.test-project"></a>

**Preparing a [test project](../glossary.json#concept.test-project).** `repos` lists the
repositories SWE-bench's harness names, read from the vendored `references/swe-bench/`.
`prepare psf/requests --rev v2.31.0` fetches that revision, a tag, a branch or a commit, without
earlier history into the **end-to-end root**, under
`--name` or the repository's name, checks it out as a `main` branch, installs Concorde from this
checkout without `d2`, initializes it, commits and opens a task bound to the root
[Module](../glossary.json#concept.module), which makes a **test project**. The task is `--task`
(default `adopt`), and `--python` records the project's interpreter, which its
[configured checks](../glossary.json#concept.configured-check) run for `{python}`. `--pi` also
installs Concorde's pi extension, which a pi main session in the project needs. It refuses a
repository SWE-bench does not name unless `--any` is given, and a project directory that already
exists. The end-to-end root is `CONCORDE_E2E_ROOT` when it is set, and otherwise `concorde-e2e` in
the system's temporary directory (`/tmp/concorde-e2e` on Linux), never the developer's home: test
projects are throwaway, and Claude Code keeps no trust for the home directory itself.

Each of `prepare`'s choices has its reason:

- It fetches only the revision, because SWE-bench's base commits are commits, which
  `git clone --branch` does not accept, and nothing in a test project needs earlier history.
- It checks the revision out on a branch, because tasks are merged into the project's primary
  branch, and a merge refuses a primary worktree on a detached `HEAD`; the branch is named `main`
  because [SWE-bench cases](cases/module.md)' `grade` grades `main` unless `--ref` names another.
- It installs without `d2`, which only renders the Specs' diagrams for a docsite a test project
  never publishes, and which every preparation would otherwise download again.
- It commits the installed and initialized project before it opens the task, because the task's
  branch starts from the committed head, and a merge refuses a primary worktree with uncommitted
  paths.
- It binds the task to the root Module, because the brownfield workflow a test project first runs
  describes the whole project from it.

A step that fails, such as the fetch, the install, `init` or `task open`, stops `prepare` with
`command_failed`, naming the command, its exit status and its output. `prepare` removes nothing it
made: the partial project directory is left for the developer to read, and a later `prepare` under
the same name refuses it with `project_exists` until the developer removes it.

**Trusting test projects.** Claude Code applies a project's `.claude/settings.json` allow rules,
which the installer writes for its workflows, only once that exact repository is trusted: trust is
keyed on the git repository root, a parent folder's trust does not count, and a
[headless session](../glossary.json#concept.headless-session) never shows the trust dialog. `trust`
marks each named project's repository root trusted in Claude Code's configuration, `~/.claude.json`
(or under `CLAUDE_CONFIG_DIR`), after backing the file up once. It changes the developer's own
configuration, so the developer runs it; a headless run does not need it.

**Running a workflow.** `run` runs a workflow to its end in the worktree of the test project's
task `--task` (default `adopt`), whose
[workspace binding](../glossary.json#concept.workspace-binding) the workflow and
every run it starts work on, so neither the workflow's arguments nor any command names the task. It
prints the [workflow result](../glossary.json#concept.workflow-result) the
workflow saved last in its [workflow record](../glossary.json#concept.workflow-record),
under `.concorde/runs/workflows/<task>/` of the project, and logs the session under
`.concorde/runs/e2e/`:

- A **headless run** (`--via claude`) runs, as a
  [headless session](../glossary.json#concept.headless-session) kept under
  `.concorde/runs/e2e/<task>-claude/`, a session started in the task's worktree that works there as
  the task's [task session](../glossary.json#concept.task-session), since running a task's
  workflow is its task session's work and the [main agent](../glossary.json#concept.main-agent)
  never works inside a task worktree, and is asked to run the installed workflow there and report
  with `concorde workflow report`. Two testing
  conditions are handled for it: `claude -p` otherwise stops a background workflow after ten idle
  minutes, so the session keeps `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`; and an untrusted project
  ignores its allow rules, so the workflow and its step commands are granted with `--allowedTools`.
- A **driver run** (`--via driver`) runs the rendered pi
  script of the workflow from the runtime the installer places under `.concorde/framework/`, which
  every install carries with or without `--pi`, and refuses with `script_missing` when that script
  is absent. It runs the script under the stand-in runtime of the Workflows tests, whose
  [step agents](../glossary.json#concept.step-agent) execute the real
  `concorde workflow step --stdin` and `concorde workflow report --stdin` in the task's worktree, so
  every [workflow step](../glossary.json#concept.workflow-step) is a real one. It has no
  main-session model between steps, while its Operations still launch real workers, so it tests
  Concorde's side without the client runtime.

`--workflow` names the workflow (default `brownfield`), `--module` the Module it works on (default
the root Module, `module.project`) and `--mode` its
[workflow mode](../glossary.json#concept.workflow-mode) (default `no-ask`); an `interactive` run
ends at its first [decision point](../glossary.json#concept.decision-point), and `run` passes no
answers to continue it. `--retry <key>` and `--restart <key>=<label>` become the workflow's own
`retry` list and `restart` map, for a run that continues a task.

A workflow result whose status is not `ok` is printed like any other. `run` fails instead with
`run_failed` when the headless session ends `exited` or `no_session`, naming its `session.json`,
or when the driver exits with a non-zero status, with its standard error and log; with the
session's own error, such as `wait_exceeded`, when the session fails, naming its `session.json`;
and with `no_result` when the run saved no workflow result of its own. `run` counts the saved results
of the workflow record before it starts and takes only a result saved since: a record that holds no
more saved results after the run than before it, or whose newest saved result is missing, fails with
`no_result` naming both counts or the missing file, so a result an earlier run of the task saved is
never printed as this run's ([requirements](requirements.md#req.e2e.own-result)).

**Watching.** `watch` lists every run of the project's
[run store](../glossary.json#concept.run-store) with its workspace, phase, step and outcome, and,
from each workspace's workflow record, its [workflow steps](../glossary.json#concept.workflow-step)
with their runs and whether they were superseded.

<a id="owners-case"></a>

**The owners case.** `owners` checks, with real sessions, the promise of
[Main session](../coordination/main-session/module.md#owners) that a run wakes only its owner
while every other main session may see it: it keeps several main sessions running at once in
the test project's primary worktree, `--claude` Claude Code and `--pi` pi sessions, two of each by
default and at least two in all, each a live session of [Headless
sessions](sessions/module.md) whose wakes are its own program's, and plays three phases on the
project's task `--task` (default `t1`), which must have a worktree:

1. **unowned**: the case itself starts `concorde task-validation` in the task worktree, a run of
   nobody's tool;
2. **owned by pi**, with a pi session: the first pi session starts `task-validation` of the task
   with its `concorde_run` tool;
3. **owned by Claude Code**, with a Claude Code session: the first Claude Code session starts it
   in background Bash.

Each run is started with `--wait` while the case holds the task's
[workspace lock](../glossary.json#concept.workspace-lock), which it releases only once every pi
session's [run view](../glossary.json#concept.run-view) shows the run running in its status bar, so
that the run outlives its launch and its end reaches the owner as a wake, never as the launching
tool's own answer. When the run has written its result and the owner has been woken, and after
`--grace` seconds more, the phase is judged over the time since the owner's launching turn ended
(the phase's start for the unowned run), in which the case prompts no session: the owner must have
begun a turn or received a notification, Claude Code's `task_notification` or the run view's
`concorde-run` message, and no other session may have done either. Then every session that does
not own the run shows that it sees it: a pi session's `/concorde` names the run as ended, which
begins no turn, after its status bar showed it running; a Claude Code session, into which nothing is
pushed, is asked to run `concorde task show <task>` and finds the run with the status of its result
([requirements](requirements.md#req.e2e.owners-case)). The case prints, and keeps as
`owners.json` beside every session's events under `.concorde/runs/e2e/owners/<time>/`, the
sessions, every phase with its owner, run, status, each session's verdict and what each other
session saw, and its outcome: `passed`, or `failed` with every problem, such as `pi-2 was woken by
a run it does not own`. A contradicted promise is the case's verdict, not an error; a session that
cannot start or refuses its first prompt, such as a pi without a usable model, a missing task
(`no_task`), a project without the pi extension (`pi_not_installed`) or a step that does not happen
in time (`live_timeout`) stops it with an error. The case spends real model turns and is run by
hand, like every end-to-end run.

## Design

End-to-end runs are not in the test suite. They clone from the network, spend real model tokens
and take tens of minutes, and their outcome depends on the model. The suite keeps the
deterministic acceptance test, which runs the same workflow with fake workers; this Module is
what the developer runs by hand, after a change to Adoption, Workflows or the worker harness, and
whose findings become ordinary tasks.

The headless run and the driver run answer different questions. The headless run is what a user's
task session does, Claude Code's workflow runtime and its step agents included. The driver run
removes the session's model and the client runtime from between the steps, but its
Operations still launch real workers, so a failure there lies on Concorde's side, in its commands,
Operations or workers. When a headless run fails, a driver run of the same task with `--retry` for
the failed step's key runs that step again without the client runtime, reusing the steps that
succeeded, and so points to whether Concorde or the client runtime is at fault; without `--retry`
it would only find the failed run recorded. Since the workers are real, one such comparison is
evidence, not proof.

The driver run does not have a runtime of its own: it runs the JavaScript sandbox of the Workflows
tests, `tests/concorde/workflows/run_script.mjs`, with step agents that execute the real commands.
This couples End-to-end testing to a test file of Workflows, and the coupling is accepted: a second
stand-in runtime would have to follow every change of the rendered scripts' adapters that the
Workflows tests already follow, and could drift from them. The file stays Workflows' and is listed
by both Modules, so a change to it concerns the driver run too.

The testing conditions stay here. A user's main session is interactive and its project trusted,
so neither the wait ceiling nor the trust keying reaches the user-facing guidance; this Module
handles both for tests, and changes nothing a user gets.

<a id="realization.e2e.tool"></a>

The **End-to-end tool** realization is `scripts/e2e/e2e.py`: preparing, trusting, running and
watching test projects, and the command line of its children's `session`, `repair-specs`, `grade`
and `dogfood` commands; `scripts/e2e/common.py` holds what the tools share, the checkout, the
end-to-end root, the error type, running a command and cloning a revision. It also lists
`tests/concorde/workflows/run_script.mjs`, the JavaScript sandbox of the Workflows tests that
stands in for the client runtime and that a driver run runs, as a file it shares with Workflows.

<a id="realization.e2e.tests"></a>

The **End-to-end tool tests**, `tests/concorde/e2e/test_e2e.py`, check the tool's pure parts, the
repository list, trust, the headless command, cloning a revision and grading, on local
repositories only, without the network or agents, verifying the
[requirements](requirements.md) and [scenarios](scenarios.md).

<a id="realization.e2e.owners"></a>

The **owners case** is `scripts/e2e/owners.py`: the phases, holding the workspace lock, judging
who was woken and asking the others what they see. Its tests,
`tests/concorde/e2e/test_owners.py`, run the whole case with stand-ins for `claude`, `pi` and
`concorde` that speak the live sessions' protocols, including a pi stand-in that wakes for every
run, which must fail the case.

### The children

Three children carry parts of End-to-end testing. Each reaches a different part of Concorde: a
headless session wakes on the runs of Execution, a case is set up through Distribution, and a
dogfood scenario drives headless sessions against a develop install that Dogfooding describes. The
parent itself sets test projects up through Distribution and runs the workflows they execute.

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
e2e -> workflows
e2e -> execution
e2e -> distribution
e2e.sessions -> execution
e2e.cases -> distribution
e2e.dogfood -> distribution
e2e.dogfood -> dogfooding
```

<a id="contains-sessions"></a>

**Headless sessions** drives a real headless Claude Code or pi main session: it grants the session
its tools, tells it the conditions of running headless, wakes it when a run or a
[session round](../glossary.json#concept.session-round) it left behind ends and keeps every round's
log. The headless runs of workflows are headless sessions, and so are
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

### Around it

End-to-end testing relies on three providers to set a test project up, run it and follow it.

<a id="uses-workflows"></a>

**Workflows** provides the workflows a test project runs, their rendered scripts and the stand-in
runtime of its tests that a driver run reuses, the
[workflow result](../glossary.json#concept.workflow-result) a run ends with, and
the [workflow record](../glossary.json#concept.workflow-record) of each workspace,
where `run` finds the latest saved result and `watch` the steps. End-to-end testing relies on the
record listing the saved results in order and each step with its run.

<a id="uses-main-session"></a>

**Main session** makes the promise the owners case checks, and provides what the case observes of
a pi main session: the [run view](../glossary.json#concept.run-view)'s `concorde_run` tool, its
status bar under the key `concorde`, its `/concorde` listing and its `concorde-run` message.

<a id="uses-tasks"></a>

**Tasks** provides the [task record](../glossary.json#concept.task-record), whose worktree the
owners case runs its unowned run in, and `concorde task show`, which a Claude Code session asks.

<a id="uses-execution"></a>

**Execution** runs every workflow step, [Operation](../glossary.json#concept.operation) and
[execution command](../glossary.json#concept.execution-command) of a test project in the workspace
its task worktree is bound as: Tasks writes that
[workspace binding](../glossary.json#concept.workspace-binding) when `prepare` opens the task, and
End-to-end testing never writes it. `watch` reads the run store's
[run progress files](../glossary.json#concept.run-progress-file) for each run's workspace, phase,
step and status, relying on them to name those fields. A run without a run progress file, whether its
runner has not written it yet or died before writing it, is left out of the list rather than
failing `watch`, which the developer may run at any moment; a run left out for the second reason
stays out.

<a id="uses-distribution"></a>

**Distribution** provides the installer and the `concorde` command that set a test project up the
way a user's project is set up; a test project always runs the Concorde of this checkout. When the
installer, `concorde init` or `concorde task open` fails, `prepare` stops with `command_failed`
naming that command, its exit status and its output, and leaves the partial project directory as it
is (see Preparing a test project); End-to-end testing never repairs a failed setup, since the
failure is the finding.

SWE-bench is included as external material: its harness names the Python projects it draws from,
such as `psf/requests` and `pallets/flask`, existing codebases of known size and quality to test on.
