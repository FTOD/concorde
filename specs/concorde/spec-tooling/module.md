# Spec tooling

## Purpose

Spec tooling is the part of Concorde that works on Specs themselves. It checks that a project's
Specs are structurally sound, has workers review whether they are good enough for their reader,
computes from them what a task may read and write, and serves them to agents and to people. Every
other part of Concorde relies on it to refuse a structure that cannot support a trustworthy
boundary. It never changes a [Spec](../glossary.json#concept.spec) on its own, never decides which
[task type](../glossary.json#concept.task-type) a piece of work gets and never enforces a boundary;
enforcement belongs to the Harness. Its deterministic core reports failures with
[its own error type](spec/errors.md) and depends on no other part of Concorde to do so; Spec review,
which calls a model, reports inside a [run result](../glossary.json#concept.run-result) like any
Operation, and Views reports a failed build of its own.

## Usage

A change to a Module's Specs usually meets Spec tooling in this order. On a task branch, the
developer, the [main agent](../glossary.json#concept.main-agent) or a `specify` worker changes a
Module's Specs. `concorde spec-validation` then reports every finding of the
[structural checks](../glossary.json#concept.structural-check) in one run; while it reports an
error, the change is not ready for delivery. Once the Specs are valid,
`concorde run spec_review` (or `spec_panel`) has workers judge the named Modules' Specs and returns
their findings with a [review verdict](../glossary.json#concept.review-verdict): `accepted`;
`changes_required`, when a blocking finding against the Specs stands; or `incomplete`, which names
each Module that could not be reviewed and why. Every later run in that worktree computes its workers'
[grants](../glossary.json#concept.grant), the paths each may read and write, from those Specs; the
main agent can ask the Spec MCP server which Modules a change concerns and what grant a task type
would give, and people read the same Specs on the published site. Each step has its own entry
point, one per child:

| Entry point | Child | Answers |
| --- | --- | --- |
| `concorde spec-validation` | Spec core | every structural finding, in one run |
| `spec_review` and `spec_panel` [Operations](../glossary.json#concept.operation) | Spec review | workers' findings and a verdict on the named Modules' Specs |
| Spec MCP server (stdio) | Spec MCP server | which Modules exist, what one selects, whom a change concerns, what grant a task type gives |
| Published site | Views | the Specs as pages for people |

A worker's grant is computed by Spec core and frozen by the Operation that launches the worker,
through the [Execution runner](../glossary.json#concept.execution-runner); the Spec MCP server,
Spec review and Views' scaffold also call Spec core as a library, for loading, typed values and file
transactions. Every answer is computed from the Specs of one worktree, so a change to the Specs on
a task branch governs only that task.

## Design

The children are split by what they depend on. Spec core loads, checks and computes, and depends on
nothing, so every other [Module](../glossary.json#concept.module) can rely on it without a cycle.
The Spec MCP server only presents what Spec core computes, to agents, and adds no rule of its own.
Views presents the same Specs to people; its publisher is TypeScript and does not call Spec core: it
parses the [registry](../glossary.json#concept.registry) and metadata itself and recomputes each document's
selecting Modules, which must equal Spec core's `selected-by`
[impact index](../glossary.json#concept.impact-index), so a page that disagrees with a worker's
context is a Views defect; it leaves full structural conformance to the validator. Spec review is
the only child that calls a model, which is why it is kept apart from the deterministic core the
Harness itself depends on.

Validation, grant computation and the Spec MCP server share Spec core's one loader on purpose, so an
answer an agent gets cannot disagree with the context a worker gets. That loader refuses a project
only for the fatal structural problems listed under
[loading failures](spec/contracts.md#loading-failures); every other problem is reported only by
`concorde spec-validation`, so a computed grant is no proof that validation passes. Validation
proves structure, review judges readability and form, and neither judges whether code keeps a
promise.

A failure never becomes a silently narrower answer. Spec core refuses with its error record instead
of returning part of a result; Spec review fails when the Specs cannot be loaded and marks a Module
`incomplete` when its structure is invalid or no grant can be computed for it; the Spec MCP server
turns every refusal into a tool error, never a partial answer; and a failed Views build deletes its
candidate and keeps the published site.

### The children

Spec tooling binds no files of its own; its children fulfil it. The other three rely on Spec core:

```d2
tooling: Spec tooling {
  core: Spec core
  mcp: Spec MCP server
  review: Spec review
  views: Views
  mcp -> core
  review -> core
  views -> core
}
```

- <a id="contains-spec"></a>**Spec core** implements the Spec Protocol: loading, validation, the
  registry mirror, [boundary sets](../glossary.json#concept.boundary-set), impact indexes, grants,
  initialization, [typed values](../glossary.json#concept.typed-value),
  [file transactions](../glossary.json#concept.file-transaction) and the Protocol text. It is the
  single source of every structural answer and must stay free of other Modules' code and of model
  calls.
- <a id="contains-spec-mcp"></a>**Spec MCP server** serves Spec core's answers to agents over local
  stdio, read-only and rooted at its worktree, adding no rule and refusing paths outside the root.
  Workers do not use it in this version; their grants come from the
  [Operation](../glossary.json#concept.operation) that launches them.
- <a id="contains-spec-review"></a>**Spec review** is the `spec_review` and `spec_panel`
  Operations: `review-spec` workers judge the named Modules' Specs against one checklist and return
  every blocking finding, and the Operation derives the verdict from them, in a panel after a chair
  has audited and merged the reviewers' findings. It never edits a Spec and never presents
  structural validity as quality.
- <a id="contains-views"></a>**Views** publishes the registered Specs as a Docusaurus site and
  scaffolds that site into other projects. Its pages derive from the registry only and are never
  written back into a Spec or offered to an agent as context.

### Around it

Spec core stays inside Spec tooling and uses no other Module, but Spec review reaches outside it,
because judging a Spec needs a model: it is launched through Workers and returns its findings inside
a [run result](../glossary.json#concept.run-result).

