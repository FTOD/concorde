<p align="center">
  <img src="docs/assets/concorde-hero.svg" alt="Concorde — Specify the architecture. Understand the system. Guide your agents." width="100%" />
</p>

<p align="center">
  <a href="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml"><img src="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml/badge.svg" alt="Source validation" /></a>
  <a href="protocol/README.md"><img src="https://img.shields.io/badge/Spec_Protocol-11.1.0-6264e8" alt="Spec Protocol 11.1.0" /></a>
  <a href="#get-started"><img src="https://img.shields.io/badge/client-Pi-273449" alt="Client: Pi" /></a>
  <a href="#control-flow-pi-workflows-and-langgraph-graphs"><img src="https://img.shields.io/badge/control_flow-pi_workflows_%C2%B7_LangGraph-273449" alt="Control flow: pi workflows and LangGraph Graphs" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-273449" alt="MIT license" /></a>
</p>

<p align="center">
  <a href="#why-concorde"><strong>Why Concorde</strong></a> ·
  <a href="#get-started"><strong>Get started</strong></a> ·
  <a href="#the-docsite"><strong>Docsite</strong></a> ·
  <a href="https://ftod.github.io/concorde/"><strong>Explore the Specs</strong></a> ·
  <a href="docs/workflow-guide.md"><strong>Workflow guide</strong></a>
</p>

# Concorde

**Architecture-aware Specs, and coding agents that work strictly within them.**

Concorde keeps a project's Specs at the center of AI-assisted development. A Spec explains what
each Module is responsible for, how it is designed, which precise promises it makes and which files
realize it. Every Agent call receives a context derived from the Specs of the Module it is bound to,
and its answer counts only after Concorde's deterministic Host has checked it. A change is made in
its own candidate worktree, checked there and delivered only when you ask.

You drive Concorde from the **Pi coding agent** through its `concorde` session tool; Pi is the only
supported client, with any of Pi's model providers. The user session (your own Pi session) reads,
answers and edits Specs directly, and chooses which capabilities to call and in what order.
Concorde never picks the next step, never repairs a Spec on its own and never merges into your
primary branch without explicit authorization.

## Why Concorde

### Specs that explain the architecture, not just the API

A **Module** is one cohesive responsibility, such as planning a change or publishing documentation.
It need not be a package or directory: its realization may span several, or be supplied entirely by
its child Modules. A project's Specs form one graph: Modules and the documents they own, the
concepts, requirements, scenarios and contracts those documents define, and typed relations between
them.

- A Module's **entry** (`module.md`) explains it for a reader who does not know the code: Purpose,
  Terminology, Usage, Design and Relationships. Explanatory topics can join it.
- **Implementation documents** hold the precise obligations: `SHALL` requirements,
  `GIVEN`/`WHEN`/`THEN` scenarios and versioned interface contracts.

Every Markdown document has a paired `.md.json` metadata file. The entry's metadata declares the
Module's own relations — which documents it owns, which Modules it `contains` and `uses` (naming
exactly the promises it `relies_on`), what else it `includes`, and which contracts it
`participates` in — and the registry `.concorde/specs.json` mirrors them for a global view. Each term
is defined once, in its owner's Terminology table, and imported elsewhere by link. Realizations bind
every file of the repository to the Modules it realizes, and tests declare the scenarios they verify.
Concorde checks all of this, and computes from it what each task may read and write.

### Each Agent call sees one Module's context, and only what its phase needs

The context of one Agent call has four kinds, all derived from declarations and frozen for the call:

| Context            | What it contains                                                                                                   | Who receives it                                                       |
| :----------------- | :----------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------- |
| **Spec**           | The bound Module's documents and those its `uses`, `contains` and `includes` select, one level, plus the external references (vendored, version-pinned documentation such as LangGraph's) it declares | Every phase                                                           |
| **Implementation** | The names of the files bound by the Module's realizations, and their contents when the phase is granted them      | Names for every phase; contents only for code writing and code review |
| **Capability**     | The definitions of the tools the Agent may use and the contracts of what they reach                               | Every phase                                                           |
| **Task**           | The request, its constraints, the stage artifacts admitted for this phase and workspace metadata                  | Every phase                                                           |

Planners and task authors reason from the Spec alone. If the Spec does not say something the task
needs, the Agent reports a Spec gap as an Issue instead of guessing from code, and the dependent
step stops until the Spec is repaired. Good results within these limits are evidence that the Spec
is sufficient and the Modules are well decoupled; they are not a proof of correctness.

### What is enforced, and what is policy

