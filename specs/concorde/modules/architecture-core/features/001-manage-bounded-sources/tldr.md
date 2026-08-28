# TL;DR: Manage Bounded Architecture Sources

`feature.architecture-core.manage-bounded-sources` · specified at `module.concorde.architecture-core`
· refines `feature.concorde.workflow` · about three minutes. This page is enough to understand what
Architecture Core does with the specification hierarchy and what must hold; the links at the end
only redirect you when you want more.

## Purpose

A maintainer or coding agent can safely propose a root specification hierarchy, retrieve exactly
one architectural level for feature placement or implementation, and deterministically validate the
maintained module, feature, contract, scenario, evidence, and view relationships. It exists so that
bounded context can be trusted and validation can act as a review gate: every answer is either a
complete result or explicit findings, never a guess and never a silent partial mutation.

## Functionality

Three deterministic operations, reached through one service protocol from an installed Concorde
command:

| Operation | What it does | What it never does |
|---|---|---|
| Initialization | Returns a proposal for the root hierarchy; applies it only after explicit acceptance. | Overwrite existing sources. |
| Context | Returns the requested level: the module, its immediate submodules, current-level features and contracts, scenarios, and stable deeper references, with concise boundary I/O. | Expose grandchildren or expand deeper bodies. |
| Validation | Reads every maintained source and returns complete, deterministic findings. | Write anything, or infer evidence it cannot establish. |

Architecture Core owns source semantics, stable identity, relationship resolution, one-level
visibility, and validation findings. It stays independent of agent command syntax, distribution,
Archify rendering, and Docusaurus publication.

**Not part of this feature**: agent invocation syntax, distribution, diagram rendering, site
publication, implementation correctness, and choosing architectural ownership without maintainer
review.

## Structure

The parent feature's core view
<a href="/architecture/concorde-workflow-components.html">workflow components</a> (maintained source
`specs/concorde/features/001-concorde-workflow/diagrams/concorde-workflow-components.json`) shows
how installed command surfaces reach this runtime and which architecture sources it reads; a child
diagram would repeat those boundaries.

```text
installed Concorde command (materialized by Spec Kit Integration)
   ──▶ Concorde Architecture Service Protocol v1 request: one operation + one target path or stable ID
   ──▶ Architecture Core runtime (standard-library Python, extensions/concorde/runtime/concorde/)
         reads specs/**: module.md · design.md · level views · contracts · feature roots
   ◀── complete result (proposal · bounded level · sorted findings)  — or explicit findings
```

The runtime is the module's only realization; `contract.core.architecture-services` is its only
provided boundary, with Spec Kit Integration and Documentation as counterparties. The required set is
explicitly empty: filesystem access is an implementation detail constrained to the project root.

## Logic

**One request**

1. An installed command sends one request naming the operation and its target.
2. The runtime parses the hierarchy and resolves stable IDs and project-relative paths without
   agent inference.
3. Initialization returns a proposal; apply happens only on explicit acceptance and refuses to
   overwrite. Context projects exactly one level. Validation runs its deterministic rules read-only.
4. The response is a complete result or explicit findings; repeated runs on unchanged inputs are
   byte-stable.

**Rules the implementation must keep**

- Initialization separates the proposal from the explicit accepted apply and refuses overwrites
  (Requirements, item 1).
- Context includes the current module and its immediate children only, with concise boundary I/O
  (Requirements, item 2).
- Validation is deterministic, complete, and non-mutating, and preserves unknown evidence honestly
  rather than inferring it (Requirements, item 3).

## Read Next

- **Exact outcome, scenario, and requirements** — [spec.md](spec.md).
- **How the accepted implementation realizes this feature** — [design.md](design.md).
- **The contract** — [contract.core.architecture-services](../../contracts/architecture-services/contract.md).
- **The level this feature belongs to** — [module.md](../../module.md) (the Architecture Core
  summary) and its [design reference](../../design.md); the root summary is
  [module.md](../../../../module.md).
- **The parent feature** — [Concorde Workflow](../../../../features/001-concorde-workflow/tldr.md),
  and its steps this feature executes:
  [initialize](../../../../features/001-concorde-workflow/subfeatures/001-initialize-architecture/spec.md),
  [context](../../../../features/001-concorde-workflow/subfeatures/002-retrieve-bounded-context/spec.md),
  [validate](../../../../features/001-concorde-workflow/subfeatures/008-validate-architecture/spec.md).
- **Framework guide** — [docs/commands.md](../../../../../../docs/commands.md) (what actually runs).
