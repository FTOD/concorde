<p align="center">
  <img src="docs/assets/concorde-hero.svg" alt="Concorde — Specify the architecture. Understand the system. Guide your agents." width="100%" />
</p>

<p align="center">
  <a href="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml"><img src="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml/badge.svg" alt="Source validation" /></a>
  <a href="protocol/README.md"><img src="https://img.shields.io/badge/Spec_Protocol-10.0.0-6264e8" alt="Spec Protocol 10.0.0" /></a>
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

The framework brings together a Spec docsite, LangGraph Studio support for observing agent
execution, explicit agent context and permissions, and a small set of built-in agents for
specification and development. Branch-local Issues retain bugs, contract gaps
and limitations reported during work, independently of whether a task continues or stops.

## Why Concorde

### 1. Write and maintain architecture-aware Specs

A Module Spec describes purpose, requirements, scenarios and architecture together. Its entities,
relationships, dependencies and implementation file bindings make software structure explicit.
Concorde supports authoring, reviewing and updating these Specs, checking their consistency, and
tracking which Module contracts are affected as shared code changes.

### 2. Understand the project and observe agent execution

The **[docsite](docsite/README.md)** publishes reading content with Module navigation and scoped inline relationship diagrams, while keeping
metadata in an auxiliary provenance view.

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

### 4. Compose State-based Operations for everyday development

Concorde uses one executable concept: **Operation**, a LangGraph node with declared input State,
output updates, effects, use conditions and execution policy. An Operation can run deterministic
code, invoke a model or compose a graph; dev-loop and specify-loop are composed Operations.
Completeness means callers do not reconstruct context policy, permission boundaries, model execution
or result checks. Trusted Host/Harness services still narrow and enforce its permission ceiling;
State cannot carry or expand authority. Public/internal only controls entry exposure.
All definitions live in `operations/`; `USES` is the single composition relation. Model-backed
Operations keep instructions, tools, permissions and timeout in an optional execution profile,
not a separate Agent registry. Hosts and launchers stay in trusted LangGraph runtime context rather
than writable State. Public Skills and existing wire envelopes remain the external entry points.

Twelve model-backed Operations execute through Pi workers: **answerer**, **router** and
**topology-designer** for questions, routing and topology design; **spec-author**,
**topology-author**, **spec-reviewer**, **context-assessor**, **planner** and **task-author** for
authoring, reviewing, planning and task definition; and **programmer**, **code-reviewer** and
**issue-solver** for implementation, code review and bounded Issue resolution. Each worker is one Pi coding
agent process (`pi --mode rpc`) run for exactly one invocation. Public Skills compose them into
workflows with explicit context and permissions for each invocation.

### 5. Turn feedback into tracked improvements

The **[Issue system](specs/concorde/issues/module.md)** keeps classified problems in Git-versioned
`.concorde/issues/` records. Workers use `report_issue` during their own graphs; a successful report
is saved immediately and does not stop the worker or authorize a repair. Review judgments and
stage blockers reference the original observations instead of copying their prose.

Use `concorde-issues` to list, show, report, reopen or solve an explicitly selected Issue. Solve can
use ordinary development, a fresh Spec repair or Issue-specific review without a mandatory triage
pass. It makes evidence-grounded dispositions autonomously and asks for human input only when a
necessary choice cannot be settled. A successful solve includes the disposition in final candidate
verification and stops at ready, never at automatic delivery or primary merge. Closed records stay
available, and a candidate-local solution says nothing about another branch.

Legacy Reflections are not automatically converted or approved. This checkout's records are in
`.concorde/archive/reflections/`. Consumer projects can explicitly preserve their old queue with
`python3 .concorde/framework/scripts/issues.py archive-reflections`; installation preserves old user
data. Removed investigator model overrides must be updated explicitly to the issue-solver role.

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

Apply the reviewed proposal, then write the root Module's Purpose, Terminology, Usage, Design and Relationships,
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

