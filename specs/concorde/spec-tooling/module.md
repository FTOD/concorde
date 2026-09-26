# Spec tooling

## Purpose

Spec tooling is the part of Concorde that works on Specs themselves. It checks that a project's
Specs are structurally sound, has workers review whether they are good enough for their reader,
computes from them what a task may read and write, and serves them to agents and to people. Every
other part of Concorde relies on it to refuse a structure that cannot support a trustworthy
boundary. It never changes a Spec on its own, never decides which task type a piece of work gets
and never enforces a boundary; enforcement belongs to the Harness. It reports failures with
[its own error type](spec/errors.md) and depends on no other part of Concorde to do so.

## Terminology

| Term | Definition |
| --- | --- |
| [Spec](../vocabulary.md#concept.concorde.spec) | |
| [Module](../vocabulary.md#concept.concorde.module) | |
| [Task type](../vocabulary.md#concept.concorde.task-type) | |
| [Boundary](../vocabulary.md#concept.concorde.boundary) | |
| [Main agent](../vocabulary.md#concept.concorde.main-agent) | |
| [Worker](../vocabulary.md#concept.concorde.worker) | |
| [Developer](../vocabulary.md#concept.concorde.developer) | |

Spec tooling defines no words of its own; each child defines the words of its interface, such as
the grant of Spec core or the review finding of Spec review.

## Usage

A developer or the main agent meets Spec tooling through one entry point per child:

| Entry point | Child | Answers |
| --- | --- | --- |
| `concorde validate` | Spec core | every structural finding, in one run |
| `spec_review` Operation | Spec review | workers' findings and a verdict on the named Modules' Specs |
| Spec MCP server (stdio) | Spec MCP server | which Modules exist, what one selects, whom a change concerns, what grant a task type gives |
| Published site | Views | the Specs as pages for people |

The Operation host is the one consumer that calls Spec core as a library, to compute and freeze a
worker's grant. Every answer is computed from the Specs of one worktree, so a Spec change on a task
branch governs only that task.

## Design

The children are split by what they depend on. Spec core loads, checks and computes, and depends on
nothing, so every other Module can rely on it without a cycle. The Spec MCP server and Views only
present what Spec core computes, to agents and to people, and add no rule of their own. Spec review
is the only child that calls a model, which is why it is kept apart from the deterministic core the
Harness itself depends on.

Maintaining and serving share one loader on purpose: a grant cannot be computed from a project the
validator would refuse, and a page cannot show a provenance that disagrees with a worker's context.
Validation proves structure, review judges readability and form, and neither judges whether code
keeps a promise.

### The children

Spec tooling binds no files of its own; its children fulfil it. Three of them only read what Spec
core computes:

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
  registry mirror, boundary sets, impact indexes, grants, initialization, typed values, file
  transactions and the Protocol text. It is the single source of every structural answer and must
  stay free of other Modules' code and of model calls.
- <a id="contains-spec-mcp"></a>**Spec MCP server** serves Spec core's answers to agents over local
  stdio, read-only and rooted at its worktree, adding no rule and refusing paths outside the root.
  Workers do not use it in this version; their grants come from the Operation host.
- <a id="contains-spec-review"></a>**Spec review** is the `spec_review` Operation: `review-spec`
  workers judge the named Modules' Specs against one checklist and return every blocking finding
  with a verdict. It never edits a Spec and never presents structural validity as quality.
- <a id="contains-views"></a>**Views** publishes the registered Specs as a Docusaurus site and
  scaffolds that site into other projects. Its pages derive from the registry only and are never
  written back into a Spec or offered to an agent as context.

### Around it

Spec core stays inside Spec tooling and uses no other Module, but Spec review reaches outside it,
because judging a Spec needs a model: it is launched through Workers and returns its findings inside
an Operation result.

