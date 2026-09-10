<p align="center">
  <img src="docs/assets/concorde-hero.svg" alt="Concorde — Specify the architecture. Understand the system. Guide your agents." width="100%" />
</p>

<p align="center">
  <a href="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml"><img src="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml/badge.svg" alt="Source validation" /></a>
  <a href="protocol/README.md"><img src="https://img.shields.io/badge/Spec_Protocol-4.0.0-6264e8" alt="Spec Protocol 4.0.0" /></a>
  <a href="#get-started"><img src="https://img.shields.io/badge/agents-Codex_%C2%B7_Claude-273449" alt="Integrations: Codex and Claude" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-273449" alt="MIT license" /></a>
</p>

<p align="center">
  <a href="#why-concorde"><strong>Why Concorde</strong></a> ·
  <a href="#get-started"><strong>Get started</strong></a> ·
  <a href="https://ftod.github.io/concorde/"><strong>Explore the Specs</strong></a> ·
  <a href="docs/workflow-guide.md"><strong>Workflow guide</strong></a>
</p>

# Concorde

**Architecture-aware Specs, project understanding, and scoped agents for Codex and Claude.**

Concorde helps you write and maintain software Specs that explain both behavior and architecture:
what each Module is responsible for, how its entities relate, what it depends on, and which files
realize it. These Specs give people a way to understand the project and agents a clear contract
to work within as the software evolves.

The framework brings together a Spec docsite, an Understand Anything graph view, explicit agent
context and permissions, and a small set of built-in agents for specification and development.

## Why Concorde

### 1. Write and maintain architecture-aware Specs

A Module Spec describes purpose, requirements, scenarios and architecture together. Its entities,
relationships, dependencies and implementation file bindings make software structure explicit.
Concorde supports authoring, reviewing and updating these Specs, checking their consistency, and
tracking which Module contracts are affected as shared code changes.

### 2. Understand the project and observe the work

The **[docsite](docsite/README.md)** publishes Specs with Module navigation, composition and
dependency graphs, and inline architecture diagrams. The **[Understand Anything graph
view](viewer/README.md)** lets you explore an existing code graph; Concorde can export a graph
from its Spec registry or overlay Module structure onto an existing graph. Opening the viewer
does not itself analyze code or generate a graph.

Recorded context, checks and reviews show what each agent could see and change and what evidence
supports its work. Optional [LangGraph Studio](scripts/development/STUDIO.md) exposes execution
graphs and live events.

### 3. Guide agents with Specs and explicit permissions

Each subagent should receive the information and authority its task needs. A bounded task gets
its Module's complete Spec collection, with file access narrowed by phase. Planners reason from
the Spec; code writers receive the declared implementation files. The host enforces these
boundaries, and a dependency never silently imports another Module's context.

The design premise is that good results within these limits increase confidence in both the
solution and the architecture: the agent can work from the declared contract without relying on
hidden implementation knowledge or changes outside its responsibility. That is useful evidence
that the Spec is sufficient and the Modules are well decoupled. It is not a proof of correctness;
tests and review still matter. Missing promises are reported as Spec gaps.

### 4. Use built-in agents for everyday development

Concorde includes three basic agents: a **coordinator** for questions, routing and topology design;
a **Spec engineer** for authoring, reviewing, planning and task definition; and a **programmer** for
implementation, code review and investigation. Public Skills compose them into workflows with
explicit context and permissions for each invocation.

## A development workflow using these foundations

```text
Request → Route → Specify → Review Spec → Plan → Tasks → Implement → Validate / Review
                                                                         ↓
                                                                   Ready candidate
                                                                         ↓
                                                             Deliver → Merge on request
```

The default development loop authors the Spec and runs reviews. `specify=false` uses the existing
Spec; `run_reviews=false` records explicit review skips. A skipped review remains distinguishable
from a successful one. Missing contracts and failed checks preserve inspectable progress for the
next invocation.

You can also ask questions against selected Specs or run a standalone Spec or code review without
starting a development change.

## Get started

You need a Git project, Python **3.11+**, Node.js **18+** and npm for the installer-managed runtime,
plus your chosen agent client. Configured checks currently require **Linux with bubblewrap**,
working namespaces and pidfd support. The optional docsite requires Node.js **20+**.

