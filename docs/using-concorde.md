# Using Concorde

This guide is for developers who want to use Concorde in their own project. It covers installing
Concorde, writing the first Spec, working with the main agent, carrying one change from an idea to
a merge, and reading what Concorde reports back. It describes Concorde 9 with
[Spec Protocol 13](https://ftod.github.io/concorde/protocol) with Claude Code as the client for
the main agent and its task sessions, and [pi](https://github.com/earendil-works/pi) or Claude Code
for the workers.

In the commands below, `concorde` stands for your project's `.concorde/bin/concorde`.

## What Concorde does for you

Concorde's **Specs** harness your agents. A Spec explains what each Module of your project is
responsible for, how it is designed, which precise promises it makes and which files realize it.
That division of responsibility is also each agent's harness: from the Specs Concorde computes
exactly what an AI task is given as context and may read and write, and runs headless Claude Code
or pi workers inside that boundary.

**You, the developer**, decide the direction and answer the questions that have a major impact.
Below you, the work passes down five levels in two halves. The first two, **coordination**, are
where work is decided and split into tasks. The last three, **execution**, do the work inside one
task's worktree, which Concorde binds to the task as a **workspace**; execution never sees the task
itself, only that binding. Agents sit at both ends, and programs run between them:

| Level           | Kind    | What it is                                                                                                                                                                                                                                |
| --------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Main session | agent   | Your own Claude Code session in the primary checkout, the **main agent**. It discusses the project with you, splits work into tasks and merges what was delivered.                                                                        |
| 2. Task         | agent   | One task's branch and worktree, worked by a **task session** the main agent starts for it; the main agent never works inside a task itself.                                                                                               |
| 3. Workflow     | program | A procedure for tasks that follow a known path, such as `brownfield`; it orders the runs in the task's worktree and stops where a decision is needed.                                                                                     |
| 4. Run          | program | One bounded job with one result: an **Operation**, which computes the grant, launches AI workers and runs your checks itself, or an **execution command** such as `task-validation` or `delivery`, a deterministic step without a worker. |
| 5. Worker       | agent   | A **worker** is a headless `claude -p` or `pi -p` process for one bounded job, under a **grant** computed from the Specs.                                                                                                                 |

Calls only go down: a worker never touches Git, runs an Operation or starts an agent, a run never
starts another run, and nothing in the execution half reads or writes a task record. Results and
errors come back up the same levels.

### Three kinds of documents

A Concorde project has three kinds of documents, each for a different reader:

| Kind                         | Reader                                                                        | Rules                                                                             |
| ---------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Module documents**         | Developers who want to understand the architecture                            | Written under the Spec Protocol; they become agent context and define boundaries. |
| **Implementation documents** | Developers and agents that need precise requirements, scenarios and contracts | Written under the Spec Protocol; same role.                                       |
| **User documents**           | People who use the project, like this guide                                   | No structural rules; never agent context; the docsite's first tab and home page.  |

## Before you start

You need:

- a Git repository for your project, with at least one commit;
- Python 3.11 or later, to build Concorde and run its installer;
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which creates Concorde's own
  Python environment and installs its dependencies;
- [Claude Code](https://docs.claude.com/en/docs/claude-code), installed and logged in, for the main
  agent and its task sessions;
- for workers that run on pi, [pi](https://github.com/earendil-works/pi) with a configured model,
  Node.js with npm, `rg` (ripgrep), `fd` and `socat`;
- Linux with a root-owned [bubblewrap](https://github.com/containers/bubblewrap) (`bwrap`), which
  backs the command sandbox of workers and runs your checks read-only; Concorde refuses a
  check it cannot sandbox rather than fall back to an unconfined process;
- Node.js 20 or later only if you want to publish your Specs as a documentation site.

## Install Concorde into a project

Build Concorde from a checkout and install it into your project:

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
python3 scripts/install-concorde.py /absolute/path/to/project
```

The installer places:

- the Concorde runtime under `.concorde/framework/`, with its own Python environment (a venv
  under `.concorde/framework/python/` that uv creates on a Python version Concorde supports: one
  already on your machine, or a Python uv downloads for it when you have none), and the
  `concorde` command as `.concorde/bin/concorde`, which always runs in that environment, never in
  your project's Python environment, even when your project's venv is activated;
- a copy of the Spec Protocol under `.concorde/protocol/`, so the rules your Specs follow travel
  with your project;
- the main agent's guidance, as the Claude Code skill `.claude/skills/concorde/SKILL.md` and a short
  block between `<!-- concorde:start -->` and `<!-- concorde:end -->` in your `CLAUDE.md` (the
  rest of the file is left untouched);
- the project MCP server, registered as `concorde` in your `.mcp.json` (other servers there are
  kept), which gives Claude Code sessions your tasks, traces and locks as tools;
- the [`d2`](https://github.com/d2lang/d2) program that draws your Specs' diagrams, as
  `.concorde/tools/d2`, at a pinned release whose checksum it verifies (`--without-d2` skips it);
- the sandbox engine pi workers run their commands in, `@anthropic-ai/sandbox-runtime`, under
  `.concorde/tools/pi-runtime/`, installed with `npm ci --ignore-scripts` from the lockfile
  Concorde ships, so you get exactly the versions it was tested with. Workers run on pi unless you
  choose Claude Code for them, so this needs npm;
  `--without-pi-runtime` skips it when every worker will run on Claude Code;
- ignore rules for the directories Concorde writes at run time, and a receipt
  `.concorde/install.json`.

The installer checks that uv, and npm when it installs the pi runtime, are on your `PATH` before it
writes anything into your project; when one is missing it refuses and says which.

The installer never writes your Specs or your registry, except the Concorde installation
realization, which it keeps in step with the files it installs, and writes your project
configuration only to bind a new Protocol copy when you update. Nor does it write the worker
configuration `.concorde/workers.json`, without which no worker runs: which models your workers
use is your choice, made before the first Operation runs, as
[Choose the worker models](#choose-the-worker-models) explains.

To update Concorde, pull the checkout and build it again, then run `concorde update` in your
project (`--from <checkout>` if the checkout moved). It installs the new version the way the first
install did, binds the new Protocol copy in `.concorde/config.json` (read what changed in
`.concorde/protocol/`), and lists your open tasks: merge your primary branch into each, since
their worktrees keep the previous Protocol copy. Your project is then **Concorde unvalidated**:
`concorde spec-validation` reports it as an error, and nothing merges, until you have repaired what the
new version finds and a validation passes. That mark comes only from an update; your own changes
never set it. An update also waits for Concorde to be idle: while an Operation or an execution command is still
running in your project, it refuses and names what runs.

### Use Concorde while developing it

If you also work on Concorde itself, install it with `--develop` from your Concorde checkout's
primary worktree, on its branch and with everything committed:

```bash
python3 scripts/install-concorde.py /absolute/path/to/project --develop
```

Your project then runs that checkout's Concorde, and its main agent watches Concorde while it works:
it never changes Concorde from your project, and when something goes wrong that would go wrong in
any project, it writes a defect report under `.concorde/runs/defects/` and tells you. Take the
report to a session in your Concorde checkout, which records it as an Issue there and fixes it in a
task of its own; once that task is merged, run `concorde update` in your project. When a boundary
stops work, the main agent first decides whether the work overreaches, your Specs draw the
boundary wrongly, or Concorde implements or designs it wrongly, and only the last two become
defect reports.

## Write your first Spec

Initialization proposes the first Spec and applies exactly what it proposed, so you can inspect
every file before anything is written:

```bash
cd /absolute/path/to/project
.concorde/bin/concorde init --propose --name "My project" > /tmp/proposal.json
jq .result /tmp/proposal.json > /tmp/accepted.json   # read it first
.concorde/bin/concorde init --apply --proposal /tmp/accepted.json
.concorde/bin/concorde spec-validation
```

Keep the proposal file outside the project. Applying it writes:

- `.concorde/config.json`, the project configuration: the Protocol binding and your project's
  interpreter;
- `.concorde/specs.json`, the **registry** that lists every Module;
- `specs/project/module.md` with its metadata `module.md.json`, the root Module `module.project`.

The first Spec is deliberately honest and small. From here you describe your project as Modules.
Every Module's entry document `module.md` is its design, written for a developer who wants to
understand the Module quickly. The Protocol requires no section of it, but recommends this order:

1. **Purpose**: what the Module is for, in plain prose.
2. **Core concepts**: the ideas a reader needs first, the Module's own terms explained and the
   project's other terms linked to the glossary.
3. **Overview**: `d2` diagrams of its main structure, functions and flows, with short prose. A
   process, even one among several Modules, is drawn as a workflow, with a lane per participant
   when that helps.
4. **Details**: its parts and how they work together, how it works with the Modules it uses and
   those that use it, its entry points and errors, and the reasons for its choices.

Precise requirements, scenarios and contracts go into the Module's implementation documents. The
[Protocol overview](https://ftod.github.io/concorde/protocol) and its
[Module template](https://ftod.github.io/concorde/protocol/templates/module) show the exact format;
[Concorde's own Specs](https://ftod.github.io/concorde/specs/concorde/module) are a complete,
working example.

You do not have to write every Spec by hand. Once the root exists, you can ask the main agent to
propose Modules for your project and let `specify` tasks write them (see below). Whoever writes
them, two commands keep Specs consistent:

```bash
concorde spec-validation     # every structural rule of the Protocol
concorde registry --write    # refresh the registry after a Module's `module` block changed
```

### A project whose code already exists

Concorde normally works Spec first: a promise is written, then realized. When you adopt Concorde
for a project that already has code, the **brownfield workflow** describes that code in Specs
once, so that from then on you can work Spec first. After initialization, ask the main agent to
run it. It opens a task bound to the root Module and starts its task session, which runs the
workflow inside that task's worktree, one step after another:

1. `survey`: a worker reads the code and proposes child Modules, which paths each binds, and the
   test and lint commands it found;
2. `scaffold`: an execution command, without any worker, creates those Modules as honest stubs
   and moves their paths out of the root;
3. `code_to_spec` for each Module: a worker reads its code and writes its Spec, and names the
   existing tests each scenario comes from; Concorde then marks those tests with a small
   `verifies` decorator (defined in the test file itself, so your tests never import Concorde),
   the only change it makes outside your Specs;
4. `spec_review`, `task-validation` and `delivery`.

The workers describe behaviour as it is. When they cannot tell whether something is intended,
such as an error that is silently ignored, they write no promise about it and report an **open
question** instead. Choose one of two modes when the workflow starts:

- **interactive**: the workflow stops at every open question and every choice about how the
  project splits; the task session reports all of them to the main agent together, the main agent
  asks you about them at once, and the workflow continues with your answers;
- **no-ask**: the workflow takes those choices itself and reports every choice, open question and
  problem at the end, for you to review before the task is merged.

The test and lint commands the survey found are reported, never configured automatically: add
the ones you trust to your checks yourself (see below).

## Configure your checks

**Checks** are your project's own commands, such as a test suite or a linter, each assigned to one
Module. Concorde runs them itself, never the worker, and records each result as evidence.
Each Module's checks have a file of their own, named after the Module: declare the checks of
`module.payments` in `.concorde/checks/module.payments.json`:

```json
{
  "checks": [
    {
      "id": "check.payments.tests",
      "argv": [
        "{python}",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/payments"
      ],
      "timeout_seconds": 300,
      "inputs": ["pyproject.toml", "src/payments", "tests/payments"]
    }
  ]
}
```

A test answers whether the code is right; a check answers what one command produced on exactly
this input, and whether that result can be trusted: Concorde runs it where it cannot change your
files and refuses a result when its inputs changed while it ran.

`{python}` is your project's own interpreter, which `.concorde/config.json` names in `python`.
`concorde init` records `.venv/bin/python` (or `venv/bin/python`) when your project has one, or the
interpreter you name with `init --python`. A relative path is looked up in the worktree the check
runs in and then in your primary checkout, so task worktrees use your primary checkout's
environment. Concorde itself never runs in your project's environment, and your checks never run
in Concorde's. A check may set its own variables in `env`, for example
`"env": {"PYTHONPATH": "src"}` for code under `src/`: the check then tests the code of the worktree
it runs in, not a copy installed in your environment.

Which tests run when is up to you. A check runs whenever one of its Module's files changes, and
also when a Module it uses changes. Two forms keep that affordable:

- **Selective checks.** Put `{tests}` in `argv`, for example
  `["{python}", "-m", "pytest", "-p", "no:cacheprovider", "{tests}"]`. Concorde replaces it with
  the tests that declare they verify a scenario of the changed Modules (with `@verifies`), wherever
  those test files live, and skips the check when there are none. A test may verify scenarios of
  several Modules; it runs when any of them changes.
- **Readiness checks.** Add `"when": "readiness"` to a full suite: it runs only when `validate` and
  `delivery` decide whether a task is ready, not in every `implement` round.

`inputs` are the paths the result depends on, without a trailing `/`; if they change while the
check runs, its result is refused as stale. Checks run in a sandbox in which the whole filesystem is read-only except a fresh
scratch directory, named by `TMPDIR`, `XDG_CACHE_HOME`, `CONCORDE_CHECK_TMPDIR` and
`CONCORDE_CHECK_REPORT_DIR`. A check that writes caches or reports into the project fails and must
be pointed at the scratch; a tool that rewrites sources, such as a formatter in fix mode, is not a
check.

## Work with the main agent

Open Claude Code in your project's primary checkout. The installed skill makes that session
the main agent; you talk to it as usual. Start it with the project MCP server as a channel, so
that the main agent can be woken when something it waits for happens:

```bash
claude --dangerously-load-development-channels server:concorde
```

Claude Code asks you once to confirm the flag, and asks, the first time, whether to use the
`concorde` server from `.mcp.json`. Channels are a research preview of Claude Code: they need you
to be logged in with claude.ai or a Console API key, and a Team or Enterprise organization must
have enabled them. Without a channel everything still works: the server's tools answer as usual,
and instead of waking the main agent itself it gives the main agent a `concorde task wait` command
that it runs in background Bash, which wakes it when the command returns. Task sessions always
work this way: Claude Code does not wake a background session with channel events.

- **Discuss first.** Ask about the project, agree the direction and the large plan. The main agent
  answers from the Specs.
- **Let it decide the ordinary things.** Names, internal structure, the order of tasks, rerunning an
  Operation with a clearer brief, splitting a task: the main agent decides these itself, writes
  each decision and its reason into the task's decision log and reports them at the end.
- **Expect questions only when they matter, and all at once.** It asks you before acting when a
  decision changes what a Module promises or the project's direction, contradicts an earlier
  decision of yours, discards work, cannot be undone by an ordinary revert, touches security or
  credentials, or needs more resources than you allowed. A task never asks you itself: its session
  reports every decision it needs to the main agent together, and the main agent asks you about
  all those it may not settle at once.
- **Approve small changes.** A typo, a one-line fix or a wording correction may be made by the main
  agent directly in your primary checkout, but only after it told you what it would change and you
  approved it; everything else is a task.
- **Delivered work is merged without asking.** When a task has been delivered, the main agent merges
  its branch and reports what it merged.

You can run every command below yourself as well; the main agent uses exactly the same ones.

### Follow runs

The main agent starts Operations and execution commands in background Bash, so it keeps talking
with you while they run, and it is woken with the result when a run it started ends. Only the
session that started a run is woken: runs of other main sessions, of task sessions and of commands
run by hand wake nobody. See how any task stands, including another session's, with
`concorde task show <task>`.

The project MCP server gives the main agent, and every task session, the same commands as tools:
`task_list`, `task_show`, `trace_show`, `run_result`, `workflow_report` and `locks` to read,
`task_open`, `task_escalate` and `task_close` to change tasks, `task_merge` to merge, and
`register_wait` to be woken when a task is delivered or closed, a run ends or a lock is released.
It never waits for a lock: when another session holds one it needs, it answers at once with who
holds it (the command, process, start time, Claude Code session and task), and when it gets the
locks for a merge it hands them to the merge process it starts, so a lock is always released when
the work holding it ends. You can wait the same way yourself with
`concorde task wait <task> --until delivered`, `concorde task wait --run <run-id>` or
`concorde task wait --lock merge`, each of which returns when that happens.

### Choose the worker models

Workers run on pi unless you put some of them on Claude Code. Which
model and reasoning level each worker uses is yours to choose, for every worker or for one worker
by its id, such as a cheaper model for `implement`'s `worker` or three different models for
`spec_panel`'s `reviewer1`, `reviewer2` and `reviewer3`; ask the main agent to change the worker
models, or edit the file yourself.

The choice lives in `.concorde/workers.json`, which Git tracks like your code, and nothing else
decides it: Concorde never takes a worker's model or reasoning level from your own pi or Claude
Code settings. No worker runs without the file, and neither the installer nor `concorde init`
writes it, since the models are yours to choose. When your project has none, the main agent asks
you which models workers may use and which is the default, then writes the file and commits it on
its own on your primary branch before the first Operation runs.

The file names each model by a **project model name** of your choosing that depends on no
installation, such as `gpt-6-astra` or `claude-opus-5-5` (letters, digits, `.`, `_` and `-`). The id
a program takes, such as `local-openai/gpt-6-astra` on pi, is defined by your own pi or Claude Code
configuration, so it never goes into the tracked file. It lists in `enabled_models` every model a
worker may run on, each `{}` or with a `reasoning` level of its own. The entries then choose among
them: a `default` for every worker, and under `operations` an Operation's `default` and one entry
per worker id under its `workers`. Each entry may set a `backend` (`pi` or `claude`), a `model` and a
`reasoning` level, and the most specific entry that sets a field wins, a backend like any other
field. A worker takes the level set by the entry that chose its model or a more specific one,
otherwise its model's own level in `enabled_models`, otherwise one a less specific entry sets,
otherwise its program's own default. Leave a field out to inherit it. The same file holds the
limits of every worker launch and the paths workers may read besides their grant:

```json
{
  "schema_version": 2,
  "enabled_models": {
    "claude-sonnet-5": { "reasoning": "medium" },
    "claude-opus-5-5": { "reasoning": "high" },
    "gpt-6-astra": {},
    "opus": {}
  },
  "default": { "model": "claude-sonnet-5" },
  "operations": {
    "spec_panel": {
      "workers": {
        "reviewer1": { "model": "claude-opus-5-5" },
        "reviewer2": { "model": "gpt-6-astra", "reasoning": "high" },
        "reviewer3": { "model": "gpt-6-astra" },
        "chair": { "backend": "claude", "model": "opus" }
      }
    }
  },
  "limits": { "timeout_seconds": 1800, "max_turns": 200, "rounds": 3 },
  "runtime": [".venv", "node_modules"]
}
```

Here every worker runs on pi with `claude-sonnet-5` at that model's own `medium`, except
`spec_panel`'s: `reviewer1` on `claude-opus-5-5` at its own `high`, `reviewer2` on `gpt-6-astra` at
the `high` of its entry, `reviewer3` on the same model at pi's default level, and the `chair` on
Claude Code with the model the project calls `opus`. An entry that only puts a worker on Claude
Code keeps the model and level it would otherwise inherit.

Your **model map** tells your machine how to reach those models: `~/.config/concorde/models.json`
(or `concorde/models.json` of `$XDG_CONFIG_HOME` when you set it, or the file the environment
variable `CONCORDE_MODEL_MAP` names by its absolute path). It is yours, outside every repository and
never committed, and one map serves all your projects, their tasks and test projects. It gives each
project model name its local id on `pi`, on `claude` or on both:

```json
{
  "schema_version": 1,
  "models": {
    "claude-sonnet-5": {
      "pi": "anthropic/claude-sonnet-5",
      "claude": "claude-sonnet-5"
    },
    "claude-opus-5-5": {
      "pi": "anthropic/claude-opus-5-5",
      "claude": "claude-opus-5-5"
    },
    "gpt-6-astra": { "pi": "local-openai/gpt-6-astra" },
    "opus": { "claude": "opus" }
  }
}
```

When your pi configuration renames a model, only the map changes; the project's choices stay as they
are. A worker whose model the map does not give an id on its program is refused; Concorde never
passes the project model name to the program instead.

Because the file is tracked, a task carries the configuration of the commit it started from. A
change meant for future tasks is committed on its own on your primary branch; the main agent does
that directly, without a task. A task may change its own models while it works, and that change
arrives with the task when it merges. Runs outside a task use the committed file, so commit a change
before such a run is to use it.

For suggestions, `python3 scripts/available_models.py --backend pi` (or `--backend claude`) lists
the models pi has credentials for and Claude Code's aliases, each with the project model names your
map already gives it, and for pi the map's ids pi no longer lists; any other name may be written
too, as long as `enabled_models` lists it and your map gives it an id.

The whole file is checked every time a worker launches. When a worker cannot be configured, its
Operation ends `failed` with `worker_model_unavailable`, and its error chain says why and how to
repair the file or your model map:

- `config_missing`: the worktree has no `.concorde/workers.json`;
- `model_not_enabled`: an entry names a model that `enabled_models` does not list, which refuses
  every worker until you enable the model or change the entry;
- `model_unresolved`: no entry names a model for the worker, which never falls back to its
  program's default model, so give the `default` a model;
- `config_invalid`: anything else malformed, such as a missing or empty `enabled_models`, an
  unknown Operation or worker id, a model named by a program's id such as `local-openai/gpt-6`
  rather than a project model name, a file of the earlier `schema_version` 1, or a reasoning level
  the worker's program does not know;
- `backend_missing`: the worker's program is not installed; it never runs on the other one
  instead;
- `model_map_missing`: your machine has no model map;
- `model_map_invalid`: the model map is malformed, such as a model without an id or an id keyed by
  another program than `pi` or `claude`;
- `model_unmapped`: the map gives the worker's model no id on the worker's program; the error names
  the entry to add.

The reasoning level is passed as `--effort` to Claude Code and as `--thinking` to pi. A pi worker
uses copies of your pi `auth.json` and `models.json` and nothing else from your pi configuration.

### Operations outside a task

`understand`, `survey`, `spec_review`, `spec_panel` and `code_review` (with `--base`) also run
**unbound**, in a worktree that is no task's workspace, such as your primary checkout. Such a run
changes no Spec or code, so the main agent uses it to answer a question or review a Module before
you agree on a change, without opening a task:

```bash
concorde run understand --modules module.payments --goal "how are retries limited today?"
```

## One change from idea to merge

Suppose you and the main agent agreed to limit payment retries in `module.payments`.

### 1. Open a task

Every change of Spec meaning or code behavior runs as a **task**: a branch `concorde/<task>` with
its own worktree, a record and a decision log. Opening the task also binds its worktree as the
task's workspace (`.concorde/workspace.json`, ignored by Git), naming its goal, Modules, branch and
base commit, so every command run inside that worktree works on the task without naming it.

```bash
concorde task open retry --goal "limit payment retries" --modules module.payments
concorde task show retry
```

The worktree is created inside your checkout at `.claude/worktrees/retry` (or `--path`), which
the installer tells Git to ignore, from your current commit (or `--base <ref>`). Your primary
checkout's files are never touched by the task.

### 2. A task session works the task

The main agent records the task's brief in its decision log and starts a **task session** for it,
even when it is the only task; it never works inside the task worktree itself, so it stays free to
talk with you while the task runs. The task session works in the task worktree. It may change Specs
and code directly and commit verified steps on the task branch, or run Operations for bounded
steps. Every `concorde` command for the task runs from the task worktree with that worktree's own
command, never your primary checkout's, because only the task branch knows the Specs and checks the
task changes.

Each Operation is one `concorde run` command and each deterministic step one execution command, all
run inside the task worktree. Each prints one JSON result, also saved in the task's folder of your
primary checkout, `.concorde/tasks/<task>/workspace/runs/<run-id>/result.json`, and one task's
worktree runs one of them at a time.

```bash
concorde run understand  --goal "how should retries be limited?" --plan
concorde run specify     --intent "state the retry limit" --input <plan-run-id>
concorde run implement   --goal "implement the retry limit"
concorde run test
concorde run code_review
concorde task-validation
concorde delivery
```

| Operation                   | Worker       | What it does                                                                                                                                                         |
| --------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `understand`                | reads only   | Assesses what the Modules promise and whether the Spec suffices; returns a plan with `--plan`.                                                                       |
| `specify`                   | writes Specs | Changes the bound Modules' own Spec documents.                                                                                                                       |
| `implement`                 | writes code  | Changes the bound Modules' code; the host runs your checks and resumes the worker on failures (`--rounds` limits the rounds).                                        |
| `test`                      | reads only   | The host runs your checks; the worker interprets the results (`--focus` narrows it).                                                                                 |
| `spec_review`               | reads only   | Reviews the bound Modules' Specs against their review memory: reports new findings, updates and resolves earlier ones (`--check-findings` has each finding checked). |
| `code_review`               | reads only   | Reviews the task's code changes against the Specs (`--base`, `--focus`).                                                                                             |
| `task-validation` (command) | none         | Deterministic: structural validation and the checks of the changed Modules; decides readiness.                                                                       |
| `delivery` (command)        | none         | Deterministic: validates the whole workspace again, then commits it on the task branch; the delivery commit is the record that the task was delivered.               |

Spec reviews keep a **review memory** per Module in `.concorde/reviews/spec/`, committed with the
task. A repeated review reports only what is new, what changed and what was fixed, and a Module
stays `changes_required` while any earlier blocking finding is still open.

A typical task runs `understand`, `specify` when the Spec must change first, `implement` and `test`,
the reviews when the change deserves them, and then `task-validation` and `delivery`. Steps are
repeated or skipped as the results tell. `--input <run-id>` passes the output of an earlier
successful run in the same worktree, such as a plan, to the next worker; `--modules` names the
Modules one run works on, instead of the task's.

Concorde never lets a worker infer a missing promise from the code. When the Spec does not say what
a change needs, the Operation stops with a **Spec gap**, and the Spec is changed first through
`specify`. The one exception is describing a project whose code came before its Specs, below.

### 3. Merge and close

`delivery` validates the whole task again itself and refuses it while anything blocks. Once it has
committed, the task session reports the delivery, and the main agent, in your primary checkout,
merges it, with the project MCP server's `task_merge` or with:

```bash
concorde task merge retry
```

This merges the task branch, runs `concorde spec-validation` on the result (or the commands you name with
`--check`, for example a build before validating), and closes the task. Closing removes the
worktree and keeps the record, and ends the task's Claude Code task sessions, as
[Task sessions](#task-sessions) says. If a check fails, the merge is undone and the primary branch is left
as it was; the output of each check is kept with the merge attempt, in
`.concorde/tasks/retry/merges/<n>/checks/`. A merge conflict is
not resolved in your primary checkout either: the merge is aborted, and the main agent has the
task session merge your primary branch into the task branch, resolve the conflict and deliver
again, the only merge a task session makes.

Several main sessions can work in the same project. Only one of them merges at a time:
`concorde task merge` holds a lock on the primary checkout for as long as it runs, and a second
merge waits for it (up to `--wait` seconds, 300 by default) or, if it gives up, tells you which
task and process holds the lock. The lock belongs to the running command, so it is released even
when that command or its session is killed. Merge with `concorde task merge`, not with `git merge`,
so that the lock applies.

A merge also waits for the task itself: while a run of that task is still going, `merge` and
`close` refuse with `workspace_busy`, naming the run, and are run again once it has ended. They
merge exactly the commit the merge's preflight checked, never whatever the task branch holds a
moment later.

A merge that was interrupted after `git merge` and before its checks finished, because its command
or its session was killed, leaves the task **merging**. Until it is finished, every `concorde task`
command that changes a task refuses with `merge_incomplete`, naming the task, the commit before the
merge and the merge commit, while `concorde task list` and `show` still answer. Finish it with
`concorde task merge retry --resume`, which reruns the merge's checks on the merge commit and then
closes the task or undoes the merge, or with `concorde task merge retry --abort`, which resets the
primary branch to the commit before the merge and returns the task to delivered, to be merged
again. If the primary branch was changed by hand after the merge, both refuse with
`merge_diverged`, and what to keep is your decision.

A task ends as **closed** when it reached its goal, merged or not, or as **failed** when it did
not. `concorde task merge` closes a merged task. A task that reached its goal without a merge,
such as an experiment or an investigation, is closed with
`concorde task close retry --completed --note "<what it achieved>"`. A task that failed is closed
with `concorde task close retry --failed --reason "<why>"`, plus `--run <run-id>` for each run
whose error caused the failure, or `--no-error` when no error did; the reason and the error chains
stay in the task's record and decision log.

`task merge` and `task close` both print the task's record with a list of `warnings`, and each
warning asks the main agent to act. A warning about the decision log means nobody wrote in it. A
warning about a task session names a Claude Code task session whose transcript the close could not
keep in the task's trace, which then stays in Claude's session list so that nothing of it is lost,
or that it could not remove; it gives the reason and the `claude rm <id>` command that removes the
session by hand.

### Task sessions

Every task is worked by its own task session, and tasks whose Modules and shared files do not
overlap may run at the same time, each in its own worktree, while the main agent stays in your
primary checkout:

```bash
concorde task session retry --main <the main agent's session name>
```

A task session does the main agent's own work inside the task, so it runs on the same program as
the main agent, Claude Code, with the same configuration. Its file tools and shell may write only its
own task, and it reports back to the main agent when it has delivered or needs decisions beyond its
task. It never asks you directly: it gathers every decision it needs and reports them together, and
the main agent settles those it may and asks you the rest at once. Only the main agent merges a task
into your primary branch. One task runs at most one Operation at a time. A check that fails after
merging is new work, never a reason to discard a change.

A task session is a background Claude Code session (`claude agents` lists them). Because nobody
answers a background session's permission prompts, it runs in Claude Code's `auto` permission mode,
where a classifier approves or refuses each action within those limits. Ending the task, by its
merge or its close, copies each such session's transcript into the task's trace and removes the
session from Claude's session list with `claude rm`, first stopping it with `claude stop` when the
task closes without a merge; you need not remove them yourself.

## Read results

`concorde run` exits with status 0 for `ok`, 1 for `blocked` or `failed`, and 2 when the command
line itself was wrong. `blocked` means the Operation needs a decision, such as a Spec gap; `failed`
means something went wrong, such as a write outside the grant or checks still failing after the
last round.

A result keeps two things apart:

- `host_evidence` — facts the host observed itself: the grant, the write audit, each check with its
  exit code and log, the resume rounds, the worker's transcript path.
- `worker` — what the worker says it did. It is a claim, never evidence.

### Error chains

Every result that is not `ok` carries an **error chain** in `error`. Each level that could not
handle the error adds one link with a detailed account: what failed and where, its evidence, what
it tried, the options it sees, and the specific reason it could not handle the error itself
(`permission`, `decision`, `scope`, `capability`, `exhausted`, `environment` or `input`). The
errors it received stay underneath as `causes`, unchanged. Reading from the top down, you see the
Operation's link, then the worker run's, the worker's own report, the failing check with the end of
its log, down to where the error started. Standard error shows the same chain as indented text,
and every other `concorde` command refuses with `{"error": <link>}` in the same shape.

When the main agent needs you to decide, it adds its own link on top instead of summarizing:

```bash
concorde task escalate retry --run <run-id> --code spec_decision \
  --detail "module.payments must say how many retries are allowed" \
  --reason decision --explanation "the retry limit is a promise of the Module" \
  --option "3 retries" --option "5 retries" --recommendation "3 retries"
```

The chain is recorded in the task's trace and the decision log and printed for you, so you see
the full path from where the error started to the question you are asked.

### Traces

Every level of the work leaves a record in one shape: the task, its task sessions, its merges, its workflow and steps, each run, each check and each worker run with its rounds, each
nested inside the level that started it. Together they are the task's trace, which you read with:

```bash
concorde trace show retry --format tree
```

It prints each part with its status, how long it took and, rolled up over everything below it, the
tokens, cost and turns the models used, so you see at once which run or worker round made a task
slow or expensive. `concorde trace show <run-id>` shows one run, `concorde trace list --history
--unbound` lists the current tasks, the closed ones and the runs without a task, and without
`--format tree` every command prints JSON for your own analysis.

While a task is open, everything about it lives in one folder, `.concorde/tasks/<task>/`. Closing
the task moves that folder to `.concorde/history/<task>/`, where it stays as it was, and commits
the task's decision log to your primary branch as `.concorde/decisions/<task>.md`. Runs without a
task are kept seven days after they end, and the transcripts of a closed task's sessions and
workers thirty days after it closed; `concorde trace prune` removes what has expired, which
`task open` and `task close` also do. To change those periods, or to remove closed tasks after some
days, write `.concorde/tracing.json`:

```json
{
  "schema_version": 1,
  "retention": {
    "unbound_days": 30,
    "history_days": 180,
    "conversation_days": 60
  }
}
```

The decision log each task commits stays in Git whatever is removed.

## What workers can and cannot do

Before a worker starts, the host computes its grant from the task worktree's Specs for one of seven
task types: `understand`, `specify`, `implement`, `test`, `review-spec`, `review-code` and
`code-to-spec`. You can see any grant yourself:

```bash
concorde grant --modules module.payments --type implement
```

It lists the paths the worker may know by name (`names`), read (`ro`) and write (`rw`); every other
path is denied. Together with the worker's brief and tools, those paths make up its context, in
five kinds:

- **Spec context**: the bound Modules' own documents, the documents their relations select one
  level deep, and the glossary entries of the terms they use;
- **external context**: the documentation and source of external dependencies that the bound
  Modules include as `external`, pinned by your version control, for example as a submodule;
- **implementation context**: the names of the bound Modules' files, and for task types that read
  code, the contents of the whole project's code;
- **capability context**: the tools the worker may use and the result it must return;
- **task context**: the brief with the task, its constraints and the artifacts of earlier steps.

The same grant is compiled into each backend's own mechanism. A worker's configuration, the copies
of the credentials it needs and its working directories live in a private directory under `/tmp`
that is removed when the worker ends; what it was given and did, its grant, brief, transcript and
rounds, is kept in its run's folder. A Claude Code worker runs with:

- deny rules for the file tools, which Claude Code also applies to its Bash sandbox;
- a hook that lets Edit and Write touch only the writable paths;
- a Bash sandbox without network, a cleared environment and a private Claude Code configuration;
- no access to Git.

A pi worker runs with Concorde's permission extension as its only extension:

- `read`, `write` and `edit` are checked against the grant first, and a denial tells the worker
  why, for example that a file is read-only or must first be created and bound by the task session;
- `bash`, `grep`, `find` and `ls` run inside the same sandbox engine Claude Code uses, so files
  outside the grant do not exist for them and there is no network;
- the worker has a cleared environment and a private pi configuration, and no context files,
  skills, prompt templates or other extensions;
- it ends by calling the `concorde_result` tool, and stops at the turn and budget limits you set.

After each round the host audits the worktree; any write outside `rw` fails the run. A worker
creates a new file only inside a directory its Module binds; any other new file is created and
bound to its Module by the task session before the worker that fills it runs.

These layers guard against scope drift and mistakes, not against a malicious actor. Their known
limits are stated in the [Harness](https://ftod.github.io/concorde/specs/concorde/harness/module)
Spec.

## Record problems as Issues

A problem the current task will not fix, such as a Spec gap in another Module, is recorded as an
**Issue** under `.concorde/issues/` so that it survives the task:

```bash
concorde issues report --file report.json [--task retry]
concorde issues list
concorde issues show <id>
```

Solving an Issue is ordinary work: a task for its Module, the Operations that fix it, and
`concorde issues close <id> --reason resolved --note <text> --evidence <path>` on that task's branch,
so the closure is merged together with the fix.

## Ask the Specs directly

The Spec tooling answers questions from the Specs without calling a model:

- `concorde spec-validation` checks every structural rule of the Protocol.
- `concorde grant --modules <ids> --type <task type>` prints a grant.
- `concorde spec-mcp` is a local stdio MCP server that answers which Modules exist, what a Module's
  context is, which Modules some paths concern and what grant a task would receive.

To let your main agent use the MCP server, register it in your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "concorde-spec": {
      "command": ".concorde/bin/concorde",
      "args": ["spec-mcp"]
    }
  }
}
```

It answers from the worktree it is rooted in. Workers never receive it.

## Publish your Specs

Concorde can scaffold a documentation site that publishes your Specs, like
[Concorde's own site](https://ftod.github.io/concorde/):

```bash
concorde docsite --propose --title "My project" > docsite-proposal.json   # read it first
concorde docsite --apply --proposal docsite-proposal.json
rm docsite-proposal.json
npm --prefix docsite ci
npm --prefix docsite run start
```

Unlike the initialization proposal, the docsite proposal is passed as a path inside the project.
`--github-pages` adds a GitHub Actions workflow that deploys the site. Scaffolding only creates
files; it never updates or deletes an existing site.

The site's tabs come in a fixed order:

1. **User documents**, when you configure them: add `"userDocs": {"path": "../docs"}` to
   `docsite/site.json`. The directory is published as it is, with a sidebar that follows its
   folders, and its root page (`README.md` or `index.md`) becomes the site's home page at `/`.
   Concorde publishes this guide that way. Without user documents, the home page opens the root
   Module's entry.
2. **Module documents**, generated from your Specs. No tab lists implementation documents: each
   Module's entry ends with a folded list of its own.
3. Any **custom docs** collections you list under `customDocs`, such as Concorde's Spec Protocol
   tab.

Neither user documents nor custom docs may contain a registered Spec document.

## Where things live

| Path                                       | What it holds                                                                           |
| ------------------------------------------ | --------------------------------------------------------------------------------------- |
| `specs/`                                   | Your Specs: each Module's documents and their `.md.json` metadata.                      |
| `.concorde/config.json`                    | The Protocol binding and your project's interpreter.                                    |
| `.concorde/checks/`                        | Your checks, one `<module id>.json` file per Module.                                    |
| `.concorde/workers.json`                   | The models and limits of the workers.                                                   |
| `.concorde/specs.json`                     | The registry of Modules.                                                                |
| `.concorde/protocol/`                      | The installed Spec Protocol.                                                            |
| `.concorde/bin/concorde`                   | The `concorde` command.                                                                 |
| `.concorde/framework/`, `.concorde/tools/` | The installed runtime and `d2` (ignored by Git).                                        |
| `.concorde/tasks/<task>/`                  | A current task: its record, decision log, sessions, merges and runs (ignored by Git).   |
| `.concorde/history/`                       | The folders of closed tasks, kept as they were (ignored by Git).                        |
| `.concorde/unbound/`                       | Runs without a task, such as an `understand` of your primary checkout (ignored by Git). |
| `.concorde/locks/`                         | Every lock Concorde takes (ignored by Git).                                             |
| `.concorde/tracing.json`                   | How long unbound runs, closed tasks and their transcripts are kept (optional).          |
| `.concorde/decisions/`                     | The decision logs of ended tasks, committed when each task ends.                        |
| `.concorde/issues/`                        | Issue records.                                                                          |
| `.claude/skills/concorde/SKILL.md`         | The main agent's guidance.                                                              |

## Learn more

- [Spec Protocol](https://ftod.github.io/concorde/protocol): the rules every Spec follows.
- [Concorde's Specs](https://ftod.github.io/concorde/specs/concorde/module): how Concorde itself is
  built, described with Concorde.
- [Source repository](https://github.com/FTOD/concorde).
