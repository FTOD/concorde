<p align="center">
  <img src="docs/assets/concorde-hero.svg" alt="Concorde — Specify the architecture. Understand the system. Guide your agents." width="100%" />
</p>

<p align="center">
  <a href="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml"><img src="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml/badge.svg" alt="Source validation" /></a>
  <a href="protocol/README.md"><img src="https://img.shields.io/badge/Spec_Protocol-10.0.0-6264e8" alt="Spec Protocol 10.0.0" /></a>
  <a href="#get-started"><img src="https://img.shields.io/badge/clients-Claude_Code_%C2%B7_Codex_%C2%B7_Pi-273449" alt="Clients: Claude Code, Codex and Pi" /></a>
  <a href="#workflows-are-langgraph-graphs-you-can-inspect"><img src="https://img.shields.io/badge/graphs-LangGraph-273449" alt="Workflows are LangGraph graphs" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-273449" alt="MIT license" /></a>
</p>

<p align="center">
  <a href="#why-concorde"><strong>Why Concorde</strong></a> ·
  <a href="#get-started"><strong>Get started</strong></a> ·
  <a href="#explore-concorde"><strong>Docsite & Studio</strong></a> ·
  <a href="https://ftod.github.io/concorde/"><strong>Explore the Specs</strong></a> ·
  <a href="docs/workflow-guide.md"><strong>Workflow guide</strong></a>
</p>

# Concorde

**Architecture-aware Specs, and coding agents that work strictly within them.**

Concorde keeps a project's Specs at the center of AI-assisted development. A Spec explains what
each Module is responsible for, how it is designed, which precise promises it makes and which files
realize it. Every agent step then runs as a fresh, sandboxed worker that receives one Module's Spec
and only the files and permissions its phase needs. A change is made in its own candidate worktree,
checked and independently reviewed there, and delivered only when you ask.

