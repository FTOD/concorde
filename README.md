<p align="center">
  <img src="docs/assets/concorde-hero.svg" alt="Concorde — Specify the architecture. Understand the system. Guide your agents." width="100%" />
</p>

<p align="center">
  <a href="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml"><img src="https://github.com/FTOD/concorde/actions/workflows/validate-source-checkout.yml/badge.svg" alt="Source validation" /></a>
  <a href="protocol/README.md"><img src="https://img.shields.io/badge/Spec_Protocol-10.0.0-6264e8" alt="Spec Protocol 10.0.0" /></a>
  <a href="#get-started"><img src="https://img.shields.io/badge/client-Pi-273449" alt="Client: Pi" /></a>
  <a href="#native-workflows-and-optional-stategraph-operations"><img src="https://img.shields.io/badge/graphs-LangGraph-273449" alt="Native workflows; optional StateGraph Operations" /></a>
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
realize it. Each native Pi Agent receives one selected Module's complete admitted context and explicit intended
file/tool policy. Native broad tools are not OS-confined by Concorde. A change is made in its own candidate worktree,
checked and independently reviewed there, and delivered only when you ask.

You drive Concorde from the **Pi coding agent** through its `concorde` session tool. Pi is the
only supported client; standalone Skills and Codex/Claude client integrations are retired.
Pi model providers, including OpenAI and Anthropic, remain supported. Model cognition runs through native pi-subagents Agents and authored workflows; deterministic actions
are Host services. LangGraph is an optional execution boundary, not a scheduler under every call. The outer agent reads,
answers and edits Specs directly, then chooses which Operations to call and in what order.

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

| Context            | What it contains                                                                                  | Who receives it                                                       |
| :----------------- | :------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------- |
| **Spec**           | The Module's own documents plus the ones it explicitly references, one level deep                 | Every phase                                                           |
| **Implementation** | The files bound by the Module's entities                                                          | Names for every phase; contents only for code writing and code review |
| **Resource**       | Vendored, version-pinned documentation and source of the libraries it declares, such as LangGraph | Planning, task authoring, code writing and code review, read-only     |
| **Task**           | The request, constraints and the stage artifacts admitted for this phase                          | Every phase                                                           |

Planners and task authors reason from the Spec alone. If the Spec does not say something the task
needs, the worker reports a Spec gap as an Issue instead of guessing from code, and the dependent step
stops. The design premise is that good results within these limits are evidence that the Spec is
sufficient and the Modules are well decoupled. That is not a proof of correctness; tests and review
still matter.

### Explicit policy and actual enforcement

Native Agents are fresh and terminal, without delegation tools, inherited project/global context or
Skills. Their file/network/credential exclusions are explicit **prompt-level policy**, not OS
confinement or proof of exclusive reads. Programmer edits use the actual assigned candidate paths.
Host-owned configured checks and tester commands retain their enforced read-only subprocess/sandbox
boundaries. Trusted admission, currentness, evidence, journal and integration authority remain Host
responsibilities; a model proposal or successful stage-only gate is never domain acceptance.

### Native workflows and optional StateGraph Operations

An **Agent** is a callable native Pi role. A **Workflow** is an authored pi-subagents composition.
An **Operation** is an explicitly selected LangGraph StateGraph flow. Finite non-model actions are
**Host tools/services**. These executable kinds do not change Module ownership or context references.
The compatibility `concorde-*` names and `operation_id` wire fields do not make every entry a Graph.

Plan, review and bounded Issue solving use authored native workflows. Context assessment, tasks and
implementation use direct native Agents. Main calls `concorde` to prepare a bound invocation, passes
its exact returned `call` to native `subagent`, and polls the same workflow entry with action `result`
when asynchronous. Final acceptance separately reconciles actual native artifacts and current inputs.

`OperationNode(agent).graph()` is the optional typed StateGraph boundary. A trusted embedding supplies
an authorized native launch/admission service through Runtime, synchronously or asynchronously. Its
State cannot choose that authority. There is no default model runner or old RPC fallback. Studio
inspects this exact boundary, not fake graph mirrors of native workflows.

### Changes run in candidate worktrees and are delivered on request

