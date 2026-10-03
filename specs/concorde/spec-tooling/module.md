# Spec tooling

## Purpose

Spec tooling is the spec [part](../glossary.json#concept.part) of Concorde, the one that works on
Specs themselves. It checks that a project's Specs are structurally sound, computes from them what a
task may read and write, and serves them to agents and to people. Every Module of Concorde that
reads Specs relies on it to refuse a structure that cannot support a trustworthy boundary. It never
changes a [Spec](../glossary.json#concept.spec) on its own, never decides which
[task type](../glossary.json#concept.task-type) a piece of work gets, never launches a worker and
never enforces a boundary: a grant it computes is applied by the worker harness, to which Method
hands it. Its deterministic core reports failures with [its own error type](spec/errors.md), and
Views reports a failed build of its own.

The spec part depends on no other part, not even the Kernel: a project can install it alone to keep
its architecture described, checked, served over MCP and published, with no agent of Concorde's.
Judging whether a Spec is good enough for its reader calls a model, so the Spec reviews are Method's
Operations, not this part's.

## Overview

Spec tooling binds only the part's guidance and its part entries; its three children fulfil it,
and the other two rely on Spec core, which loads, checks and computes everything they present:

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
| Spec MCP server (stdio) | Spec MCP server | which Modules exist, what one selects, whom a change concerns, what grant a task type gives |
| Published site | Views | the Specs as pages for people |

<a id="uses-distribution"></a>

The spec part registers these commands, the Spec MCP server and its guidance with
[Distribution](../distribution/module.md), the installation host present in every installation,
through its [part registration](../glossary.json#concept.part-registration), the plain data whose
shape [Distribution's contract](../distribution/contracts.md#part-registration) fixes, together with its
install contribution: the [Protocol copy](../glossary.json#concept.protocol-copy) under
`.concorde/protocol/`, the project configuration's
[Protocol binding](../glossary.json#concept.protocol-binding) and the initialization of a project
that has no Spec yet.

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

Whoever changes a Module's Specs — in Concorde a [task session](../glossary.json#concept.task-session) or a `specify` worker on a task
branch, or the developer — runs `concorde spec-validation`, which reports every finding of the
[structural checks](../glossary.json#concept.structural-check) in one run; while it reports an
error, the change is not ready. Structure is all it proves: whether the Specs explain enough for
their reader is judged by a review, which Method's `spec_review` and `spec_panel` Operations run
where the method part is installed.

Every later run in that worktree computes its workers'
[grants](../glossary.json#concept.grant), the paths each may read and write, from those Specs;
an agent can ask the Spec MCP server which Modules a change concerns and what grant a task type
would give, and people read the same Specs on the published site. A worker's grant is computed by
Spec core and frozen by the Method step that launches the worker; the Spec MCP server and Views'
scaffold also call Spec core as a library. Every answer is computed from the Specs of one worktree,
so a change to the Specs on a task branch governs only that task.

## Why it is built this way

### A part that depends on nothing

The Spec tooling is the one part every Spec-reading Module relies on and the one a project may want
alone, so it depends on no part. It keeps its own copy of the few data utilities it shares in kind
with the Kernel — [typed values](../glossary.json#concept.typed-value),
[file transactions](../glossary.json#concept.file-transaction), schema checking and digests — in
its own code and with its own error types, accepting the duplication so that installing it pulls in
nothing else. The two copies agree on the formats the Kernel's contracts give, not on code, which
is why Spec core's `uses` of the Kernel is a reliance on formats alone. What it hands to other
parts leaves it as plain data: a [grant](../glossary.json#concept.grant) is Spec core's own record
([Grants](spec/contracts.md#grants)), which Method freezes and projects into the
[grant input](../worker-harness/workers/contracts.md#grant-input) the worker harness owns, so the
spec part never learns the harness's format.

### Split by what each child depends on

Spec core loads, checks and computes, and depends on nothing, so every other
[Module](../glossary.json#concept.module) can rely on it without a cycle. The Spec MCP server only
presents what Spec core computes, to agents, and adds no rule of its own. Views presents the same
Specs to people; its publisher is TypeScript and does not call Spec core: it parses the
[registry](../glossary.json#concept.registry) and metadata itself and recomputes each document's
selecting Modules, which must equal Spec core's `selected-by`
[impact index](../glossary.json#concept.impact-index), so a page that disagrees with a worker's
context is a Views defect; it leaves full structural conformance to the validator. No child calls a
model.

### One loader for every answer

Validation, grant computation and the Spec MCP server share Spec core's one loader on purpose, so an
answer an agent gets cannot disagree with the context a worker gets. That loader refuses a project
only for the fatal structural problems listed under
[loading failures](spec/contracts.md#loading-failures); every other problem is reported only by
`concorde spec-validation`, so a computed grant is no proof that validation passes. Validation
proves structure, and neither it nor anything else in this part judges readability or whether code
keeps a promise.

### No silently narrower answer

A failure never becomes a silently narrower answer. Spec core refuses with its error record instead
of returning part of a result; the Spec MCP server turns every refusal into a tool error, never a
partial answer; and a failed Views build deletes its candidate and keeps the published site.

### Part entries

<a id="realization.spec-tooling.part"></a>

The **Part entries** are the spec part's
[part registration](../glossary.json#concept.part-registration) and the code it names for
Distribution: the `concorde` commands `spec-validation`, `registry`, `grant` and `init`, which call
Spec core, `docsite`, which calls Views' scaffold, and `spec-mcp`, which runs the Spec MCP server,
each answering Spec core's shared envelope for Distribution to print except `spec-mcp`, which owns
standard input and output; and the install services, which place the docsite template Views'
inventory rule selects and keep an installed project's files bound through Spec core's
initializer. They belong to the part rather than to one child because they call all three, so
that Spec core imports neither Views nor the Spec MCP server
([req.spec.no-owner-imports](spec/requirements.md#req.spec.no-owner-imports)).

### Guidance

<a id="realization.spec-tooling.guidance"></a>

The **Spec tooling guidance** is the part's sections of the [main-session
guidance](../glossary.json#concept.main-session-guidance), kept in `prompts/guidance/spec/` and
registered under `guidance` in the part's registration, which
[Distribution](../distribution/module.md#guidance-composition) composes after Coordination's working
method wherever the part is installed: the project skill's "Project terms" and "Specs"
(`spec-validation`, `grant`, `registry --write`, the Spec MCP server and how to escalate Spec
tooling's own error record), the task-session prompt's project terms and Spec tooling's errors, and
the `CLAUDE.md` block's sentence on the project terms, beside which the installer imports the
glossary. Each section says what happens where a part it mentions is not installed.

## The children

- <a id="contains-spec"></a>**Spec core** implements the Spec Protocol: loading, validation, the
  registry mirror, [boundary sets](../glossary.json#concept.boundary-set), impact indexes, grants,
  initialization and the Protocol text, with its private copy of typed values and file transactions.
  It is the single source of every structural answer and must stay free of other Modules' code and
  of model calls.
- <a id="contains-spec-mcp"></a>**Spec MCP server** serves Spec core's answers to agents over local
  stdio, read-only and rooted at its worktree, adding no rule and refusing paths outside the root.
  Workers do not use it in this version; their grants come from the
  [Operation](../glossary.json#concept.operation) that launches them.
- <a id="contains-views"></a>**Views** publishes the registered Specs as a Docusaurus site and
  scaffolds that site into other projects. Its pages derive from the registry only and are never
  written back into a Spec or offered to an agent as context.
