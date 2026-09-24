<p align="center">
  <img src="docs/assets/concorde-hero.svg" alt="Concorde — Specify the architecture. Understand the system. Guide your agents." width="100%" />
</p>

<p align="center">
  <a href="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml"><img src="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml/badge.svg" alt="Source validation" /></a>
  <a href="protocol/README.md"><img src="https://img.shields.io/badge/Spec_Protocol-13.0.0-6264e8" alt="Spec Protocol 13.0.0" /></a>
  <a href="#get-started"><img src="https://img.shields.io/badge/client-Claude_Code_%7C_pi-273449" alt="Client: Claude Code or pi" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-273449" alt="MIT license" /></a>
</p>

<p align="center">
  <a href="#why-concorde"><strong>Why Concorde</strong></a> ·
  <a href="#get-started"><strong>Get started</strong></a> ·
  <a href="#the-docsite"><strong>Docsite</strong></a> ·
  <a href="https://ftod.github.io/concorde/"><strong>Explore the Specs</strong></a> ·
  <a href="docs/using-concorde.md"><strong>Using Concorde</strong></a>
</p>

# Concorde

**Architecture-aware Specs, and Claude Code or pi workers fenced by them.**

Concorde keeps a project's Specs at the center of AI-assisted development. A Spec explains what
each Module is responsible for, how it is designed, which precise promises it makes and which files
realize it. From those Specs Concorde computes exactly what a task may read and write, and runs
headless Claude Code or pi workers inside that boundary. Your own Claude Code or pi session, the
**main agent**, splits work into tasks, runs Concorde's Operations, reads their results and merges what
was delivered.

