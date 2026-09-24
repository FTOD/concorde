# Using Concorde

This guide is for developers who want to use Concorde in their own project. It covers installing
Concorde, writing the first Spec, working with the main agent, carrying one change from an idea to
a merge, and reading what Concorde reports back. It describes Concorde 9 with
[Spec Protocol 13](https://ftod.github.io/concorde/protocol) with Claude Code or
[pi](https://github.com/earendil-works/pi) as the client, for the main agent and for the workers.

In the commands below, `concorde` stands for your project's `.concorde/bin/concorde`.

## What Concorde does for you

Concorde keeps your project's **Specs** at the center of AI-assisted development. A Spec explains
what each Module of your project is for, how it is designed, which precise promises it makes and
which files realize it. From those Specs Concorde computes exactly what an AI task may read and
write, and runs headless Claude Code or pi workers inside that boundary.

You work with three actors:

- **You, the developer**, decide the direction and answer the questions that have a major impact.
- **The main agent** is your own Claude Code or pi session in the project's primary checkout. It discusses
  the project with you, splits agreed work into tasks, runs Concorde's Operations, reads their
  results, keeps a decision log and merges what was delivered. It normally does not edit the
  project itself.
- **Workers** are headless `claude -p` or `pi -p` processes that one Operation starts for one bounded job,
  such as implementing a change. Each works under a **grant** computed from the Specs: the paths it
  may know by name, read and write. Everything else is denied.

Between the main agent and the workers sits the **Operation host**, the deterministic part of every
Operation: it computes the grant, launches the worker, audits what it changed, runs your checks
itself and writes a result you can trust.

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
- Python 3.11 or later;
- [Claude Code](https://docs.claude.com/en/docs/claude-code), installed and logged in, or
  [pi](https://github.com/earendil-works/pi) with a configured model; for pi also Node.js with npm,
  `rg` (ripgrep), `fd` and `socat`, and optionally
  [pi-subagents](https://github.com/nicobailon/pi-subagents) for its run view;
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

- the Concorde runtime under `.concorde/framework/` and the `concorde` command as
  `.concorde/bin/concorde`;
- a copy of the Spec Protocol under `.concorde/protocol/`, so the rules your Specs follow travel
  with your project;
- the main agent's guidance, as the Claude Code skill `.claude/skills/concorde/SKILL.md` and a short
  block between `<!-- concorde:start -->` and `<!-- concorde:end -->` in your `CLAUDE.md` (the rest
  of the file is left untouched);
- the [`d2`](https://github.com/d2lang/d2) program that draws your Specs' diagrams, as
  `.concorde/tools/d2`, at a pinned release whose checksum it verifies (`--without-d2` skips it);
- ignore rules for the directories Concorde writes at run time, and a receipt
  `.concorde/install.json`.

To use pi, add `--pi`. The installer then also places:

- the sandbox engine pi workers run their commands in, `@anthropic-ai/sandbox-runtime`, under
  `.concorde/tools/pi-runtime/`, installed with `npm ci --ignore-scripts` from the lockfile
  Concorde ships, so you get exactly the versions it was tested with;
- Concorde's pi extension, the **run view**, as `.pi/extensions/concorde/`;
- the main agent's guidance a second time, as the pi skill `.pi/skills/concorde/SKILL.md`.

The installer never writes your Specs, your registry or your project configuration.

To update Concorde, pull the checkout, build again and rerun the installer. When the new version
carries a newer Protocol, `concorde validate` refuses with `protocol_mismatch` until you accept it:
read what changed in `.concorde/protocol/`, then update the `protocol` version and digest in
`.concorde/config.json` to the new copy's.

## Write your first Spec

Initialization proposes the first Spec and applies exactly what it proposed, so you can inspect
every file before anything is written:

```bash
cd /absolute/path/to/project
.concorde/bin/concorde init --propose --name "My project" > /tmp/proposal.json
jq .result /tmp/proposal.json > /tmp/accepted.json   # read it first
.concorde/bin/concorde init --apply --proposal /tmp/accepted.json
.concorde/bin/concorde validate
```

Keep the proposal file outside the project. Applying it writes:

- `.concorde/config.json`, the project configuration: the Protocol binding and your checks;
- `.concorde/specs.json`, the **registry** that lists every Module;
- `specs/project/module.md` with its metadata `module.md.json`, the root Module `module.project`.

The first Spec is deliberately honest and small. From here you describe your project as Modules.
Every Module's entry document `module.md` answers five questions in order:

1. **Purpose** — what the Module is for, in plain prose.
2. **Terminology** — the words it defines and the ones it imports.
3. **Usage** — how it is used and how it must react.
4. **Design** — how it is built, including the files that realize it.
5. **Relationships** — which Modules it contains and uses, drawn as a `d2` diagram.

Precise requirements, scenarios and contracts go into the Module's implementation documents. The
[Protocol overview](https://ftod.github.io/concorde/protocol) and its
[Module template](https://ftod.github.io/concorde/protocol/templates/module) show the exact format;
[Concorde's own Specs](https://ftod.github.io/concorde/specs/concorde/module) are a complete,
working example.

You do not have to write every Spec by hand. Once the root exists, you can ask the main agent to
propose Modules for your project and let `specify` tasks write them (see below). Whoever writes
them, two commands keep Specs consistent:

```bash
concorde validate            # every structural rule of the Protocol
concorde registry --write    # refresh the registry after a Module's `module` block changed
```

## Configure your checks

**Checks** are your project's own commands, such as a test suite or a linter, each assigned to one
Module. The Operation host runs them itself, never the worker, and records each result as evidence.
Declare them in `.concorde/config.json` under `checks`:

```json
{
  "id": "check.payments.tests",
  "module": "module.payments",
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
```

`inputs` are the paths the result depends on; if they change while the check runs, its result is
refused as stale. Checks run in a sandbox in which the whole filesystem is read-only except a fresh
scratch directory, named by `TMPDIR`, `XDG_CACHE_HOME`, `CONCORDE_CHECK_TMPDIR` and
`CONCORDE_CHECK_REPORT_DIR`. A check that writes caches or reports into the project fails and must
be pointed at the scratch; a tool that rewrites sources, such as a formatter in fix mode, is not a
check.

## Work with the main agent

Open Claude Code or pi in your project's primary checkout. The installed skill makes that session
the main agent; you talk to it as usual.

- **Discuss first.** Ask about the project, agree the direction and the large plan. The main agent
  answers from the Specs.
- **Let it decide the ordinary things.** Names, internal structure, the order of tasks, rerunning an
  Operation with a clearer brief, splitting a task: the main agent decides these itself, writes
  each decision and its reason into the task's decision log and reports them at the end.
- **Expect questions only when they matter.** It asks you before acting when a decision changes what
  a Module promises or the project's direction, contradicts an earlier decision of yours, discards
  work, cannot be undone by an ordinary revert, touches security or credentials, or needs more
  resources than you allowed.
- **Delivered work is merged without asking.** When a task has been delivered, the main agent merges
  its branch and reports what it merged.

You can run every command below yourself as well; the main agent uses exactly the same ones.

### In pi: the run view

In pi the main agent starts Operations with the `concorde_run` tool instead of background Bash. The
tool starts `concorde run` in the background and returns at once; when the run ends, the main agent
is woken with its result. Meanwhile every run of the project appears in pi-subagents' **FleetView**
as an external job: its task and Operation, the step it is in, and, while a worker runs, the
worker's round and latest tool call, such as `implement worker (pi) round 2 · worker: bash pytest
-q`. When it ends, the view shows its status and summary. `/concorde` lists the recent runs, also
without pi-subagents. The view only observes: the Operation keeps running if you close pi.

### Choose the worker models

Workers run on the program you talk to: a Claude Code main agent gets Claude Code workers, a pi
main agent pi workers. Mixing the two is not supported yet. Which model and reasoning level they
use is yours to choose; ask the main agent to change the worker models.

- In pi, the main agent opens a picker (you can also type `/concorde-models`). You choose the
  default for every task type or a task type of your choice, then a model from the ones pi lists
  with credentials, then a reasoning level.
- In Claude Code, the main agent lists the candidates and asks you the same three questions.
  Claude Code cannot list the models of your account, so it offers its aliases (`fable`, `opus`,
  `sonnet`, `haiku`) and the models your settings name; type a full model name such as
  `claude-opus-5-5` as a free answer if you want a specific one.

The choice is stored per worktree in `.concorde/worker-models.json`, which Git ignores:

```json
{
  "schema_version": 1,
  "pi": {
    "default": { "model": "anthropic/claude-sonnet-5", "reasoning": "medium" },
    "task_types": {
      "implement": { "model": "local-openai/gpt-6", "reasoning": "low" }
    }
  }
}
```

A task copies the primary worktree's file when it is opened and keeps it: a change you make later
applies to tasks opened after it, and changes an existing task only if you ask for that task. The
same commands work by hand:

```bash
concorde workers models                    # candidates and the current choice
concorde workers set --model sonnet --reasoning medium
concorde workers set --task-type implement --model opus
concorde workers unset --task-type implement
concorde workers show --task retry         # one task's own copy
```

The reasoning level is passed as `--effort` to Claude Code and as `--thinking` to pi. A pi worker
uses copies of your pi `auth.json` and `models.json` and nothing else from your pi configuration.

## One change from idea to merge

Suppose you and the main agent agreed to limit payment retries in `module.payments`.

### 1. Open a task

Every change of Spec meaning or code behavior runs as a **task**: a branch `concorde/<task>` with
its own worktree, a record and a decision log.

```bash
concorde task open retry --goal "limit payment retries" --modules module.payments
concorde task show retry
```

The worktree is created inside your checkout at `.claude/worktrees/retry` (or `--path`), which
the installer tells Git to ignore, from your current commit (or `--base <ref>`). Your primary
checkout's files are never touched by the task.

### 2. Work inside the task

The main agent enters the task worktree (Claude Code's EnterWorktree) and does the work there. It
may change Specs and code directly and commit verified steps on the task branch, or run
Operations for bounded steps. Every `concorde` command for the task runs from the task worktree
with that worktree's own command, never your primary checkout's, because only the task branch
knows the Specs and checks the task changes.

Each Operation is one `concorde run` command. It prints one JSON result, also saved as
`.concorde/runs/<run-id>/result.json` of your primary checkout. The main agent runs them in the
background (background Bash in Claude Code, the `concorde_run` tool in pi) so it can keep talking
with you meanwhile.

```bash
concorde run understand  --task retry --goal "how should retries be limited?" --plan
concorde run specify     --task retry --intent "state the retry limit" --input <plan-run-id>
concorde run implement   --task retry --goal "implement the retry limit"
concorde run test        --task retry
concorde run code_review --task retry
concorde run validate    --task retry
concorde run delivery    --task retry
```

| Operation     | Worker       | What it does                                                                                                                  |
| ------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `understand`  | reads only   | Assesses what the Modules promise and whether the Spec suffices; returns a plan with `--plan`.                                |
| `specify`     | writes Specs | Changes the bound Modules' own Spec documents, including declaring files that do not exist yet.                               |
| `implement`   | writes code  | Changes the bound Modules' code; the host runs your checks and resumes the worker on failures (`--rounds` limits the rounds). |
| `test`        | reads only   | The host runs your checks; the worker interprets the results (`--focus` narrows it).                                          |
| `spec_review` | reads only   | Reviews the bound Modules' Specs and reports every blocking finding (`--check-findings` has each finding checked).            |
| `code_review` | reads only   | Reviews the task's code changes against the Specs (`--base`, `--focus`).                                                      |
| `validate`    | none         | Deterministic: structural validation and the checks of the changed Modules; decides readiness.                                |
| `delivery`    | none         | Deterministic: validates the whole task again, then commits its evidence bundle on the task branch.                           |

A typical task runs `understand`, `specify` when the Spec must change first, `implement` and `test`,
the reviews when the change deserves them, and then `validate` and `delivery`. Steps are repeated
or skipped as the results tell. `--input <run-id>` passes the output of an earlier successful run of
the same task, such as a plan, to the next worker; `--modules` binds more Modules to the task.

Concorde never lets a worker infer a missing promise from the code. When the Spec does not say what
a change needs, the Operation stops with a **Spec gap**, and the Spec is changed first through
`specify`.

### 3. Merge and close

`delivery` validates the whole task again itself and refuses it while anything blocks. Once it has
committed, the main agent leaves the task worktree and, in your primary checkout:

```bash
concorde task merge retry
```

This merges the task branch, runs `concorde validate` on the result (or the commands you name with
`--check`, for example a build before validating), and closes the task. Closing removes the
worktree and keeps the record. If a check fails, the merge is undone and the primary branch is left
as it was; the output of the checks is in `.concorde/tasks/retry.merge.log`. A merge conflict is
not resolved in your primary checkout either: the merge is aborted, and the conflict is resolved
in the task worktree by merging your primary branch into the task branch and delivering again.

Several main sessions can work in the same project. Only one of them merges at a time:
`concorde task merge` holds a lock on the primary checkout for as long as it runs, and a second
merge waits for it (up to `--wait` seconds, 300 by default) or, if it gives up, tells you which
task and process holds the lock. The lock belongs to the running command, so it is released even
when that command or its session is killed. Merge with `concorde task merge`, not with `git merge`,
so that the lock applies.

A task ends as **closed** when it reached its goal, merged or not, or as **failed** when it did
not. `concorde task merge` closes a merged task. A task that reached its goal without a merge,
such as an experiment or an investigation, is closed with
`concorde task close retry --completed --note "<what it achieved>"`. A task that failed is closed
with `concorde task close retry --failed --reason "<why>"`, plus `--run <run-id>` for each run
whose error caused the failure, or `--no-error` when no error did; the reason and the error chains
stay in the task's record and decision log.

### Several tasks at once

Tasks whose Modules and shared files do not overlap may run at the same time, each in its own
worktree. A session works inside one task at a time, so for work split into several tasks the main
agent starts a **task session** per task and stays in your primary checkout:

```bash
concorde task session retry --main <the main agent's session name>
```

A task session is a background Claude Code session (`claude agents` lists them) working in the
task worktree by the same method. Its file tools and shell may write only its own task, and it
reports back to the main agent when it has delivered or needs a decision beyond its task. Only the
main agent merges. Because nobody answers a background session's permission prompts, a task
session runs in Claude Code's `auto` permission mode, where a classifier approves or refuses each
action within those limits. One task runs at most one Operation at a time. A merge conflict is
resolved in the task, and a check that fails after merging is new work, never a reason to discard
a change.

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

The chain is recorded in the task record and the decision log and printed for you, so you see the
full path from where the error started to the question you are asked.

## What workers can and cannot do

Before a worker starts, the host computes its grant from the task worktree's Specs for one of six
task types: `understand`, `specify`, `implement`, `test`, `review-spec` and `review-code`. You can
see any grant yourself:

```bash
concorde grant --modules module.payments --type implement
```

It lists the paths the worker may know by name (`names`), read (`ro`) and write (`rw`); every other
path is denied. The same grant is compiled into each backend's own mechanism. A Claude Code worker
runs in its own run directory under `.concorde/runs/` with:

- deny rules for the file tools, which Claude Code also applies to its Bash sandbox;
- a hook that lets Edit and Write touch only the writable paths;
- a Bash sandbox without network, a cleared environment and a private Claude Code configuration;
- no access to Git.

A pi worker runs with Concorde's permission extension as its only extension:

- `read`, `write` and `edit` are checked against the grant first, and a denial tells the worker
  why, for example that a file is read-only or must first be declared through `specify`;
- `bash`, `grep`, `find` and `ls` run inside the same sandbox engine Claude Code uses, so files
  outside the grant do not exist for them and there is no network;
- the worker has a cleared environment and a private pi configuration, and no context files,
  skills, prompt templates or other extensions;
- it ends by calling the `concorde_result` tool, and stops at the turn and budget limits you set.

After each round the host audits the worktree; any write outside `rw` fails the run. A file that
does not exist yet can only be written once `specify` has declared it as a pending file of its
Module.

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

- `concorde validate` checks every structural rule of the Protocol.
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
2. **Module documents** and **Implementation documents**, generated from your Specs.
3. Any **custom docs** collections you list under `customDocs`, such as Concorde's Spec Protocol
   tab.

Neither user documents nor custom docs may contain a registered Spec document.

## Where things live

| Path                                       | What it holds                                                                |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| `specs/`                                   | Your Specs: each Module's documents and their `.md.json` metadata.           |
| `.concorde/config.json`                    | The Protocol binding and your checks.                                        |
| `.concorde/specs.json`                     | The registry of Modules.                                                     |
| `.concorde/protocol/`                      | The installed Spec Protocol.                                                 |
| `.concorde/bin/concorde`                   | The `concorde` command.                                                      |
| `.concorde/framework/`, `.concorde/tools/` | The installed runtime and `d2` (ignored by Git).                             |
| `.concorde/tasks/`                         | Task records and decision logs (ignored by Git).                             |
| `.concorde/runs/`                          | Each Operation run: its result, logs and worker transcript (ignored by Git). |
| `.concorde/evidence/`                      | Evidence bundles committed by `delivery`.                                    |
| `.concorde/issues/`                        | Issue records.                                                               |
| `.claude/skills/concorde/SKILL.md`         | The main agent's guidance.                                                   |

## Learn more

- [Spec Protocol](https://ftod.github.io/concorde/protocol): the rules every Spec follows.
- [Concorde's Specs](https://ftod.github.io/concorde/specs/concorde/module): how Concorde itself is
  built, described with Concorde.
- [Source repository](https://github.com/FTOD/concorde).
