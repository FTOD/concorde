# Concorde

![Concorde — Specify the architecture. Understand the system. Guide your agents.](assets/concorde-hero.svg)

**Specify the architecture. Fence your agents.**

Concorde keeps your project's Specs at the center of AI-assisted development. Its Spec tooling
validates the Specs, computes from them exactly what a task may read and write, serves them over a
local MCP server and publishes them as a site like this one. Your Claude Code session, the main
agent, splits work into tasks and runs Concorde's Operations, whose headless Claude Code workers
run inside the Spec-derived boundary and whose results keep host evidence apart from worker
claims.

New here? Start with **[Using Concorde](using-concorde.md)**.

## Context and permission, managed around the Spec

- **Read complete Module specifications.** Module documents explain purpose, terminology, use,
  design and relationships for a reader who does not know the code. Implementation documents hold
  the precise requirements, scenarios and contracts, and tests declare the scenarios they verify.
- **Grants computed from the Specs.** The Spec Protocol defines six task types — `understand`,
  `specify`, `implement`, `test`, `review-spec`, `review-code` — and the access level each gives
  every boundary set. A grant lists every path a task may know by name, read or write; everything
  else is denied.
- **Workers fenced by their own settings.** Each worker is a headless `claude -p` process with
  generated deny rules (which also bind its Bash sandbox), a write-only hook, a sandbox without
  network, a cleared environment and its own configuration directory. The host audits every round
  against the grant. These guard against drift and mistakes, not a malicious actor.
- **Operations: host steps plus workers.** `understand`, `specify`, `implement`, `test`,
  `spec_review` and `code_review` run workers; `validate` and `delivery` are deterministic. The
  host runs configured checks itself, resumes a worker only to fix failing checks, and stops with
  an escalation on a Spec gap or a boundary it would have to cross.
- **Tasks are branches.** Each task is a branch with its own worktree, a record and a decision
  log. Tasks run in parallel only in separate worktrees; delivery commits the change with its
  evidence and the main agent merges it.
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
   again and commits it with its evidence, and the main agent merges the branch.

## Install into a Git project

Use Python 3.11+ and a logged-in Claude Code on Linux with bubblewrap. The installer places the
runtime, the `concorde` command, the Protocol copy and the main-session guidance; it never writes
your Specs. Claude Code is the only supported client in this version.

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
python3 scripts/install-concorde.py /absolute/path/to/project

cd /absolute/path/to/project
.concorde/bin/concorde init --propose --name "My project"
```

[Using Concorde](using-concorde.md) continues from here.

## Commands

In an installed project the command is `.concorde/bin/concorde`; Operations print one JSON result.

| Command                                             | Use                                                                     |
| --------------------------------------------------- | ----------------------------------------------------------------------- |
| `concorde validate`                                 | Check every structural rule of the Specs.                               |
| `concorde grant --modules <ids> --type <task type>` | Print the grant of a task type for some Modules.                        |
| `concorde spec-mcp`                                 | Run the local stdio MCP server rooted at the project.                   |
| `concorde task open\|list\|show\|session\|close`    | Manage tasks: branch, worktree, record, decision log and task sessions. |
| `concorde run <operation> --task <task>`            | Run one Operation and print its result.                                 |
| `concorde init --propose\|--apply`                  | Propose and apply a project's first Spec.                               |
| `concorde docsite --propose\|--apply`               | Scaffold a documentation site for the project's Specs.                  |

| Operation     | Result and boundary                                                                           |
| ------------- | --------------------------------------------------------------------------------------------- |
| `understand`  | An assessment of the Modules and, when asked, a plan; reads Specs and only the names of code. |
| `specify`     | A change of the bound Modules' own Spec documents; structural validation afterwards.          |
| `implement`   | A code change within the bound Modules' realization; configured checks with resume rounds.    |
| `test`        | The host's check results interpreted by a read-only worker.                                   |
| `spec_review` | Review findings and a verdict on the bound Modules' Specs.                                    |
| `code_review` | Review findings and a verdict on the task's code changes.                                     |
| `validate`    | Readiness: structural validation and the configured checks of the changed Modules.            |
| `delivery`    | A commit of the task's change with its evidence bundle on the task branch.                    |

## Explore

- [Module documents](https://ftod.github.io/concorde/specs/concorde/module): how Concorde itself is
  built, described with Concorde.
- [Spec Protocol](https://ftod.github.io/concorde/protocol): the rules every Spec follows.
- [Source repository](https://github.com/FTOD/concorde).