Concorde supports **Claude Code** and **[pi](https://github.com/earendil-works/pi)**, for the main
agent and for the workers. One grant is compiled into each: Claude Code settings with deny rules, a
write hook and its sandbox, or a pi permission extension with the same sandbox engine. In pi the
main agent also gets a run view in [pi-subagents](https://github.com/nicobailon/pi-subagents)'
FleetView that shows every Operation and its worker's progress.

## Why Concorde

### Specs that explain the architecture

Every Module has an entry `module.md` written under the independent
[Spec Protocol](protocol/README.md): its purpose, its words, how it is used, how it is designed and
how it relates to other Modules, with implementation documents holding precise requirements,
scenarios and contracts. A human understands the project from the Specs; an agent receives the same
Specs as its context.

### Spec tooling that stands on its own

The **Spec tooling** checks and serves Specs without calling a model:

- `concorde validate` checks every structural rule of the Protocol.
- `concorde grant --modules <ids> --type <task type>` computes the **grant** of a task: every path
  it may know by name, read or write, for one of the six Protocol task types (`understand`,
  `specify`, `implement`, `test`, `review-spec`, `review-code`).
- `concorde spec-mcp` is a local stdio **MCP server** that lets any agent ask which Modules exist,
  what a Module's context is, whom a change concerns and what grant a task would receive — always
  from the Specs of the one worktree it is rooted at.
- The **docsite** publishes the Specs for readers.

### Workers inside a Spec-derived boundary

An Operation such as `implement` computes the grant from the task worktree's Specs, then launches a
`claude -p` worker whose own settings enforce it: deny rules for the file tools (which Claude Code
also applies to its Bash sandbox), a small hook that makes the writable paths the only ones Edit and
Write may touch, a closed Bash sandbox with no network, a cleared environment and a private
configuration directory. After the worker stops, the host audits the worktree against the grant,
runs the project's configured checks itself in a read-only sandbox and, when a check fails, resumes
the same worker with the failures. These layers guard against scope drift and mistakes, not a
malicious actor; the [Harness](specs/concorde/harness/module.md) states their limits honestly.

### Tasks, results and error chains

Each unit of work is a **task**: a branch with its own worktree, a record and a decision log. Every
Operation returns one JSON result that keeps what the host verified (`host_evidence`) apart from
what the worker claims (`worker`). Every failure carries an **error chain**: each level that could
not handle the error (a check, the worker, the worker harness, the Operation, the main agent) adds
one link with a detailed account, its evidence, what it tried, its options and the specific reason
it could not handle the error, and keeps the errors it received as causes, unchanged. The main
agent reads the whole chain, decides what it can, records it, and asks the developer only about
decisions with major impact, adding its own link with `concorde task escalate` so the developer
sees the full path from where the error started.

## Get started

Install Concorde into a Git project and initialize its first Spec:

```bash
python3 /path/to/concorde/scripts/concorde.py build
python3 /path/to/concorde/scripts/install-concorde.py /path/to/project   # add --pi for pi
cd /path/to/project
.concorde/bin/concorde init --propose --name "My project" > /tmp/proposal.json
jq .result /tmp/proposal.json > /tmp/accepted.json   # inspect it first
.concorde/bin/concorde init --apply --proposal /tmp/accepted.json
.concorde/bin/concorde validate
```

The installer places the runtime under `.concorde/framework/`, the `.concorde/bin/concorde`
command, the Protocol copy under `.concorde/protocol/`, the main-session guidance as the
Claude Code skill `.claude/skills/concorde/SKILL.md` and a block in `CLAUDE.md`, and the
[`d2`](https://github.com/d2lang/d2) program that renders your Specs' diagrams as
`.concorde/tools/d2`, a pinned release whose checksum it verifies (`--without-d2` skips it). With
`--pi` it also places the locked pi runtime, the pi run view and the pi skill. It never writes your
Specs. Then open Claude Code or pi in the project and talk to it: it is now the main agent.
Workers run on the same program as the main agent; ask it to change the models they use and it lets
you choose from what your Claude Code or pi installation offers (`concorde workers`).

A typical change, as the main agent runs it:

```bash
concorde task open retry --goal "limit payment retries" --modules module.payments
concorde run understand --task retry --goal "how should retries be limited?" --plan
concorde run specify    --task retry --intent "state the retry limit"
concorde run implement  --task retry --goal "implement the retry limit"
concorde run validate   --task retry
concorde run delivery   --task retry
concorde task merge retry
```

[Using Concorde](docs/using-concorde.md) walks through installation, the first Spec, checks and
this workflow in detail.

## The docsite

The **[published docsite](https://ftod.github.io/concorde/)** opens on Concorde's user documents
under [`docs/`](docs/README.md), then renders Concorde's own Specs and the Spec Protocol. To
preview it locally with Node.js 20+ and the [`d2`](https://github.com/d2lang/d2/releases) program
on `PATH`, which renders the Specs' diagrams (the Concorde installer places `d2` in projects it
installs into):

```bash
python3 scripts/concorde.py build
npm --prefix docsite ci
npm --prefix docsite run start -- --host 127.0.0.1 --no-open
```

For your own project, [scaffold a docsite](docsite/README.md#scaffold-a-docsite) with
`concorde docsite --propose` and then `--apply`.

## The Spec Protocol in brief

Concorde's independent **[Spec Protocol 13.0.0](protocol/README.md)** has two purposes: a human
understands a project's backbone from its Specs without reading code, and a harness derives from
the Specs exactly what each AI task may read and write. A Module's entry answers five questions in
order — **Purpose**, **Terminology**, **Usage**, **Design**, **Relationships** — and every node and
relation is declared exactly once. A Module's context is computed from its own declarations, one
level deep, and its write sets are its own documents and the files its realizations bind. Since
version 12 the Protocol also defines the six **task types** and the access level each assigns to
every boundary set.

## Develop Concorde

```bash
uv sync --locked --group dev
python3 scripts/concorde.py build
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
.venv/bin/python -m pytest                          # parallel by default; -n 0 runs in-process
CONCORDE_LIVE_CLAUDE=1 .venv/bin/python -m pytest tests/concorde/harness/workers/test_live.py
CONCORDE_LIVE_PI=1 .venv/bin/python -m pytest tests/concorde/harness/workers/test_pi_live.py
```

The last two commands run a real worker to check what only the agent itself enforces: the first
needs a logged-in Claude Code and costs a few cents; the second needs a configured pi
(`CONCORDE_LIVE_PI_MODEL` names the model) and the pi runtime, from `install-concorde.py --pi` or
`CONCORDE_SANDBOX_RUNTIME`. Never edit build output under `generated/`; change the
sources (`prompts/`, `protocol/`, `src/`) and rebuild. See the [source-checkout rules](AGENTS.md) and
[Concorde's own Specs](specs/concorde/module.md).

---

[MIT licensed](LICENSE). Built with Concorde's own [Specs](specs/concorde/module.md).
