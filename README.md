<p align="center">
  <img src="docs/assets/concorde-hero.svg" alt="Concorde — Specify the architecture. Understand the system. Guide your agents." width="100%" />
</p>

<p align="center">
  <a href="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml"><img src="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml/badge.svg" alt="Source validation" /></a>
  <a href="protocol/README.md"><img src="https://img.shields.io/badge/Spec_Protocol-7.0.0-6264e8" alt="Spec Protocol 7.0.0" /></a>
  <a href="#get-started"><img src="https://img.shields.io/badge/agents-Codex_%C2%B7_Claude-273449" alt="Integrations: Codex and Claude" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-273449" alt="MIT license" /></a>
</p>

<p align="center">
  <a href="#why-concorde"><strong>Why Concorde</strong></a> ·
  <a href="#get-started"><strong>Get started</strong></a> ·
  <a href="#explore-concorde"><strong>Docs, graphs & Studio</strong></a> ·
  <a href="https://ftod.github.io/concorde/"><strong>Explore the Specs</strong></a> ·
  <a href="docs/workflow-guide.md"><strong>Workflow guide</strong></a>
</p>

# Concorde

**Architecture-aware Specs, project understanding, and scoped Pi worker agents, invoked from Codex or Claude.**

Concorde helps you write and maintain software Specs that explain both behavior and architecture:
what each Module is responsible for, how its entities relate, what it depends on, and which files
realize it. These Specs give people a way to understand the project and agents a clear contract
to work within as the software evolves.

The framework brings together a Spec docsite, an Understand Anything graph view, LangGraph Studio
support for observing agent execution, explicit agent context and permissions, and a small set of
built-in agents for specification and development. A reflection system retains feedback and Spec
gaps so they can be investigated and carried into future improvements.

## Why Concorde

### 1. Write and maintain architecture-aware Specs

A Module Spec describes purpose, requirements, scenarios and architecture together. Its entities,
relationships, dependencies and implementation file bindings make software structure explicit.
Concorde supports authoring, reviewing and updating these Specs, checking their consistency, and
tracking which Module contracts are affected as shared code changes.

### 2. Understand the project and observe agent execution

The **[docsite](docsite/README.md)** publishes reading content with Module navigation and scoped inline relationship diagrams, while keeping
metadata in an auxiliary provenance view. The **[Understand Anything graph
view](viewer/README.md)** lets you explore an existing code graph; Concorde can export a graph
from its Spec registry or overlay Module structure onto an existing graph. Opening the viewer
does not itself analyze code or generate a graph.

**Agent observability** covers the working process as well as its results. Concorde supports
**[LangGraph Studio](scripts/development/STUDIO.md)** to inspect execution graphs and follow live
stage and agent-process events: when work starts, finishes or fails. Recorded context, permission
policies, checks and reviews show what each agent could see and change and what evidence supports
its work. Studio is an optional interface for running and debugging these same workflows.

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

Concorde defines twelve Pi workers, one per lifecycle role: **answerer**, **router** and
**topology-designer** for questions, routing and topology design; **spec-author**,
**topology-author**, **spec-reviewer**, **context-assessor**, **planner** and **task-author** for
authoring, reviewing, planning and task definition; and **programmer**, **code-reviewer** and
**investigator** for implementation, code review and investigation. Each worker is one Pi coding
agent process (`pi --mode rpc`) run for exactly one invocation. Public Skills compose them into
workflows with explicit context and permissions for each invocation.

### 5. Turn feedback into tracked improvements

The **[reflection system](specs/concorde/reflections/module.md)** keeps project feedback and
persistent Spec gaps as records attributed to a Module or scenario. Use
`concorde-reflections-triage` to inspect the queue, capture selected gaps, investigate problems and
turn an approved resolution into a fresh development task.