### Explore Module architecture

Open a Module's reading entry in **Module Specs**. Purpose and Usage introduce the responsibility,
Design explains its realization, and Relationships shows scoped collaboration diagrams. The sidebar
follows Module parentage. There is no separate docsite Graph tab.

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

This inspects admitted permissions without starting a worker. Change `mode` to `execute` to run
the question through a Pi worker, using the project's configured model and thinking level and the
developer's own Pi login. Inspect **result**,
**policies** and **events** in the state; execution emits operation, stage and agent-process
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

Concorde's independent **Spec Protocol 10.0.0** defines one specification category: a **Module Spec**.
A Module describes a cohesive software responsibility; its implementation may span packages,
services or shared files. Each Spec document has one owning Module. A Module's explicit
`references` includes other Module-owned documents or one registered document, expanded once;
Markdown links remain navigation. Shared interfaces have one definition and local participant bindings.

The repository's Specs, runtime admission, context serialization and publication support
Protocol 10/Profile 15/registry schema 5, with document metadata schema 2. Resolved contexts retain unique owners, one-level reference
provenance and exact byte digests without granting provider implementation access; see
[Spec context queries](specs/concorde/spec/contracts.md#registry-stable-id-spec-context-queries).
Runtime and publication tests verify these boundaries separately from the rule build.

Concorde's own docsite includes an **Agent Graphs** tab at `/concorde/agent-graphs`, showing the actual
executable LangGraph Graphs, expanded Studio entries and routing handoffs with links to the Specs. This page
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
| **Design** | How do responsibilities, state, graph and constraints fulfill its guarantees? |
| **Relationships** | Which entities collaborate, under which conditions, and how does dependency differ from composition? |

**Module Specs** contain explanatory entries and topics with `document.role: module`.
**Implementation Specs** contain the same Module's formal requirements, scenarios and canonical
interface contracts with `document.role: implementation`. Formal definitions are forbidden in entries
and topic pages; topics such as Registry do not become separate owners. Both roles remain normative,
human-readable parts of one complete Module specification, and both enter agent context unchanged.
The docsite presents them in parallel tabs under the same Module hierarchy. Internal constraints
are not weakened by their location. Diagrams
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
| Report, inspect or solve classified Issues without mandatory triage | `concorde-issues` |
| Initialize or configure a project | `concorde-init` · `concorde-configure` |
| Validate a candidate or deliver a verified change | `concorde-validate` · `concorde-deliver` |

These nine public Skills expose selected Operations. Other Operations are composed by the host. See the [operation registry](specs/concorde/development/operations.md)
for the full interface.

## Agents, operations and executable entry points

Concorde currently defines **26 Operations and 9 public Skills**. Fourteen Operations use host
adapters and twelve have model execution profiles. A model-backed Operation runs a fresh Pi worker
for its bounded invocation; workers are executions, not a second executable entity inventory. Public Skills provide instructions for invoking
those operations from the developer's agent client.

### Model-backed Operations and workers

| Operation / worker profile | Phase / action | Responsibility and authority |
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
| `issue-solver` | issue-solve | Select bounded work or an evidence-grounded disposition from a selected Issue and its Module Spec. |

Each model-backed Operation keeps its instructions in `operations/<name>/spec.md` and its
execution profile in `operations/<name>/__init__.py`: task contract, workspace, Pi tools, children
and timeout. Definitions live in [operations/](operations/__init__.py); the
[Operations and workers guide](specs/concorde/harness/agents-and-harnesses.md) explains the execution contract. Each worker fulfils exactly one task contract, and each
invocation receives fresh, explicitly bounded context and permissions.

### Host-adapted Operations

| Operation | Behavior | Public Skill |
| :--- | :--- | :--- |
| `main` | Answer questions, route requests, and design and apply accepted topology changes. | `concorde-main` |
| `specify-loop` | Route a change, author or revise its Spec, and independently review it before implementation. | `concorde-specify-loop` |
| `dev-loop` | Call specify-loop, then plan, implement, validate and review code to a ready candidate. | `concorde-dev-loop` |
| `review` | Run a standalone Spec or code review, including source diagnosis. | `concorde-review` |
| `issues` | Inspect, report, reopen or solve an explicit Issue to a verified candidate. | `concorde-issues` |
| `init` | Propose and apply project initialization with a pinned Protocol. | `concorde-init` |
| `configure` | Apply the project's Pi worker model/thinking selection and, on request, accept an updated Protocol binding. | `concorde-configure` |
| `validate` | Run deterministic Spec and configured code checks and record readiness. | `concorde-validate` |
| `deliver` | Stage a verified candidate on its own branch and clean up; merge into the primary branch on a separate explicit request. | `concorde-deliver` |
| `specify` | Author Spec replacements for the bound Module. | — |
| `context-solve` | Validate Module participant routing and assess context sufficiency. | — |
| `plan` | Assess sufficiency and produce a revision-bound plan. | — |
| `tasks` | Derive acceptance tasks from the accepted plan. | — |
| `implement` | Implement component tasks or coordinate participating components. | — |

Of these fourteen host-adapted Operations, four make no model calls and ten may call a model.
Nine have public Skills; five are internal host adapters. Together with the twelve model-backed
Operations above, there are seventeen internal Operations, all complete building blocks without
a standalone public launcher and reachable only through admitted composition. Current workers have no admitted
Operation references of their own; the host composes the workflows.

Each Operation declares public exposure, context selection (`discover`, `bound` or `none`),
determinism, optional model execution configuration and composed Operations independently. A Graph organizes calls,
branches and loops; “stage” describes a position in execution, not a type of Operation.

The source inventory is [operations/](operations/__init__.py); the
[operation registry](specs/concorde/development/operations.md) describes the contracts.

### Harness

A Harness is context, control flow, models and per-worker permissions and environment: the shared
part is the host environment allowlist, the Pi worker runtime and the LangGraph Graphs that
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
| `python3 scripts/run-operation.py <skill> < invocation.json` | Invoke one of the nine public operations using a typed JSON request, in `execute` or `describe-policy` mode. |
| `python3 scripts/concorde.py <command>` | `validate`, `build`, `docsite`, `protocol-manifest`. |
| [LangGraph Studio](scripts/development/STUDIO.md) | Start, observe and debug the same nine public workflows through the shared OperationHost. |
| `python3 scripts/install-concorde.py` | Preview or apply installation into a project. |
| `python3 scripts/issues.py` | Inspect branch-local Issues or explicitly archive legacy Reflection data. |
| `npm --prefix docsite run <script>` | `start`, `build`, `validate`, `typecheck`, `test`, `check`. |
| `python3 scripts/development/run-tests.py` | Run the project's test suite. |
| `python3 scripts/worktree-guard.py` | Explain or check the source-checkout worktree policy. |

The CLI `validate` command performs direct validation. The `concorde-validate` operation also
manages candidate readiness evidence as part of the lifecycle. Studio uses the same host and
operations as the CLI and Skills.

## Explore and contribute

- **[Spec explorer](https://ftod.github.io/concorde/)** — published Protocol, Module contracts and relationship graphs.
- **[Workflow guide](docs/workflow-guide.md)** — JSON requests, review, delivery, check sandboxing and Protocol upgrades.
- **[LangGraph Studio](scripts/development/STUDIO.md)** — execution graphs, live events and debugging.
- **[Docsite](docsite/README.md)** — publish Specs as a navigable site with Module navigation and relationship diagrams.
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
Concorde itself is developed by direct maintenance in this checkout; its own graphs run on this
repository only when you explicitly ask for one, so the `concorde-*` Skills built here are
user-invoked only. See the [source-checkout policy](AGENTS.md).

---

[MIT licensed](LICENSE). Built with Concorde's own [Specs](specs/concorde/module.md).