Agents run fresh and terminal: no delegation tool, no inherited project or global context. Their
file, network and credential limits are **instructions**, not operating-system confinement; the
[Harness](specs/concorde/harness/module.md) states exactly what is enforced. What is enforced:
the launch shape of every call, the Host's acceptance of its result against unchanged inputs, and
the read-only boundary in which configured checks and tester commands run. A model's answer is a
proposal until the Host accepts it.

### Control flow: pi workflows and LangGraph Graphs

An **Operation** is one cataloged executable entry with exactly one control-flow kind: a **Host
service** (deterministic code), a **single Agent call**, a **pi workflow** (a script of Agent calls
and Host steps that pi-subagents runs) or a **LangGraph Graph** built with the Graph API only.
The catalog holds eleven Operations, all public: they are the capabilities the `concorde` tool
offers. Simple fixed sequences are pi workflows; a Graph is used when state and branching must be
inspectable. Each workflow is explained by a step table and each Graph by a Graph Spec in its
owner's Spec, and a deterministic check compares every compiled Graph with its Graph Spec.

For a model-backed capability, `concorde` returns a prepared native call; the user session passes
it unchanged to the pi-subagents `subagent` tool and, for a workflow, polls it with the `concorde`
tool's `result` action. The Terminal Agent Operation, `OperationNode(agent).graph()`, lets a program embed one Agent
call as a typed LangGraph `StateGraph` node; its trusted Agent service arrives in LangGraph's
Runtime context, never in State.

### Agents and Task subagents

The [Agents Module](specs/concorde/agents/module.md) defines the seven **Agents**, the model steps
inside capabilities: `context-assessor`, `planner`, `task-author`, `programmer`, `spec-reviewer`,
`code-reviewer` and `issue-solver`. Each has one definition fixing its phase, what it reads and
writes, its stage inputs, its result fields, its tools and its time limit. Business rules stay with
their owners: Planning owns plans and tasks, Implementation owns task completion, Review owns
findings and Issue solving owns dispositions.

**Task subagents** are not Agents: they own a whole task and are defined by the
[Pi session](specs/concorde/session/module.md). The `tester` tests a stopped candidate read-only and
ships to every project; the `maintenance-worker` is source-only and changes Concorde's own sources.
The user session is the external caller that coordinates them, not another Agent.

### Changes run in candidate worktrees and are delivered on request

A mutating request from your primary worktree runs in a candidate worktree that the Host creates
from the committed `HEAD`. Your session stays where it is and receives the candidate's result,
including its path, branch and `change_id`, with which you continue the change. `concorde-validate`
decides readiness from current evidence; `concorde-deliver` publishes the ready candidate on the
branch `concorde/delivered/<change_id>`; merging into your primary branch is a further request that
states your explicit authorization.

### Problems become tracked Issues

Agents record bugs, missing or conflicting promises and limitations as Git-versioned
[Issues](specs/concorde/issues/module.md) under `.concorde/issues/`. Reporting does not stop an
Agent or authorize a repair. `concorde-issues` lists, shows, reports, reopens or solves one selected
Issue; solving verifies with fresh reviews and hands any needed development or Spec repair back to
the caller, and never delivers.

## Choose work explicitly

The user session reads the relevant complete Specs, selects the owning Module and edits its reading,
paired metadata and registry directly. These edits keep Spec consistency and ownership rules; they
never count as review or completion evidence.

A typical change is a sequence the user session chooses: agree the Spec (optionally
`concorde-spec-review`), then `concorde-context-solve`, `concorde-plan`, `concorde-tasks`,
`concorde-implement`, optionally `concorde-code-review`, `concorde-validate` and `concorde-deliver`.
Dependencies are enforced — tasks need a current accepted plan, implementation needs accepted tasks,
and a review the change requires must be current — but no automatic loop runs and nothing is
repaired on its own.

| Capability         | Agent                              | Reads                                         | May change                               |
| :----------------- | :--------------------------------- | :-------------------------------------------- | :--------------------------------------- |
| Context assessment | `context-assessor`                 | Complete bound Spec                           | Nothing; reports sufficiency or gaps     |
| Spec review        | `spec-reviewer`                    | Complete Spec context, fresh                  | Nothing; returns findings                |
| Plan               | `context-assessor`, then `planner` | Spec, references and implementation file names | Nothing; returns a current plan         |
| Tasks              | `task-author`                      | Spec, references and the accepted plan        | Nothing; returns acceptance tasks        |
| Implement          | `programmer`                       | Spec, tasks, references and listed files      | Only the Module's listed implementation  |
| Code review        | `code-reviewer`                    | Spec and the implementation under review      | Nothing; returns findings                |
| Validate           | none                               | Structural and configured checks              | Records current evidence                 |