Each record retains the observation, evidence, investigation and developer comments, so the
problem remains available across sessions. Investigation uses the responsible Module's context
and authorized files. Developers explicitly decide whether to resolve or dismiss a report;
finishing a repair does not automatically close it.

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
and the [Pi coding agent](https://www.npmjs.com/package/@earendil-works/pi-coding-agent)
(`npm install -g @earendil-works/pi-coding-agent`; Concorde is developed against 0.85.1) on `PATH`,
logged in with `pi` then `/login` — every Concorde worker runs as one Pi process using that login
and Pi's own model providers. Configured checks currently require **Linux with bubblewrap**,
working namespaces and pidfd support. The optional docsite requires Node.js **20+**.

**1. Clone and build Concorde.**

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
npm ci --prefix pi
```

`npm ci --prefix pi` installs pi-subagents, used for one level of worker delegation; the installer
provisions it into an installed project's managed runtime automatically.

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

Apply the reviewed proposal, then write the root Module's Purpose, Usage, Design and Relationships,
with precise requirements/scenarios and the paired metadata declarations. Initialization creates an honest stub; unresolved behavior still needs to be specified.
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

## Explore Concorde

Try **[Concorde's published docsite](https://ftod.github.io/concorde/)**. The screenshots below
show Concorde's own Specs, graph data and local Studio integration
([screenshot sources](docs/assets/README.md)). Commands in this section run
from the Concorde repository root unless an installed-project example is explicitly labeled.

### Run the docsite

With Node.js **20+**, preview the registered Specs locally:

```bash
python3 scripts/concorde.py build
npm --prefix docsite ci
npm --prefix docsite run start -- --host 127.0.0.1 --no-open
```

Open [localhost:3000/concorde/](http://localhost:3000/concorde/). Use **Module Specs** to navigate
the Module tree and read each Module's purpose, requirements, scenarios and architecture diagrams.
The **Spec Protocol** tab explains the specification language. To create a verified static site,
run `npm --prefix docsite run build`; the output is `docsite/build/`.

![Concorde's published docsite showing a Module Spec and its navigation](docs/assets/concorde-docsite.png)

For another initialized project, follow [Scaffold a docsite](docsite/README.md#scaffold-a-docsite),
then run the same npm commands from that project's root. Its URL follows `docsite/site.json`.

### Use the graph views

**Module architecture:** open a Module's reading entry in **Module Specs**. Purpose and Usage
introduce the responsibility, Design explains its realization, and Relationships shows scoped
collaboration diagrams. The sidebar follows Module parentage. There is no separate docsite Graph
tab; the independent Understand Anything export/viewer below provides code-graph exploration.

**Code relationships:** open the Understand Anything viewer. In this source checkout, install
the pinned viewer and export a graph from Concorde's Spec registry:

```bash
npm --prefix viewer ci --ignore-scripts
python3 scripts/concorde.py ua-graph --allow-primary-worktree
node viewer/node_modules/understand-anything-viewer/bin/viewer.mjs . --no-open
```

Open the complete **Dashboard URL** printed by the viewer, including its access token. Select a
layer to explore its files, search for a node, and select it to inspect details and connections.
Use **Fit View** to recenter, or **Learn** and **Start Tour** when the loaded graph includes a tour.

The exporter creates a Spec-derived graph when none exists, or overlays Module structure onto an
existing Understand Anything graph. It does not analyze source code. The screenshot uses
Concorde's existing Understand Anything analysis, which includes code relationships and a tour.
The `--allow-primary-worktree` flag explicitly allows this graph export in the primary checkout.

![Understand Anything exploring Concorde's code graph](docs/assets/concorde-code-graph.png)

In a project where Concorde is **installed**, use its managed viewer instead. Run from that
project's root:

```bash
python3 .concorde/framework/scripts/concorde.py ua-graph --allow-primary-worktree
python3 .concorde/framework/scripts/run-ua-graph-viewer.py --project-root . --no-open
```

See the [graph exporter](specs/concorde/views/ua-graph.md) and
[viewer guide](viewer/README.md) for graph locations and runtime details.

### Observe runs in LangGraph Studio

Start Concorde's local Agent Server using the locked Studio dependencies:

```bash
uv sync --locked --group studio
python3 scripts/concorde.py build
uv run --locked --group studio langgraph dev \
  --config generated/langgraph.json --host 127.0.0.1 --port 2024 \
  --n-jobs-per-worker 1 --no-browser
```

Open **[LangGraph Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)**
and sign in to LangSmith for run interactions. Allow access to the local network if your browser
asks. Select **concorde-main**, create a new thread, choose **View Raw** in the input editor, and
submit this policy preview:

```json
{
  "invocation": {
    "type_id": "concorde-capability-invocation",
    "schema_version": 3,
    "capability_id": "concorde-main",
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

This inspects admitted permissions without starting a worker. Change `mode` to `execute` to run
the question through a Pi worker, using the project's configured model and thinking level and the
developer's own Pi login. Inspect **result**,
**policies** and **events** in the state; execution emits capability, stage and agent-process
events, including starts, completions and failures. These are process events, not token-level
traces of the agent's internal reasoning or tool calls.

![LangGraph Studio connected to Concorde's local server, showing the concorde-main graph and policy-preview input](docs/assets/concorde-studio.png)

The screenshot shows the connected graph and input setup, before submitting a run.

To observe new CLI or Skill invocations in Studio, set this in the shell that launches them:

```bash
export CONCORDE_STUDIO_URL=http://127.0.0.1:2024
```

Keep using the usual Skills and JSON requests. The launcher prints the Studio thread and run IDs
to stderr; open that thread in Studio. The caller and server must belong to the same project and
worktree. `unset CONCORDE_STUDIO_URL` restores local execution without the server.

See the [Studio guide](scripts/development/STUDIO.md) for debugging, results and setup in
[installed consumer projects](scripts/development/STUDIO.md#consumer-project-setup), and the
[official Studio setup](https://docs.langchain.com/oss/python/langgraph/studio) for account setup.

## The contract at the center

Concorde's independent **Spec Protocol 7.0.0** defines one specification category: a **Module Spec**.
A Module describes a cohesive software responsibility; its implementation may span packages,
services or shared files. Each Spec document has one owning Module. A Module's explicit
`references` includes other Module-owned documents or one registered document, expanded once;
Markdown links remain navigation. Shared interfaces have one definition and local participant bindings.

The repository's Specs, runtime admission, context serialization and publication support
Protocol 7/Profile 14/registry schema 5. Resolved contexts retain unique owners, one-level reference
provenance and exact byte digests without granting provider implementation access; see
[Spec context queries](specs/concorde/spec/registry.md#stable-id-spec-context-queries).
Runtime and publication tests verify these boundaries separately from the rule build.

Concorde's own docsite includes an **Agent Flows** tab at `/concorde/agent-flows`, showing the actual
executable LangGraph Flows, expanded Studio entries and routing handoffs with links to the Specs. This page
is excluded from consumer site templates. Build the checkout with the development Python
environment (`.venv`, or `CONCORDE_PYTHON` for a source copy) and `npm --prefix docsite run build`.

The Protocol defines **complete content** and its **human-readable subset**. A registered
`module.md` and `module.md.json` form one document unit with one identity and owner. The Markdown
explains meaning; metadata records identity, ownership and implementation mappings and points to
local readable explanations rather than copying them. Both members enter complete agent context,
and a metadata-only edit invalidates affected context/review identities.

| Reading section | The question it answers |
| :--- | :--- |
| **Purpose** | What responsibility does this Module own, for whom and within which scope? |
| **Usage** | When and how should a consumer use it, with which inputs, outcomes and limits? |
| **Design** | How do responsibilities, state, flow and constraints fulfill its guarantees? |
| **Relationships** | Which entities collaborate, under which conditions, and how does dependency differ from composition? |

Requirements, scenarios and interface agreements remain precise readable obligations, placed later
or in registered companions. Internal constraints are not weakened by their location. Diagrams
may show a scoped subset of entities; there is no separate entity-inventory reading chapter.
A logical Module need not invent a public API. The Protocol defines reading membership and
completeness, not docsite pages, sidebars, folding or interactions.

Tests declare the scenarios they verify. Concorde derives coverage from those declarations;
structural validation and declared coverage provide evidence, without proving semantic completeness.

Read the [Protocol](protocol/README.md), start from the
[Module template](protocol/templates/module.md), or explore
[Concorde's own Module Spec](specs/concorde/module.md) to see it applied to this repository.

## Choose an entry point

| You want to… | Use |
| :--- | :--- |
| Ask about the system or design its topology | `concorde-main` |
| Write or revise a Spec and review it before implementation | `concorde-specify-loop` |
| Take a change through specification, implementation and checks | `concorde-dev-loop` |
| Review a Spec or diagnose code in a fresh read-only invocation | `concorde-review` |
| Track feedback and Spec gaps, investigate problems and act on approved resolutions | `concorde-reflections-triage` |
| Initialize or configure a project | `concorde-init` · `concorde-configure` |
| Validate a candidate or deliver a verified change | `concorde-validate` · `concorde-deliver` |

These nine public Skills expose selected Capabilities. Other Capabilities are composed by the host. See the [capability registry](specs/concorde/development/capabilities.md)
for the full interface.

## Agents, capabilities and executable entry points

Concorde currently defines **12 Pi workers, 14 capabilities and 9 public Skills**. Capabilities
orchestrate execution; workers perform the steps that need model judgment, each running as one Pi
coding agent process for exactly one invocation. Public Skills provide instructions for invoking
those capabilities from the developer's agent client.

### Workers

| Worker | Phase / action | Responsibility and authority |
| :--- | :--- | :--- |
| `answerer` | route / ask | Answer questions from selected complete Module Specs; read-only, no routes or writes. |
| `router` | route / route | Select the one owning Module route; no implementation contents or writes. |
| `topology-designer` | route / design-topology | Design candidate topology from selected complete Specs and the explicit inventory; no implementation contents or writes. |
| `spec-author` | specify | Author structured Spec document replacements; the host applies them. |
| `topology-author` | topology-author | Produce candidate-owned topology documents for host application. |
| `spec-reviewer` | spec-review | Independent Spec review findings; read-only. |
| `context-assessor` | context-solve | Assess Module context sufficiency; no authored artifacts. |
| `planner` | plan | Produce an implementation plan; no source contents or writes. |
| `task-author` | tasks | Derive implementation acceptance tasks from the accepted plan; no source contents or writes. |
| `programmer` | implementation | Implement tasks; may write only the selected Module's listed implementation files. |
| `code-reviewer` | code-review | Independent code review findings; authorized code read-only. |
| `investigator` | implementation (reflection) | Investigate a reflection selection; authorized code read-only. |

Each worker is `agents/<name>/spec.md` (its role Spec) plus `agents/<name>/__init__.py` (its
profile: task contract, workspace, Pi tools, children, timeout). Definitions live in
[agents/](agents/__init__.py); the [Agents and Harnesses](specs/concorde/harness/agents-and-harnesses.md)
Spec is the authoritative catalog. Each worker fulfils exactly one task contract, and each
invocation receives fresh, explicitly bounded context and permissions.

### Capability inventory

| Capability | Behavior | Public Skill |
| :--- | :--- | :--- |
| `main` | Answer questions, route requests, and design and apply accepted topology changes. | `concorde-main` |
| `specify-loop` | Route a change, author or revise its Spec, and independently review it before implementation. | `concorde-specify-loop` |
| `dev-loop` | Call specify-loop, then plan, implement, validate and review code to a ready candidate. | `concorde-dev-loop` |
| `review` | Run a standalone Spec or code review, including source diagnosis. | `concorde-review` |
| `reflections-triage` | Inspect feedback, capture gaps, investigate, implement resolutions and manage owned records. | `concorde-reflections-triage` |
| `init` | Propose and apply project initialization with a pinned Protocol. | `concorde-init` |
| `configure` | Apply the project's Pi worker model/thinking selection and, on request, accept an updated Protocol binding. | `concorde-configure` |
| `validate` | Run deterministic Spec and configured code checks and record readiness. | `concorde-validate` |
| `deliver` | Stage a verified candidate on its own branch and clean up; merge into the primary branch on a separate explicit request. | `concorde-deliver` |
| `specify` | Author Spec replacements for the bound Module. | — |
| `context-solve` | Validate Module participant routing and assess context sufficiency. | — |
| `plan` | Assess sufficiency and produce a revision-bound plan. | — |
| `tasks` | Derive acceptance tasks from the accepted plan. | — |
| `implement` | Implement component tasks or coordinate participating components. | — |

Four Capabilities make no model calls; the other ten may call a model. The nine public Skills
each expose one Capability. The five non-public Capabilities have no standalone
launcher and are reachable only through declared host composition. Current workers have no admitted
Capability references of their own; the host composes the workflows.

Each Capability declares public exposure, context selection (`discover`, `bound` or `none`),
determinism, launched Agents and composed capabilities independently. A Flow organizes calls,
branches and loops; “stage” describes a position in execution, not a type of Capability.

The source inventory is [capabilities/](capabilities/__init__.py); the
[capability registry](specs/concorde/development/capabilities.md) describes the contracts.

### Harness

A Harness is context, control flow, models and per-worker permissions and environment: the shared
part is the host environment allowlist, the Pi worker runtime and the LangGraph Flows that
orchestrate workers; the per-worker part is each worker's profile — its workspace kind (`capsule`
for Spec-only work, `project` for work that reads or writes implementation files), Pi tools,
children and timeout. The host compiles effective permissions from the worker's contract and its
own grant for each invocation; a worker's Pi process starts with sessions, project settings, skills
and discovered extensions disabled. See the
[shared environment](src/concorde/harness/harness.py) and the
[Agents and Harnesses](specs/concorde/harness/agents-and-harnesses.md) Spec.

### Launchers and supporting tools

Commands below are relative to this source checkout. Installed projects use the corresponding
scripts under `.concorde/framework/`; Studio and development setup are documented separately.

| Entry point | Available operations |
| :--- | :--- |
| `python3 scripts/run-capability.py <skill> < invocation.json` | Invoke one of the nine public capabilities using a typed JSON request, in `execute` or `describe-policy` mode. |
| `python3 scripts/concorde.py <command>` | `validate`, `build`, `docsite`, `ua-graph`, `protocol-manifest`. |
| [LangGraph Studio](scripts/development/STUDIO.md) | Start, observe and debug the same nine public workflows through the shared CapabilityHost. |
| `python3 scripts/install-concorde.py` | Preview or apply installation into a project. |
| `python3 scripts/reflections_queue.py` | Query and maintain the reflection queue. |
| `python3 scripts/run-ua-graph-viewer.py` | Launch the code graph viewer. |
| `npm --prefix docsite run <script>` | `start`, `build`, `validate`, `typecheck`, `test`, `check`. |
| `python3 scripts/development/run-tests.py` | Run the project's test suite. |
| `python3 scripts/worktree-guard.py` | Explain or check the source-checkout worktree policy. |

The CLI `validate` command performs direct validation. The `concorde-validate` capability also
manages candidate readiness evidence as part of the lifecycle. Studio uses the same host and
capabilities as the CLI and Skills.

## Explore and contribute

- **[Spec explorer](https://ftod.github.io/concorde/)** — published Protocol, Module contracts and relationship graphs.
- **[Workflow guide](docs/workflow-guide.md)** — JSON requests, review, delivery, check sandboxing and Protocol upgrades.
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
Concorde itself is developed by direct maintenance in this checkout; its own flows run on this
repository only when you explicitly ask for one, so the `concorde-*` Skills built here are
user-invoked only. See the [source-checkout policy](AGENTS.md).

---

[MIT licensed](LICENSE). Built with Concorde's own [Specs](specs/concorde/module.md).