You drive Concorde from the agent client you already use: **Claude Code** or **Codex** through
installed Skills, or the **Pi coding agent** through a `concorde` session tool. Every model-backed
step runs as a [Pi](https://www.npmjs.com/package/@earendil-works/pi-coding-agent) worker process,
and every workflow is a LangGraph graph you can open in LangGraph Studio.

## Why Concorde

### Specs that explain the architecture, not just the API

A **Module** is one cohesive responsibility, such as planning a change or publishing documentation.
It need not be a package or directory: its realization may span several, or be supplied entirely by
its child Modules. Each Module owns one complete Spec in two parts:

- **Module Specs** explain it for a reader who does not know the code: Purpose, Terminology,
  Usage, Design and Relationships, with a Mermaid diagram of how its entities collaborate.
- **Implementation Specs** hold the precise obligations: `SHALL` requirements, `GIVEN`/`WHEN`/`THEN`
  scenarios and structured interface contracts.

Every Markdown document has a paired `.md.json` metadata file that records its identity, owner and
role, the entities it explains and the files or directory prefixes that realize them. The registry
`.concorde/specs.json` records how Modules compose (`parent`), what they depend on (`uses`) and which
other documents they explicitly include as context (`references`). Tests declare the scenarios they
verify, so coverage is derived from the tests rather than from a list someone must maintain.
Concorde checks all of this for consistency and tracks which Module contracts a shared file affects.

### Each agent sees one Module's contract, and only what its phase needs

A worker bound to a Module receives four kinds of context, frozen for its invocation:

| Context | What it contains | Who receives it |
| :--- | :--- | :--- |
| **Spec** | The Module's own documents plus the ones it explicitly references, one level deep | Every phase |
| **Implementation** | The files bound by the Module's entities | Names for every phase; contents only for code writing and code review |
| **Resource** | Vendored, version-pinned documentation and source of the libraries it declares, such as LangGraph | Planning, task authoring, code writing and code review, read-only |
| **Task** | The request, constraints and the stage artifacts admitted for this phase | Every phase |

Planners and task authors reason from the Spec alone. If the Spec does not say something the task
needs, the worker reports a Spec gap as an Issue instead of guessing from code, and the dependent step
stops. The design premise is that good results within these limits are evidence that the Spec is
sufficient and the Modules are well decoupled. That is not a proof of correctness; tests and review
still matter.

### Permissions are enforced outside the model

Each model-backed step is one fresh Pi process (`pi --mode rpc`) for exactly one invocation, started
with sessions, project settings, Skills and discovered extensions disabled. Inside it, a tool gate
checks every tool call against the host's grant. Around it, a **bubblewrap sandbox** derived from
that grant makes the host filesystem read-only, masks the developer's secret locations, agent-client
state and every other worktree, and leaves only the write grant and the run directory writable, with
a private `/tmp` and process namespace. Only the programmer may write code, and only its Module's
listed files; reviewers and planners are read-only. Configured checks run in a separate read-only
sandbox. The known limits are stated in the [Harness Spec](specs/concorde/harness/module.md#usage):
the network is shared, the masked locations are a fixed list, and Linux with bubblewrap is required.
An unavailable sandbox refuses the launch rather than running the worker unconfined.

### Workflows are LangGraph graphs you can inspect

Concorde has one executable concept, the **Operation**: a LangGraph node with declared input State,
output State updates, effects, use conditions and execution policy. An Operation runs deterministic
code, calls a model, or runs a compiled graph of other Operations; `dev-loop` and `specify-loop` are
composed Operations. Every graph is built with LangGraph's Graph API and documented by a Graph Spec
whose diagram a deterministic check keeps equal to the compiled graph. Each Operation is explained,
with its Graph Spec, in the Specs of the Module that owns it; the same graphs appear in LangGraph
Studio, and every worker launch records its tokens, cost and wall time for
`python3 scripts/concorde.py usage`.

### Changes run in candidate worktrees and are delivered on request

A change requested from your primary worktree runs in a candidate worktree that the host creates from
the committed `HEAD`. Your session stays where it is and receives the candidate's result, including
its path, branch and `change_id`, with which you continue the change. A development loop stops at a
**ready** candidate. Delivery is a separate request that publishes the branch
`concorde/delivered/<change_id>`; merging into your primary branch needs another explicit request.

### Problems become tracked Issues

Workers record bugs, missing or conflicting promises and limitations as Git-versioned
[Issues](specs/concorde/issues/module.md) under `.concorde/issues/`. Reporting does not stop a worker
or authorize a repair. `concorde-issues` lists, shows, reports, reopens or solves an explicitly
selected Issue; solving uses the ordinary development and review Operations and stops at a verified
candidate, never at delivery.

## How a change flows

`concorde-dev-loop` runs in a candidate worktree created from the committed `HEAD`:

```text
Route ─▶ Specify ─▶ Review Spec ─▶ Plan ─▶ Tasks ─▶ Implement ─▶ Validate ─▶ Code review ─▶ Ready
                                             ▲                                    │
                                             └─ blocking findings, repairs left ──┘

Ready candidate ─▶ concorde-deliver ─▶ branch concorde/delivered/<change_id> ─▶ merge on request
```

| Step | Worker | Reads | May change |
| :--- | :--- | :--- | :--- |
| Route | `router` | The Specs it selects, starting from the entry Module | Nothing; selects the owning Module |
| Specify | `spec-author` | The Module's Spec context | Proposes Spec documents; the host validates and applies them |
| Review Spec | `spec-reviewer` | The Spec context, in a fresh conversation | Nothing; returns findings |
| Plan | `context-assessor`, then `planner` | Spec, resources and implementation file names | Nothing; a gap stops before planning |
| Tasks | `task-author` | Spec, resources and the accepted plan | Nothing; returns acceptance tasks |
| Implement | `programmer` | Spec, tasks, resources and the listed files | Only the Module's listed files |
| Validate | none (deterministic) | Configured checks in a read-only sandbox | Records evidence |
| Code review | `code-reviewer` | Spec and the authorized code, read-only | Nothing; returns findings |

`specify=false` works from the existing Spec, and `run_reviews=false` records explicit review skips
that stay distinguishable from successful reviews. A Spec gap, a failed check or an exhausted repair
budget stops with inspectable progress that the next invocation resumes from its current evidence.
`concorde-specify-loop` runs only the first three steps; `concorde-main` answers questions without
starting a change.

## Get started

**Requirements.** A Git project on **Linux with [bubblewrap](https://github.com/containers/bubblewrap)**,
working user, mount and PID namespaces and pidfd support: every worker and every configured check
runs inside it. **Python 3.11+**, **Node.js 18+** and npm, used for the managed runtime and the Agent
Skills CLI. The [Pi coding agent](https://www.npmjs.com/package/@earendil-works/pi-coding-agent) on
`PATH` (`npm install -g @earendil-works/pi-coding-agent`; Concorde is developed against 0.85.1),
logged in with `pi` then `/login`: workers use that login and Pi's own model providers. The optional
docsite needs Node.js **20+**.

**1. Clone and build Concorde.**

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
```

**2. Preview the installation into your project, then apply it.** Use `--integration claude`,
`codex` or `pi`; repeat the option to set up several clients in one project.

```bash
python3 scripts/install-concorde.py --target /absolute/path/to/project --integration claude --preview
python3 scripts/install-concorde.py --target /absolute/path/to/project --integration claude --apply
```

The installer provisions a locked managed runtime at `.concorde/.venv`, deploys the framework to
`.concorde/framework/`, places the Protocol at `.concorde/protocol/` and adds a guidance block to
each selected client's root instruction file (`CLAUDE.md` or `AGENTS.md`). For Claude Code and Codex
it runs the standard [Agent Skills CLI](https://github.com/vercel-labs/skills) (`npx skills add`,
pinned by the package) so the Skills land in each tool's usual layout; for Pi it installs a session
extension under `.pi/extensions/` whose `concorde` tool runs the same Operations. It preserves your
content outside the entries it owns, and the Skills need no Concorde dependencies in your own
`python3`: the launcher re-runs itself inside the managed runtime.

**3. Commit the installation, then initialize the project.** Every change, initialization included,
runs in a candidate worktree created from the committed `HEAD`, so commit the installed framework and
root guidance first. Then, in an agent session inside your project:

```text
Use concorde-init to initialize this project. Propose the setup for my review.
```

Review the proposal and ask to apply it. Applying runs in a candidate worktree and returns its path,
branch and `change_id`. It records the Pi model and thinking level your workers use (change them later
with `concorde-configure`) and creates an honest stub of the root Module Spec. Complete the stub's
Purpose, Terminology, Usage, Design and Relationships in that candidate, then bring it into your
primary branch with `concorde-validate`, `concorde-deliver` and a separate merge request.

**4. Ask, specify and develop.**

```text
Use concorde-main to explain how requests reach the storage layer.
Use concorde-dev-loop to implement the change described below: …
```

In Pi, ask the session to use the `concorde` tool for the same Operations. See the
[workflow guide](docs/workflow-guide.md) for typed JSON requests, delivery, topology changes and
Protocol upgrades.

## Choose an entry point

| You want to… | Use |
| :--- | :--- |
| Ask about the system, route a task or design Module topology | `concorde-main` |
| Write or revise a Spec and have it reviewed before implementation | `concorde-specify-loop` |
| Take a change through specification, implementation and checks to a ready candidate | `concorde-dev-loop` |
| Review a Spec or code in a fresh read-only invocation | `concorde-review` |
| Report, inspect, reopen or solve an Issue | `concorde-issues` |
| Initialize a project or change the worker model | `concorde-init` · `concorde-configure` |
| Validate a candidate or deliver a verified change | `concorde-validate` · `concorde-deliver` |

These nine public Operations are the Skills (or the Pi tool's operations). Every one also accepts
`mode: "describe-policy"`, which previews the exact context and permissions each stage would receive
without starting a worker.

## Explore Concorde

### The docsite

The **[published docsite](https://ftod.github.io/concorde/)** renders Concorde's own Specs. Its tabs
are **Module Specs** (the explanatory entries, navigated by Module parentage), **Implementation
Specs** (requirements, scenarios, contracts and Graph Specs of the same Modules) and **Spec
Protocol**; there is no separate graph page. To preview it locally with Node.js 20+:

```bash
python3 scripts/concorde.py build
npm --prefix docsite ci
npm --prefix docsite run start -- --host 127.0.0.1 --no-open
```

Open [localhost:3000/concorde/](http://localhost:3000/concorde/). `npm --prefix docsite run build`
produces a verified static site in `docsite/build/`.

![Concorde's docsite showing the root Module Spec's Purpose and Terminology, the Module tree and the four documentation tabs](docs/assets/concorde-docsite.png)

For your own project, [scaffold a docsite](docsite/README.md#scaffold-a-docsite) with
`python3 .concorde/framework/scripts/concorde.py docsite --propose` and then `--apply`; add
`--github-pages` for a deployment workflow.

### LangGraph Studio

Start Concorde's local Agent Server with the locked Studio dependencies:

```bash
uv sync --locked --group studio
python3 scripts/concorde.py build
uv run --locked --group studio langgraph dev \
  --config generated/langgraph.json --host 127.0.0.1 --port 2024 \
  --n-jobs-per-worker 1 --no-browser
```

Open **[LangGraph Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)**, sign
in to LangSmith for run interactions and allow local network access if your browser asks. Select
**concorde-main**, create a thread, choose **View Raw** and submit this policy preview:

```json
{
  "invocation": {
    "type_id": "concorde-operation-invocation",
    "schema_version": 3,
    "operation_id": "concorde-main",
    "mode": "describe-policy",
    "configuration": null,
    "input": {
      "type_id": "concorde-main-request",
      "schema_version": 1,
      "data": {
        "task": "Explain Concorde's workflow host",
        "target_id": "module.development"
      }
    }
  }
}
```

It shows the admitted permissions without starting a worker. With `mode` set to `execute`, the
question runs through a Pi worker with the project's configured model and your Pi login; inspect
**result**, **policies** and **events** in the state. Events report operation, stage and worker
starts, completions and failures, not token-level traces of a worker's reasoning.

![LangGraph Studio connected to Concorde's local server, showing the concorde-main graph and policy-preview input](docs/assets/concorde-studio.png)

To send ordinary Skill or CLI invocations through the server, set
`export CONCORDE_STUDIO_URL=http://127.0.0.1:2024` in the shell that launches them; the launcher
prints the Studio thread and run IDs. See the [Studio guide](scripts/development/STUDIO.md) for
debugging and [installed-project setup](scripts/development/STUDIO.md#consumer-project-setup).

## The Spec Protocol in brief

Concorde's independent **[Spec Protocol 10.0.0](protocol/README.md)** defines one specification
category, the Module Spec, and which part of it is written for human reading. A Module's reading entry
`module.md` answers five questions in order:

| Section | The question it answers |
| :--- | :--- |
| **Purpose** | What responsibility does this Module own, for whom and within which scope? |
| **Terminology** | Which concepts does the reader need, each defined once in its canonical table? |
| **Usage** | When and how is it used, with which inputs, results, errors and limits? |
| **Design** | How do its decomposition, state and constraints fulfill its guarantees, and why? |
| **Relationships** | Which entities collaborate, under which conditions, as a labeled Mermaid view? |

Explanatory topics join the entry with `document.role: module`. Formal requirements, scenarios and
structured contracts live only in companions with `document.role: implementation`, owned by the same
Module. Both roles are normative reading and both enter agent context whole; the docsite simply shows
them in parallel tabs. A Module's context is its own documents plus its explicit `references`,
expanded exactly one level: a Markdown link never adds a file to what an agent may read, and a
metadata-only edit invalidates the reviews that relied on it. Structural validation and declared test
coverage are evidence, not proof of semantic completeness.

Start from the [Protocol](protocol/README.md), the [Module template](protocol/templates/module.md)
or [Concorde's own root Spec](specs/concorde/module.md), which applies it to this repository.

## Under the hood

### Operations

Concorde defines **26 Operations**, listed in [`operations/`](operations/__init__.py); the
[operation registry](specs/concorde/development/operations.md) describes their contracts. Nine are
public, fourteen are host-adapted, and twelve are model-backed Operations whose execution profile
names a Pi worker:

| Model-backed Operation | Responsibility and authority |
| :--- | :--- |
| `answerer` · `router` · `topology-designer` | Answer questions, select the owning Module or design topology from selected complete Specs; no implementation contents, no writes. |
| `spec-author` · `topology-author` | Propose Spec or topology documents that the host validates and applies. |
| `spec-reviewer` · `context-assessor` | Review a Spec independently or assess whether its context is sufficient; read-only. |
| `planner` · `task-author` | Produce a plan and acceptance tasks without reading source contents. |
| `programmer` | Implement tasks, writing only the selected Module's listed files. |
| `code-reviewer` | Review code independently; authorized code read-only. |
| `issue-solver` | Choose bounded work or an evidence-grounded disposition for one selected Issue. |

The host-adapted Operations are the nine public ones plus `specify`, `context-solve`, `plan`,
`tasks` and `implement`, which `dev-loop` composes. Four of them (`init`, `configure`, `validate`
and `deliver`) never call a model. Each model-backed Operation keeps its role instructions in
`operations/<name>/spec.md` and its profile (task contract, workspace kind, Pi tools, children and
timeout) in `operations/<name>/__init__.py`. A worker with declared children can delegate one level
deep, in the foreground and with fresh context: the spec reviewer to `fact-check` and `consistency`,
the planner to `scout`, the programmer to `scout`, `planner` and `verifier`, and the code reviewer to
`scout` and `verifier`. See [Operations and Harnesses](specs/concorde/harness/agents-and-harnesses.md).

### Launchers and tools

Commands are relative to this checkout; installed projects use the same scripts under
`.concorde/framework/`.

| Entry point | Use |
| :--- | :--- |
| `python3 scripts/run-operation.py <operation> < invocation.json` | Submit a typed request to one of the nine public Operations, in `execute` or `describe-policy` mode. |
| `python3 scripts/concorde.py build` · `validate` | Render workers, Skills and schemas; run the Spec, Operation, contract and build-output checks. |
| `python3 scripts/concorde.py skills --write` · `protocol-manifest` | Render the published Skills under `skills/`; accept a changed Protocol bundle. |
| `python3 scripts/concorde.py docsite` · `usage` | Scaffold a project docsite; summarize recorded worker usage per run. |
| `python3 scripts/install-concorde.py` | Preview or apply installation into a project. |
| `python3 scripts/issues.py` | Inspect branch-local Issues from the command line. |
| [LangGraph Studio](scripts/development/STUDIO.md) | Run and observe the same public graphs through the shared host. |
| `npm --prefix docsite run <script>` | `start`, `build`, `validate`, `typecheck`, `test`, `check`. |

The CLI `validate` command checks the project directly; the `concorde-validate` Operation also
records readiness evidence for a candidate.

## Develop Concorde

```bash
uv sync --locked --group dev
python3 scripts/concorde.py build
python3 scripts/development/init-references.py   # vendored references under reference/
npm ci --prefix pi                                # the Pi extensions workers load
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
python3 scripts/development/run-tests.py
```

Concorde is developed by direct maintenance in this checkout. Its own graphs run on this repository
only when you explicitly ask for one, so the `concorde-*` Skills built here are user-invoked only.
Never edit build output (`generated/`, the Skill projections or the rendered `skills/`); change
`prompts/`, `operations/` or `pi/extensions/` and rebuild. See the
[source-checkout policy](AGENTS.md) and [development details](docs/workflow-guide.md#development).

---

[MIT licensed](LICENSE). Built with Concorde's own [Specs](specs/concorde/module.md).