A change requested from your primary worktree runs in a candidate worktree that the host creates from
the committed `HEAD`. Your session stays where it is and receives the candidate's result, including
its path, branch and `change_id`, with which you continue the change. Current validation and selected review evidence can establish a
**ready** candidate; no loop history is required. Delivery is a separate request that publishes the branch
`concorde/delivered/<change_id>`; merging into your primary branch needs another explicit request.

### Problems become tracked Issues

Workers record bugs, missing or conflicting promises and limitations as Git-versioned
[Issues](specs/concorde/issues/module.md) under `.concorde/issues/`. Reporting does not stop a worker
or authorize a repair. `concorde-issues` lists, shows, reports, reopens or solves an explicitly
selected Issue. Verification uses fresh independently admitted native reviews and finite checks; repair decisions return
selected intent to the caller without automatic authoring or development, and never deliver.

## Choose work explicitly

The outer agent reads the relevant complete Specs, selects the owner and directly edits reading,
paired metadata and registry/topology within the task grant. These edits retain deterministic Spec
consistency and ownership rules; they do not create review or completion evidence.

A caller-selected sequence might be contract edits, Spec review, assessment/planning, tasks,
implementation, code review and validation. This is not an executable development workflow: the
caller chooses each Operation and explicit Module target. Dependencies remain enforced — tasks
need a current accepted plan, implementation needs accepted tasks, and a selected review must
actually be current and successful. Component work is selected separately, not developed by a parent.

| Operation          | Worker                             | Reads                                         | May change                               |
| :----------------- | :--------------------------------- | :-------------------------------------------- | :--------------------------------------- |
| Context assessment | `context-assessor`                 | Complete selected Spec                        | Nothing; reports sufficiency or blockers |
| Spec review        | `spec-reviewer`                    | Complete Spec context, fresh                  | Nothing; returns findings                |
| Plan               | `context-assessor`, then `planner` | Spec, resources and implementation file names | Nothing; returns a current plan          |
| Tasks              | `task-author`                      | Spec, resources and accepted plan             | Nothing; returns acceptance tasks        |
| Implement          | `programmer`                       | Spec, tasks, resources and listed files       | Only the Module's listed implementation  |
| Code review        | `code-reviewer`                    | Spec and authorized code                      | Nothing; returns independent findings    |
| Validate           | none                               | Structural and configured checks              | Records current evidence                 |

Missing promises, stale plans, incomplete tasks and required failed/stale reviews block dependent
work. For a repair, the caller can explicitly select current blocking code-review evidence for
new tasks, implement them and obtain fresh evidence. No automatic author or repair loop runs.
Delivery is always a separate request; direct/manual candidates need no invented plan, but cannot
bypass unfinished planned work or selected required evidence.

## Get started

