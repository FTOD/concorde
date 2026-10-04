# Spec tooling

## Purpose

Spec tooling is the spec [part](../glossary.json#concept.part) of Concorde, the one that works on
Specs themselves. Spec tooling performs these functions:

- It checks that a project's Specs are structurally sound.
- It computes from them what a task may read and write.
- It serves them to agents and to people.

Every Module of Concorde that reads Specs relies on it to refuse a structure that cannot support a
trustworthy boundary. It never changes a [Spec](../glossary.json#concept.spec) on its own.
It writes Spec files only when asked to, by these commands or services:

- `concorde init --apply`, which creates a project's first Spec.
- `concorde registry --write`, which regenerates the [registry](../glossary.json#concept.registry)
  mirror.
- The install services, which keep the installation realization's file entries bound after an
  install or update.

Each of these writes exactly what a deterministic rule derives. None decides a promise.
Spec tooling never does any of these things:

- Decide which [task type](../glossary.json#concept.task-type) a piece of work gets.
- Launch a [worker](../glossary.json#concept.worker).
- Enforce a boundary.

The worker harness applies a grant Spec tooling computes. The worker harness is the part that
prepares each worker's permissions and launches it. Method hands the grant to the worker harness.
Method is the part whose [Operations](../glossary.json#concept.operation) launch workers.
Spec tooling's deterministic core reports failures with [its own error type](spec/errors.md).
Views reports a failed build of its own.

The spec part depends on no other part, not even the Kernel. The Kernel is the part that defines the
data formats and locks the other parts share. A project can install Spec tooling alone, with no
agent of Concorde's, for these purposes:

- To keep its architecture described.
- To keep its architecture checked.
- To keep its architecture served over MCP.
- To keep its architecture published.

Judging whether a Spec is good enough for its reader calls a model, so the Spec reviews are Method's
Operations, not this part's.

## Overview

Spec tooling binds only the part's guidance and its part entries. Its three children fulfil it.
The other two rely on Spec core, which performs these functions:

- It loads everything they present.
- It checks everything they present.
- It computes everything they present.

```d2
tooling: Spec tooling {
  core: Spec core
  mcp: Spec MCP server
  views: Views
  mcp -> core
  views -> core
}
```

Each child has its own entry point:

| Entry point | Child | Answers |
| --- | --- | --- |
| `concorde spec-validation` | Spec core | every structural finding, in one run |
| `concorde registry`, `concorde grant`, `concorde init` | Spec core | the registry mirror, the grant a task type would give, a project's first Spec |
| `concorde spec-mcp`, a stdio server registered in the project's `.mcp.json` ([using it](spec-mcp/module.md#using-the-server)) | Spec MCP server | which Modules exist, what one declares and selects, whom a change concerns, what grant a task type gives, every structural finding |
| `npm run build` in `docsite/`; `concorde docsite --propose` and `--apply --proposal FILE` in another project ([the commands](views/module.md#the-commands)) | Views | the Specs as pages for people; the same site scaffolded into another project |

<a id="uses-distribution"></a>

Through its [part registration](../glossary.json#concept.part-registration), the spec part registers
these commands, the Spec MCP server and its guidance with [Distribution](../distribution/module.md).
Distribution is the installation host present in every installation.
The part registration is plain data whose shape
[Distribution's contract](../distribution/contracts.md#part-registration) fixes.
The spec part also registers its install contribution through its part registration.
The install contribution comprises these items:

- The [Protocol copy](../glossary.json#concept.protocol-copy) under `.concorde/protocol/`.
- The project configuration's [Protocol binding](../glossary.json#concept.protocol-binding).
- The initialization of a project that has no Spec yet.

### A Spec change through Spec tooling

A change to a Module's Specs usually meets Spec tooling in this order:

```d2 illustrative
direction: down
change: "Change a Module's Specs:\na task session, a specify worker,\nthe developer"
core: "Spec core" {
  validate: "concorde spec-validation:\nevery structural finding"
  error: "An error finding?" {shape: diamond}
}
ready: "Specs structurally sound:\nready for review and\nthe next step" {shape: page}
grant: "Every later grant computed\nfrom these Specs"
change -> core.validate -> core.error
core.error -> change: "yes: not ready"
core.error -> ready: no
ready -> grant
```

Whoever changes a Module's Specs runs `concorde spec-validation`. In Concorde, the changer is one of
these actors:

- A [task session](../glossary.json#concept.task-session).
- A `specify` worker on a task branch.
- The developer.

The command reports every finding of the [structural checks](../glossary.json#concept.structural-check)
in one run. While it reports an error, the change is not ready. Structure is all it proves.
A review judges whether the Specs explain enough for their reader.
Where the method part is installed, Method's `spec_review` and `spec_panel` Operations run that review.

Every later run in that worktree computes its workers'
[grants](../glossary.json#concept.grant) from those Specs. The grants are the paths each may read and
write. An agent can ask the Spec MCP server which Modules a change concerns and what grant a task
type would give. People read the same Specs on the published site.
Spec core computes a worker's grant. The Method step that launches the worker freezes the grant.
The Spec MCP server and Views' scaffold also call Spec core as a library.
Every answer is computed from the Specs of one worktree, so a change to the Specs on a task branch
governs only that task.

## Why it is built this way

### A part that depends on nothing

The Spec tooling is the one part every Spec-reading Module relies on. A project may want this part
alone, so it depends on no part. In its own code and with its own error types, it keeps its own copy
of these few data utilities shared in kind with the Kernel:

- [typed values](../glossary.json#concept.typed-value).
- [file transactions](../glossary.json#concept.file-transaction).
- Schema checking.
- Digests.

It accepts the duplication so that installing it pulls in nothing else.
The two copies agree on the formats the Kernel's contracts give, not on code.
That is why Spec core's `uses` of the Kernel is a reliance on formats alone.
What it hands to other parts leaves it as plain data.
A [grant](../glossary.json#concept.grant) is Spec core's own record
([Grants](spec/contracts.md#grants)). Method freezes that record and projects it into the
[grant input](../worker-harness/workers/contracts.md#grant-input) the worker harness owns.
This keeps the spec part from ever learning the harness's format.

### Split by what each child depends on

Spec core performs these functions:

- It loads.
- It checks.
- It computes.

Spec core depends on nothing, so every other [Module](../glossary.json#concept.module) can rely on
it without a cycle. The Spec MCP server only presents what Spec core computes, to agents, and adds
no rule of its own. Views presents the same Specs to people. Its publisher is TypeScript and does
not call Spec core. The publisher parses the [registry](../glossary.json#concept.registry) and
metadata itself. It recomputes each document's selecting Modules.
These must equal Spec core's `selected-by` [impact index](../glossary.json#concept.impact-index).
A page that disagrees with a worker's context is therefore a Views defect.
The publisher leaves full structural conformance to the validator. No child calls a model.

### One loader for every answer

Validation, grant computation and the Spec MCP server share Spec core's one loader on purpose.
This keeps an answer an agent gets from disagreeing with the context a worker gets.
That loader refuses a project only for the fatal structural problems listed under
[loading failures](spec/contracts.md#loading-failures).
Every other problem is reported only by `concorde spec-validation`, so a computed grant is no proof
that validation passes. Validation proves structure.
Neither it nor anything else in this part judges readability or whether code keeps a promise.

### No silently narrower answer

A failure never becomes a silently narrower answer. Spec core refuses with its error record instead
of returning part of a result. The Spec MCP server turns every refusal into a tool error, never a
partial answer. Except when the filesystem refuses the rollback of a failed promotion, a failed
Views build deletes its candidate and keeps the published site.
When the filesystem refuses that rollback, the previous site is left for manual recovery, as
Views' [promotion](views/pipeline.md#promotion) says.

### Part entries

<a id="realization.spec-tooling.part"></a>

The **Part entries** are the spec part's
[part registration](../glossary.json#concept.part-registration) and the code it names for
Distribution. Its commands are these `concorde` commands:

- `spec-validation`, `registry`, `grant` and `init`, which call Spec core.
- `docsite`, which calls Views' scaffold.
- `spec-mcp`, which runs the Spec MCP server.

Except `spec-mcp`, each command answers Spec core's
[shared envelope](spec/contracts.md#validation-result) for Distribution to print.
The `spec-mcp` command owns standard input and output.
The other Part entries are the install services.
These services place the docsite template Views' inventory rule selects.
After every install or update, they keep the installation realization's exact file entries in step
with the installation record through Spec core's `bind_installation`
([Initialization](spec/contracts.md#initialization)).
The Part entries belong to the part rather than to one child because they call all three.
This keeps Spec core from importing either Views or the Spec MCP server
([req.spec.no-owner-imports](spec/requirements.md#req.spec.no-owner-imports)).

<a id="init-command"></a>

The `init` command is a thin adapter over Spec core's `initialize`
([Initialization](spec/contracts.md#initialization)). `concorde init --propose --name <name>
[--target <id>] [--python <interpreter>]` calls it with action `propose` (`--target` defaulting to
`module.project`). `concorde init --apply --proposal <file>` reads the project-relative JSON
`<file>`. The file must be an object holding at least `proposal` and `proposal_digest`.
The whole `result` that `--propose` printed is one such object.
The apply command calls `initialize` with action `apply` and those two fields.
Any other field of the file is ignored. The proposal itself is checked by `initialize`.
Either way the command prints Spec core's [shared envelope](spec/contracts.md#validation-result)
with `tool` `init` and `target` `.`.
On success, the envelope has status `success` with `initialize`'s answer as `result` (exit code 0).
That answer's own `status` is `proposed` or `applied`.
On refusal, the envelope has status `failed` with the refusal's
[error record](spec/errors.md) as `error` (exit code 3).
Besides `initialize`'s own refusals, the adapter adds `invalid_input` for these cases:

- A malformed command line.
- A propose without `--name`.
- An apply without `--proposal`.
- A proposal file that cannot be read as JSON.

For a file that is not an object holding both fields, the adapter adds `invalid_proposal`.

```d2 illustrative
direction: right
distribution: Distribution {
  command: "concorde command"
  installer: installer
  composition: guidance composition
}
part: Spec tooling {
  entries: Part entries
  guidance: Guidance
  core: Spec core
  mcp: Spec MCP server
  views: Views
  entries -> core: "spec-validation, registry,\ngrant, init, bind"
  entries -> views: "docsite, template"
  entries -> mcp: spec-mcp
}
distribution.command -> part.entries: routes a command
distribution.installer -> part.entries: "install services"
part.guidance -> distribution.composition: sections
```

### Guidance

<a id="realization.spec-tooling.guidance"></a>

The **Spec tooling guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance). The sections are kept in
`prompts/guidance/spec/` and registered under `guidance` in the part's registration.
Wherever the part is installed,
[Distribution](../distribution/module.md#guidance-composition) composes these sections after the
working method of Coordination. Coordination is the part of the
[main agent](../glossary.json#concept.main-agent), its tasks and their task sessions.
The Spec tooling guidance comprises these sections:

- The project skill's "Project terms" and "Specs" (`spec-validation`, `grant`, `registry --write`,
  the Spec MCP server and how to escalate Spec tooling's own error record).
- The task-session prompt's project terms and Spec tooling's errors.
- The `CLAUDE.md` block's sentence on the project terms, beside which the installer imports the
  glossary.

Each section says what happens where a part it mentions is not installed.

## The children

- <a id="contains-spec"></a>**Spec core** implements the Spec Protocol: loading, validation, the
  registry mirror, [boundary sets](../glossary.json#concept.boundary-set), impact indexes, grants,
  initialization and the Protocol text. Spec core has its private copy of typed values and file
  transactions.
  It is the single source of every structural answer. Spec core must stay free of other Modules'
  code and of model calls.
- <a id="contains-spec-mcp"></a>**Spec MCP server** serves Spec core's answers to agents over local
  stdio. The server is read-only and rooted at its worktree. It adds no rule and refuses paths
  outside the root. Workers do not use it in this version. Their grants come from the
  [Operation](../glossary.json#concept.operation) that launches them.
- <a id="contains-views"></a>**Views** publishes the registered Specs as a Docusaurus site and
  scaffolds that site into other projects. Its pages derive from the registry only and are never
  written back into a Spec or offered to an agent as context.
