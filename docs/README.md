# Concorde

![Concorde — Specs that harness your agents.](assets/concorde-hero.svg)

**Specs that harness your agents.**

Concorde is spec-harnessed agent development. Your project's Specs divide it into Modules and say
what each one is responsible for; Concorde turns that division of responsibility into the harness
of every AI agent that works on the project: the context it is given and the files it may read and
write. Your Claude Code or pi session, the main agent, splits the work into tasks, and every worker
it launches through Concorde runs inside the harness its task's Modules define.

New here? Start with **[Using Concorde](using-concorde.md)**.

## From responsibility to harness

1. **The Specs divide the responsibility.** Every Module states its purpose, its words, how it is
   used, and how it is designed: how it is built, how it works with other Modules and which files
   realize it.
2. **The division derives the harness.** A task binds some Modules and has one of seven task types:
   `understand`, `specify`, `implement`, `test`, `review-spec`, `review-code`, and `code-to-spec`
   for describing code written before its Specs. From those alone
   Concorde computes the worker's context, the Specs, implementation files and tools it needs, and
   its grant, every path it may know by name, read or write. Everything else is denied.
3. **The host enforces and verifies.** The grant is compiled into the worker's own settings. After
   the worker stops, the host audits what it changed, runs the project's checks itself and keeps
   what it verified apart from what the worker claims.
4. **Failures travel up as an error chain.** A level that cannot handle an error adds a detailed
   link saying why and keeps what it received underneath, so the main agent, and you when a
   decision is yours, see the whole path.

Change the Specs and the harness changes with them: there is no separate permission file to keep
in step.

## What you get

- **Architecture-aware Specs.** Module documents explain purpose, terminology, use and design,
  inside a Module and between Modules, to a reader who does not know the code, and tests declare the scenarios they
  verify. You understand the project from them; an agent receives the same text as its context.
  This site is built from them.
- **Just the context a task needs.** A worker sees what its Modules declare, one level deep, and
  no more. It never infers a missing promise from the code: it stops with a Spec gap, and the Spec
  is changed first. Only a codebase adopted after its code was written is described from its code,
  once, by the brownfield workflow, which reports doubtful intent as open questions.
- **Workers fenced by their own settings.** A Claude Code worker gets generated deny rules (which
  also bind its Bash sandbox), a write hook and a sandbox without network; a pi worker gets
  Concorde's permission extension on the same sandbox engine. Both have a cleared environment and
  a private configuration, and the host audits every round against the grant. These guard against
  drift and mistakes, not a malicious actor.
- **Verified, not trusted.** Every Operation returns one JSON result where `host_evidence` is kept
  apart from `worker`, which is only a claim, and every failure carries an error chain.
- **Tasks that can run side by side.** Each task is a branch with its own worktree, a record and a
  decision log. Tasks whose Modules and shared files do not overlap run at once in task sessions;
  `concorde task merge` merges them one at a time and validates the result again.
- **Spec tooling that stands alone.** `concorde validate`, `concorde grant` and the stdio MCP
  server `concorde spec-mcp` answer from the Specs of one worktree without calling a model, so any
  agent can ask what a task may touch.

## One task from idea to merge

The main agent agrees the direction with you, then works through a task; it decides ordinary
questions itself and escalates only decisions with major impact.

1. **Discuss and open.** Agree the change and open a task: a branch and worktree for the Modules
   it touches. The main agent works inside that worktree, or starts a task session per task when
   the work splits into several.
2. **Understand and specify.** Run `understand` to assess and plan; run `specify` when the Spec
   must change first.
3. **Implement and test.** Run `implement` and `test`; the host audits every write and runs the
   configured checks itself.
4. **Validate, deliver, merge.** `validate` previews readiness, `delivery` validates the whole task
   again and commits it with its evidence, and `concorde task merge` merges the branch and closes
   the task.

A question that changes nothing, such as how a Module works today, needs no task: `understand`,
`spec_review` and `code_review` also run from the primary worktree without one.

## Install into a Git project

Use Python 3.11+ on Linux with bubblewrap, and a logged-in Claude Code or a configured
[pi](https://github.com/earendil-works/pi). The installer places the runtime, the `concorde`
command, the Protocol copy and the main agent's guidance; it never writes your Specs.

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
python3 scripts/install-concorde.py /absolute/path/to/project   # add --pi for pi

cd /absolute/path/to/project
.concorde/bin/concorde init --propose --name "My project"
```

[Using Concorde](using-concorde.md) continues from here.

## Commands

In an installed project the command is `.concorde/bin/concorde`; Operations print one JSON result.

| Command                                                 | Use                                                                          |
| ------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `concorde validate`                                     | Check every structural rule of the Specs.                                    |
| `concorde grant --modules <ids> --type <task type>`     | Print the grant of a task type for some Modules.                             |
| `concorde spec-mcp`                                     | Run the local stdio MCP server rooted at the project.                        |
| `concorde task open\|list\|show\|session\|merge\|close` | Manage tasks: branch, worktree, record, decision log, task sessions, merges. |
| `concorde task escalate`                                | Add the main agent's link on top of an error chain and record it.            |
| `concorde run <operation> [--task <task>]`              | Run one Operation and print its result.                                      |
| `concorde issues report\|list\|show\|close`             | Record problems a task will not fix, so they survive it.                     |
| `concorde init --propose\|--apply`                      | Propose and apply a project's first Spec.                                    |
| `concorde docsite --propose\|--apply`                   | Scaffold a documentation site for the project's Specs.                       |

| Operation           | Result and boundary                                                                           |
| ------------------- | --------------------------------------------------------------------------------------------- |
| `understand`        | An assessment of the Modules and, when asked, a plan; reads Specs and only the names of code. |
| `specify`           | A change of the bound Modules' own Spec documents; structural validation afterwards.          |
| `implement`         | A code change within the bound Modules' realization; configured checks with resume rounds.    |
| `test`              | The host's check results interpreted by a read-only worker.                                   |
| `spec_review`       | Review findings and a verdict on the bound Modules' Specs.                                    |
| `code_review`       | Review findings and a verdict on the task's code changes.                                     |
| `validate`          | Readiness: structural validation and the configured checks of the changed Modules.            |
| `delivery`          | A commit of the task's change with its evidence bundle on the task branch.                    |
| `configure_workers` | The models and reasoning levels the workers use, for all workers or one Operation's.          |

## Explore

- [Module documents](https://ftod.github.io/concorde/specs/concorde/module): how Concorde itself is
  built, described with Concorde.
- [Spec Protocol](https://ftod.github.io/concorde/protocol): the rules every Spec follows.
- [Source repository](https://github.com/FTOD/concorde).