**1. Clone and build Concorde.**

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
```

**2. Preview the installation into your project, then apply it.** Replace `/absolute/path/to/project`
with your existing Git project's path; use `claude` instead of `codex` for Claude.

```bash
python3 scripts/install-concorde.py --target /absolute/path/to/project --integration codex --preview
python3 scripts/install-concorde.py --target /absolute/path/to/project --integration codex --apply
```

The installer provisions the locked runtime, installs the public Skills and adds Protocol guidance
to the selected root instruction file. It preserves user content outside its owned entries.

**3. Open an agent session in your project and initialize it.**

```text
Use concorde-init to initialize this project. Propose the setup for my review.
```

Apply the reviewed proposal, then define the root Module's Purpose, Requirements, Scenarios and
Ontology. Initialization creates an honest stub; unresolved behavior still needs to be specified.
Commit the installed framework and root guidance so candidate worktrees inherit them.

**4. Explore and evolve your project.**

Use `concorde-main` to ask questions against selected Specs or design Module topology. Publish
the [docsite](docsite/README.md#scaffold-a-docsite) to browse the architecture. For a development
change, use the built-in loop:

```text
Use concorde-dev-loop to implement the next change described below: …
```

The host prepares a candidate worktree from committed HEAD. Continue in the fresh session it
hands off, with that worktree's own instructions. See the
[workflow guide](docs/workflow-guide.md#install-and-initialize) for typed JSON invocations,
initialization details and session handoffs.

## The contract at the center

Concorde's independent **Spec Protocol 4.0.0** defines one specification category: a **Module Spec**.
A Module describes a cohesive software responsibility; its implementation may span packages,
services or shared files.

| Part | The question it answers |
| :--- | :--- |
| **Purpose** | What is this Module for, and who uses it? |
| **Requirements** | What must it guarantee? Each requirement is one decidable `SHALL` statement. |
| **Scenarios** | What happens in a concrete situation? Testable `GIVEN` / `WHEN` / `THEN` steps. |
| **Ontology** | What exists, how does it relate, and which files realize it? Entities and labeled relationships. |

Tests declare the scenarios they verify. Concorde derives coverage from those declarations;
structural validation and declared coverage provide evidence, without proving semantic completeness.

Read the [Protocol](protocol/README.md), start from the
[Module template](protocol/templates/module.md), or explore
[Concorde's own Module Spec](specs/concorde/module.md) to see it applied to this repository.

## Choose an entry point

| You want to… | Use |
| :--- | :--- |
| Ask about the system or design its topology | `concorde-main` |
| Take a change through specification, implementation and checks | `concorde-dev-loop` |
| Review a Spec or diagnose code in a fresh read-only invocation | `concorde-review` |
| Inspect and act on recorded feedback | `concorde-reflections-triage` |
| Initialize or configure a project | `concorde-init` · `concorde-configure` |
| Validate a candidate or deliver a verified change | `concorde-validate` · `concorde-deliver` |

These eight public Skills expose the global and lifecycle capabilities. Internal stages are
composed by the host. See the [capability registry](specs/concorde/development/capabilities.md)
for the full interface.

## Explore and contribute

- **[Spec explorer](https://ftod.github.io/concorde/)** — published Protocol, Module contracts and relationship graphs.
- **[Workflow guide](docs/workflow-guide.md)** — JSON requests, review, delivery, enforcement and Protocol upgrades.
- **[LangGraph Studio](scripts/development/STUDIO.md)** — execution graphs, live events and debugging.
- **[Docsite](docsite/README.md) · [Code viewer](viewer/README.md)** — publish Specs and inspect an existing Understand Anything graph. Launching the viewer does not generate or validate that graph.
- **[Source-checkout policy](AGENTS.md)** — worktree ownership, maintenance and generated-output rules.

For source development, install the locked dependencies and run the deterministic checks:

```bash
uv sync --locked --group dev
python3 scripts/concorde.py build
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
python3 scripts/development/run-tests.py
```

See [development details](docs/workflow-guide.md#development) for targeted tests and docsite checks.

---

[MIT licensed](LICENSE). Built with Concorde's own [Specs](specs/concorde/module.md).