## Get started

**Requirements.** A Git project on **Linux with [bubblewrap](https://github.com/containers/bubblewrap)**,
working user, mount and PID namespaces and pidfd support: configured checks and tester commands run
in that boundary. **Python 3.11+**, **Node.js 18+** and npm for the managed runtime and the Pi
extension dependencies. The [Pi coding agent](https://www.npmjs.com/package/@earendil-works/pi-coding-agent)
on `PATH` (`npm install -g @earendil-works/pi-coding-agent`; Concorde is developed against 0.85.1),
logged in with `pi` then `/login`: Agents use that login and Pi's own model providers. The optional
docsite needs Node.js **20+**.

**1. Clone and build Concorde.**

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
```

**2. Preview the installation into your project, then apply it.**

```bash
python3 scripts/install-concorde.py --target /absolute/path/to/project --preview
python3 scripts/install-concorde.py --target /absolute/path/to/project --apply
```

The installer provisions a locked managed runtime at `.concorde/.venv`, deploys the framework to
`.concorde/framework/`, places the Protocol at `.concorde/protocol/` and adds a guidance block to
`AGENTS.md`. It installs a receipt-owned session entry, `.pi/extensions/concorde-session.ts`, whose
`concorde` tool describes and runs the eleven capabilities, and the generic `tester`. It preserves
your content outside the entries it owns, and the launcher re-runs itself inside the managed
runtime. Upgrades update or remove only unchanged receipt-owned outputs; edited, symlinked or
unknown content is reported as a conflict.

**3. Commit project inputs, then initialize the project.** Candidate worktrees start from the
committed `HEAD`, so commit your project files, root guidance and the complete Protocol bundle
first. The framework, `.concorde/.venv`, the installation receipt and the `.pi` runtime assets may
stay ignored: each candidate gets its own verified local installation, never the primary's runtime.
Then, in a Pi session inside your project, trust the local project extension when Pi asks:

```text
Use concorde-init to initialize this project. Propose the setup for my review.
```

Review the proposal and ask to apply it. Apply takes exactly the proposal that was returned, named
by its digest, and refuses if the project changed since. It records the Pi model and thinking level
your Agents use (change them later with `concorde-configure`) and creates an honest stub of the
root Module Spec. Applied from the primary worktree, it runs in a candidate unless you ask to
initialize the primary directly; complete the stub there, then validate, deliver and merge.

Existing installations are verified and reused. Missing, stale or conflicting local assets block
execution and require explicit recovery with the installer. For a normal Git-created worktree:

```bash
python3 /explicit/project/.concorde/framework/scripts/install-concorde.py \
  --target /absolute/path/to/worktree --preserve-project --preview
# Inspect the proposal, then repeat with --apply.
```

See [installation and recovery](specs/concorde/distribution/installation.md#local-installations-in-worktrees).

**4. Read, edit and select capabilities.**

```text
Read the complete registered Specs and explain how requests reach storage.
Edit the selected Module's contract and paired metadata to describe this approved change.
Use concorde-plan for target module.storage and task “Implement the approved retry policy”.
```

Every capability that acts on one Module receives an explicit target; questions and Spec edits are
ordinary user session work.

## Choose an entry point

| You want to…                                     | Use                                      |
| :----------------------------------------------- | :--------------------------------------- |
| Assess the bound Spec for a task                 | `concorde-context-solve`                 |
| Plan a change of one Module                      | `concorde-plan`                          |
| Turn a current plan into acceptance tasks        | `concorde-tasks`                         |
| Implement accepted tasks within listed files     | `concorde-implement`                     |
| Review a Spec, including terminology consistency | `concorde-spec-review`                   |
| Review code against its Spec                     | `concorde-code-review`                   |
| Inspect, report, reopen or solve an Issue        | `concorde-issues`                        |
| Initialize or configure Agents                   | `concorde-init` · `concorde-configure`   |
| Validate or deliver a candidate                  | `concorde-validate` · `concorde-deliver` |

`describe-policy` previews what a request would do without starting an Agent; initialization and
configuration use their own propose and apply steps instead.

## Explore Concorde

### The docsite

The **[published docsite](https://ftod.github.io/concorde/)** renders Concorde's own Specs in three
tabs: **Module documents** (the explanatory entries, navigated by Module parentage),
**Implementation documents** (requirements, scenarios, contracts and Graph Specs of the same
Modules) and **Spec Protocol**. To preview it locally with Node.js 20+:

```bash
python3 scripts/concorde.py build
npm --prefix docsite ci
npm --prefix docsite run start -- --host 127.0.0.1 --no-open
```

Open [localhost:3000/concorde/](http://localhost:3000/concorde/). `npm --prefix docsite run build`
produces a verified static site in `docsite/build/`.

![Concorde's docsite showing the root Module Spec's Purpose and Terminology, the Module tree and the documentation tabs](docs/assets/concorde-docsite.png)

For your own project, [scaffold a docsite](docsite/README.md#scaffold-a-docsite) with
`python3 .concorde/framework/scripts/concorde.py docsite --propose` and then `--apply`; add
`--github-pages` for a deployment workflow.

## The Spec Protocol in brief

Concorde's independent **[Spec Protocol 11.1.0](protocol/README.md)** has two purposes: a human
understands a project's backbone from its Specs without reading code, and a harness derives from
the Specs exactly what each AI task may read and write. A Module's entry `module.md` answers five
questions in order:

| Section           | The question it answers                                                          |
| :---------------- | :------------------------------------------------------------------------------- |
| **Purpose**       | What responsibility does this Module own, for whom and within which scope?       |
| **Terminology**   | Which words does the reader need, each defined once by its owner?                |
| **Usage**         | When and how is it used, with which inputs, results, errors and limits?          |
| **Design**        | How do its decomposition, state and constraints fulfil its guarantees, and why?  |
| **Relationships** | How does it collaborate with other Modules, shown in a diagram checked against the declared relations? |

Every node and relation is declared exactly once. A Module's context is computed from its own
declarations, one level deep: a Markdown link never adds a file to what an agent may read. Its write
sets are its own documents and the files its realizations bind. Structural validation and declared
test coverage are evidence, not proof that a Spec is sufficient.

Start from the [Protocol](protocol/README.md), the [Module template](protocol/templates/module.md)
or [Concorde's own root Spec](specs/concorde/module.md), which applies it to this repository.

## Under the hood

Commands are relative to this checkout; installed projects use the same scripts under
`.concorde/framework/`.

| Entry point                                                      | Use                                                                                          |
| :--------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| `python3 scripts/run-operation.py <operation> < invocation.json` | The launcher: runs one capability request; Agent calls and workflows need the Pi session.    |
| `python3 scripts/concorde.py build` · `build --check`            | Render the Agents' instructions, the session entry and catalog, the Protocol assets and schemas; check they are current. |
| `python3 scripts/concorde.py validate` · `check-package`         | Check the Specs, registry, coverage and configured inputs; check the package inventory.     |
| `python3 scripts/concorde.py protocol-manifest`                  | Inspect, or explicitly accept and bind, a changed Protocol bundle.                           |
| `python3 scripts/concorde.py docsite` · `registry`               | Scaffold a project docsite; rewrite the registry mirror.                                     |
| `python3 scripts/install-concorde.py`                            | Preview or apply installation into a project.                                                |
| `python3 scripts/issues.py`                                      | Inspect branch-local Issues from the command line.                                           |
| `npm --prefix docsite run <script>`                              | `start`, `build`, `validate`, `typecheck`, `test`, `check`.                                  |

The CLI `validate` command checks the project directly; the `concorde-validate` capability also
records readiness evidence for a candidate.

## Develop Concorde

```bash
uv sync --locked --group dev
python3 scripts/concorde.py build
python3 scripts/development/init-references.py   # vendored references under reference/
npm ci --prefix pi                                # the Pi extension dependencies
python3 scripts/concorde.py build --check
python3 scripts/concorde.py validate
.venv/bin/python -m pytest                        # parallel by default; -n 0 runs in-process
```

Concorde maintains itself with Task subagents: the source user session registers a candidate,
launches one fresh `maintenance-worker` there as its only writer, and after it stops may hand the
candidate to a fresh `tester` bound to the candidate's exact build through
`select-session --mode test`. The source checkout's session entry stays private
(`generated/session/pi/concorde-session.ts`) and is never installed into ambient discovery.

Never edit build output under `generated/`; change the authored sources (`prompts/`, `agents/`,
`operations/`, `pi/`, `src/`, `protocol/`) and rebuild. See the [source-checkout rules](AGENTS.md)
and the [development details](docs/workflow-guide.md#development).

---

[MIT licensed](LICENSE). Built with Concorde's own [Specs](specs/concorde/module.md).