**Requirements.** A Git project on **Linux with [bubblewrap](https://github.com/containers/bubblewrap)**,
working user, mount and PID namespaces and pidfd support: configured checks and tester commands use that enforced boundary. Native Agent file policies
are not sandbox enforcement. **Python 3.11+**, **Node.js 18+** and npm, used for the managed runtime and Pi
extension dependencies, not a Skills installer. The [Pi coding agent](https://www.npmjs.com/package/@earendil-works/pi-coding-agent) on
`PATH` (`npm install -g @earendil-works/pi-coding-agent`; Concorde is developed against 0.85.1),
logged in with `pi` then `/login`: workers use that login and Pi's own model providers. The optional
docsite needs Node.js **20+**.

**1. Clone and build Concorde.**

```bash
git clone https://github.com/FTOD/concorde.git
cd concorde
python3 scripts/concorde.py build
```

**2. Preview the Pi-only installation into your project, then apply it.** There is no client
selector; retired `--integration` flags are rejected, including `--integration pi`.

```bash
python3 scripts/install-concorde.py --target /absolute/path/to/project --preview
python3 scripts/install-concorde.py --target /absolute/path/to/project --apply
```

The installer provisions a locked managed runtime at `.concorde/.venv`, deploys the framework to
`.concorde/framework/`, places the Protocol at `.concorde/protocol/` and adds a guidance block to
`AGENTS.md`. It installs a receipt-owned session extension under `.pi/extensions/` whose
`concorde` tool describes and runs the eleven public Operations. It preserves your content outside
the entries it owns, and the launcher re-runs itself inside the managed runtime. No standalone
Skills are installed and no Skills CLI runs.

Upgrades retire only unchanged receipt-owned outputs and exact owned root blocks. Edited,
symlinked or unknown content conflicts safely. Old external CLI-owned `.agents/skills`,
`.claude/skills` entries and `skills-lock.json` are left untouched, with a manual retirement notice;
remove only your own retired Concorde entries, never those directories or locks wholesale.

**3. Commit project inputs, then initialize the project.** Candidate worktrees start from committed
`HEAD`, so commit your project files, root guidance and complete Protocol bundle first. Framework,
`.concorde/.venv`, installation receipt and `.pi` runtime assets may remain ignored; they do not
need to be committed. Before executing a new consumer candidate, the host installs and verifies a
complete local copy from the exact invoking package. Each candidate has its own Pi session entry,
Framework and independently provisioned dependencies; it never executes through primary's runtime.
Then, in a Pi session inside your project, trust the local project extension when Pi asks:

```text
Use concorde-init to initialize this project. Propose the setup for my review.
```

Review the proposal and ask to apply it. Applying runs in a candidate worktree and returns its path,
branch and `change_id`. It records the Pi model and thinking level your workers use (change them later
with `concorde-configure`) and creates an honest stub of the root Module Spec. Complete the stub's
Purpose, Terminology, Usage, Design and Relationships in that candidate, then bring it into your
primary branch with `concorde-validate`, `concorde-deliver` and a separate merge request.

Existing current installations are verified and reused, not reinstalled on every call. Missing,
stale or conflicting local assets block execution and require explicit installer recovery. For a
normal Git-created worktree, use the same supported installer with `--preserve-project`:

```bash
python3 /explicit/project/.concorde/framework/scripts/install-concorde.py \
  --target /absolute/path/to/worktree --preserve-project --preview
# Inspect the proposal, then repeat with --apply.
```

This preserves inherited root guidance and a complete Protocol bundle without adopting ownership
or changing the accepted binding. Installation must finish before local Operations run. System
Pi/Node may be shared, but Frameworks and managed environments are not shared or symlinked between
worktrees. A candidate's own Pi session has all eleven public Operations through its local
`.pi/extensions/concorde-session.ts`; durable status and runs still belong only to primary.
See [installation and recovery](specs/concorde/distribution/installation.md#installing-another-worktree).
Source maintenance remains the separate private-entry path below, with no ambient installation.

**4. Read, edit and select Operations.**

```text
Read the complete registered Specs and explain how requests reach storage.
Edit the selected Module's contract and paired metadata to describe this approved change.
Use concorde-plan for target module.storage and task “Implement the approved retry policy”.
```

In Pi, use the `concorde` tool for the same retained Operations. Every bounded task receives an
explicit target; questions and Spec/registry edits are ordinary outer-agent work, not routed Operations.

## Choose an entry point

| You want to…                                     | Use                                      |
| :----------------------------------------------- | :--------------------------------------- |
| Assess the selected Spec for a task              | `concorde-context-solve`                 |
| Plan an explicit-target change                   | `concorde-plan`                          |
| Turn a current plan into acceptance tasks        | `concorde-tasks`                         |
| Implement accepted tasks within listed files     | `concorde-implement`                     |
| Review a Spec, including terminology consistency | `concorde-spec-review`                   |
| Review code against its Spec                     | `concorde-code-review`                   |
| Inspect, report, reopen or solve an Issue        | `concorde-issues`                        |
| Initialize or configure workers                  | `concorde-init` · `concorde-configure`   |
| Validate or deliver a candidate                  | `concorde-validate` · `concorde-deliver` |

These eleven compatibility capability names are the Pi tool entries. `describe-policy` previews
bounded grants without launching a worker; initialization/configuration use their explicit
proposal or apply contracts instead of a policy preview.

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

Open **[LangGraph Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024)** and
select `terminal-agent-operation`. This inspects the actual optional typed StateGraph. Execution
requires an explicitly supplied trusted native Agent service; no model is selected implicitly.
See [the Operation API and Studio guide](scripts/development/STUDIO.md). Native capabilities do not
redirect through `CONCORDE_STUDIO_URL`. Retaining the installed LangGraph dependency is intentional;
optional execution does not mean untested removal of installed dependencies.

## The Spec Protocol in brief

Concorde's independent **[Spec Protocol 10.0.0](protocol/README.md)** defines one specification
category, the Module Spec, and which part of it is written for human reading. A Module's reading entry
`module.md` answers five questions in order:

| Section           | The question it answers                                                          |
| :---------------- | :------------------------------------------------------------------------------- |
| **Purpose**       | What responsibility does this Module own, for whom and within which scope?       |
| **Terminology**   | Which concepts does the reader need, each defined once in its canonical table?   |
| **Usage**         | When and how is it used, with which inputs, results, errors and limits?          |
| **Design**        | How do its decomposition, state and constraints fulfill its guarantees, and why? |
| **Relationships** | Which entities collaborate, under which conditions, as a labeled Mermaid view?   |

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

### Typed executable inventory

The compatibility package [`operations/`](operations/__init__.py) declares eleven public capability
names, seven canonical native Agents and the separately selected `terminal_agent_operation` StateGraph
boundary. Every public catalog entry has an explicit kind; Issue bookkeeping actions are deterministic
Host services while `issues.solve` is a bounded native workflow. Roles are not duplicate private
model-backed Operation aliases. Canonical `operations/<role>/spec.md` and native preludes render the
owned Agent assets. No public path schedules a mandatory Graph or hidden old Pi-RPC worker.

### Launchers and tools

Commands are relative to this checkout; installed projects use the same scripts under
`.concorde/framework/`.

| Entry point                                                      | Use                                                                                                    |
| :--------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------- |
| `python3 scripts/run-operation.py <operation> < invocation.json` | Compatibility Host transport; native cognition is prepared/invoked through the candidate Pi entry. |
| `python3 scripts/concorde.py build` · `validate`                 | Render workers, the Pi catalog and schemas; run the Spec, Operation, contract and build-output checks. |
| `python3 scripts/concorde.py protocol-manifest`                  | Inspect or explicitly accept and bind a changed Protocol bundle.                                       |
| `python3 scripts/concorde.py docsite` · `usage`                  | Scaffold a project docsite; summarize recorded worker usage per run.                                   |
| `python3 scripts/install-concorde.py`                            | Preview or apply installation into a project.                                                          |
| `python3 scripts/issues.py`                                      | Inspect branch-local Issues from the command line.                                                     |
| [LangGraph Studio](scripts/development/STUDIO.md)                | Inspect/use the explicitly selected typed StateGraph Operation boundary.                                        |
| `npm --prefix docsite run <script>`                              | `start`, `build`, `validate`, `typecheck`, `test`, `check`.                                            |

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

Concorde self-maintenance uses a fresh Concorde-catalog-free writer in a candidate, followed by a
separate fresh sibling tester supplied only the exact candidate-built Pi entry, embedded catalog
and runtime provenance. Both disable inherited/discovered Concorde catalogs and never fork old
instructions or delegate tasks. The main coordinates from its initial worktree and integrates
only with explicit authorization. The writer formats, checks and commits, then stops writing
before testing. Failed tests return to maintenance followed by another fresh tester.

Source builds keep the Pi shim private at `generated/session/pi/concorde-session.ts`, never ambient
discovery. Use `select-session --mode test --pi-entry <absolute-private-entry> --runtime
<absolute-candidate-launcher> --output <absolute-candidate-.concorde/work/selection.json>` and
reverify with `select-session --verify <absolute-selection>` before the fresh host starts. Supply
`CONCORDE_SESSION_SELECTION`, only the returned exact `-e` entry and discovery-disable flags, and
a separate host-owned Pi configuration directory. Missing/stale artifacts or candidate Python
block; selection is provenance, not evidence of extension loading, tool use or model execution.
The host retains the actual file/tool grant; no global fallback or Studio redirect is allowed.

Never edit build output under `generated/`; change `prompts/operation-guidance/`, other authored
`prompts/`, `operations/` or `pi/extensions/` and rebuild. There is no standalone `skills/` product
or `skills` publishing command. See the
[source-checkout policy](AGENTS.md) and [development details](docs/workflow-guide.md#development).

---

[MIT licensed](LICENSE). Built with Concorde's own [Specs](specs/concorde/module.md).
