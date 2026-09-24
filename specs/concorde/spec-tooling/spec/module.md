# Spec core

## Purpose

Spec core is Concorde's implementation of the Spec Protocol and the deterministic heart of Spec
tooling. It loads a project's Specs, checks their structure, and computes from the declarations
alone what a task may read and write and whom a change concerns. It uses no other Module and never
calls a model. It does not judge whether a Spec explains enough or whether code keeps a promise,
does not decide which task type a piece of work gets, and never enforces a grant.

## Terminology

| Term | Definition |
| --- | --- |
| Registry | The project-wide index of Modules, which mirrors every Module's `module` block and is never itself a place where relations are declared. |
| Document | One registered Markdown reading file together with its `.md.json` metadata file, which share one identity and one owning Module. |
| Protocol binding | The project configuration's explicit acceptance of one installed Spec Protocol copy, recorded as its version and the digest of its manifest. |
| Structural check | One decidable rule of the Spec Protocol or of Concorde's Spec conventions, named by a rule identity and carrying the severity error or warning. |
| Boundary set | One of the five sets the Protocol derives for a Module: its Spec context, external context, implementation context, Spec scope or implementation scope. |
| Grant | The per-path access list, each path at level `names`, `ro` or `rw`, that one task type assigns to the bound Modules, computed from one worktree's Specs and identified by its context identity. |
| Context identity | The digest of the selected Spec sources and pinned external material together with the declarations that selected them. |
| Impact index | A derived reverse lookup that tells which Modules a change to a document, node, contract or file concerns. |
| Verification declaration | A statement in a test's own source that names the scenario identities the test verifies. |
| Typed value | A versioned JSON record `{type_id, schema_version, data}` whose data is checked against the schema its owner registered for that type. |
| File transaction | A set of whole-file writes, each bound to the digest of the bytes it replaces, that is applied completely or not at all. |
| Initial proposal | The exact files that initialization offers for a new project before anything is written. |
| [Module](../../vocabulary.md#concept.concorde.module) | |
| [Spec](../../vocabulary.md#concept.concorde.spec) | |
| [Task type](../../vocabulary.md#concept.concorde.task-type) | |
| [Spec context](../../vocabulary.md#concept.concorde.spec-context) | |
| [Implementation context](../../vocabulary.md#concept.concorde.implementation-context) | |
| [Boundary](../../vocabulary.md#concept.concorde.boundary) | |
| [Worker](../../vocabulary.md#concept.concorde.worker) | |
| [Evidence](../../vocabulary.md#concept.concorde.evidence) | |
| [Developer](../../vocabulary.md#concept.concorde.developer) | |

## Usage

What each part of Spec core reads and produces:

```d2
model: Spec model
validator: Validator
grants: Grant computation
init: Project initializer
writer: Transaction writer
types: Typed values

registry: Registry
document: Document
binding: Protocol binding
sets: Boundary set
impact: Impact index
check: Structural check
declaration: Verification declaration
grant: Grant
identity: Context identity
value: Typed value
transaction: File transaction
proposal: Initial proposal

model -> registry: loads
model -> document: loads
model -> binding: verifies
model -> sets: computes
model -> impact: computes
validator -> model: checks the Specs loaded by
validator -> check: runs
validator -> declaration: reads
validator -> registry: regenerates the mirror of
grants -> sets: applies a task type to
grants -> grant: computes
grants -> identity: computes
types -> value: checks
writer -> transaction: applies
init -> proposal: proposes
init -> writer: writes through
init -> validator: validates the result with
```

<a id="concept.spec.registry"></a><a id="concept.spec.document"></a><a id="concept.spec.protocol-binding"></a>

**Loading.** Every program that needs the Specs loads the configuration `.concorde/config.json`,
the Protocol binding, the registry `.concorde/specs.json` and the documents each entry registers.
The registry only mirrors each entry's `module` block; the entry is where relations are declared.
Nothing unregistered is a Spec, a link never adds a document, and a loaded repository is an
immutable snapshot. Loading refuses a binding that disagrees with the installed copy
(`protocol_mismatch`), so new rules apply only after the developer rebinds. See
[Loading](design.md#loading).

<a id="concept.spec.structural-check"></a><a id="concept.spec.verification-declaration"></a>

**Validation.** `python3 scripts/concorde.py validate` reports every structural finding in one run,
each with its rule, severity, file and remediation; errors make the result `invalid`. Coverage comes
from verification declarations in the tests' own source, parsed and never run
([syntax](contracts.md#verification-declarations)). A task may change its own `module` block but
never the registry, so `concorde.py registry --write` regenerates a stale mirror
(`CHK.registry.mirror`). Success is evidence about structure only; see
[What validation tells you](validation.md).

<a id="concept.spec.boundary-set"></a><a id="concept.spec.impact-index"></a>

**Boundaries and impact.** For the Modules a task is bound to, Spec core returns the five boundary
sets, selected one level deep. The impact indexes (`selected-by`, `referenced-by`,
`implemented-by`, binding Modules, changed definitions) say whom a change concerns and never widen
a boundary. Which Modules a task may edit or must re-review is the Operations' policy. See
[Boundary sets and impact indexes](design.md#boundary-sets-and-impact-indexes).

<a id="concept.spec.grant"></a><a id="concept.spec.context-identity"></a>

**Grants.** `concorde grant --root <worktree> --modules <ids> --type <task type>` computes, from
one worktree's Specs, which paths a worker may change (`rw`), read (`ro`) or only know by name
(`names`); every other path is denied. The grant carries its context identity, so a caller can tell
later whether anything the worker could read has changed. It refuses to make writable a file that
an unbound Module also binds. The Operation host freezes the grant into a worker at launch and the
Spec MCP server returns the same computation; Spec core neither stores nor enforces it. See
[Grants and context identity](design.md#grants-and-context-identity).

<a id="concept.spec.typed-value"></a><a id="concept.spec.file-transaction"></a><a id="concept.spec.initial-proposal"></a>

**Shared services.** Every structured value Modules exchange is a typed value
`{type_id, schema_version, data}` whose owner registers its schema
([typed values](contracts.md#typed-values)). A file transaction writes a set of files completely or
not at all, each write bound to the digest it replaces. `initialize(root, package, data)` first
proposes the exact first files and their digest, then applies exactly that proposal and keeps it
only if the project validates; it refuses `already_initialized` and `not_installed`. Which command
exposes it is Distribution's decision.

## Design

How Spec core is built, with the files each part binds:

```d2
core: Spec core {
  model: Spec model {
    "model.py"
    "repository.py"
    "repository_base.py"
    "content_model.py"
    "content_repository.py"
    "syntax.py"
    "boundaries.py"
    "impact.py"
  }
  validator: Validator {
    "validation.py"
    "verification.py"
    "registry.py"
    "diagnostics.py"
  }
  grants: Grant computation {
    "grants.py"
  }
  init: Project initializer {
    "initialize.py"
  }
  writer: Transaction writer {
    "changes.py"
    "content_changes.py"
  }
  types: Typed values {
    "typed_data.py"
    "schema.py"
    "frontmatter.py"
  }
  errors: Spec tooling errors {
    "errors.py"
  }
  assets: Protocol assets {
    "prompts/protocol/"
    "protocol/manifest.json"
  }
  text: Protocol text {
    "protocol/"
  }
  validator -> model: checks the Specs loaded by
  model -> assets: checks the installed copy against
  init -> writer: writes through
  init -> validator: validates the result with
  assets -> text: packages
}
```

Python sources are under `src/concorde/spec/` and tests under `tests/concorde/spec/`.

- <a id="realization.spec.model"></a>**Spec model** loads the registry and documents and computes
  every set and index from declarations alone, never reading implementation contents.
- <a id="realization.spec.validator"></a>**Validator** evaluates every check over one loaded model,
  reads verification declarations and configured-check inputs without running anything, and
  regenerates the registry mirror.
- <a id="realization.spec.grants"></a>**Grant computation** applies a task type to the bound
  Modules' boundary sets, computes the context identity and refuses unbound shared writes.
- <a id="realization.spec.initializer"></a>**Project initializer** proposes and applies the first
  Spec of a project.
- <a id="realization.spec.transactions"></a>**Transaction writer** applies digest-bound file
  transactions and confirms pending entries whose files now exist.
- <a id="realization.spec.typed-values"></a>**Typed values** hold the registration table, the closed
  offline checker, shared schema building blocks, strict JSON, safe paths and the front-matter
  parser.
- <a id="realization.spec.errors"></a>**Spec tooling errors** are Spec tooling's own error type:
  code, message, location, reason, remediation and causes, as the [error record](errors.md) defines.
  They depend on no other Module.
- <a id="realization.spec.protocol-text"></a><a id="realization.spec.protocol-assets"></a>**Protocol
  text** is the standard itself; **Protocol assets** are the bundle sources and tracked manifest
  from which Distribution renders the installed copy.
- <a id="realization.spec.tests"></a>**Spec tests** exercise all of this on small fixture projects.

One loader serves every query, grant and check, so they cannot disagree about who owns a document or
what a relation selects. For consumers it refuses a project whose structure cannot support a
trustworthy boundary; for the validator it collects the same problems as findings. Spec core uses
nothing: other Modules' schemas arrive through registration, their file locations as arguments, and
their concerns as their own configured checks. The grant computation sits next to the boundary sets
so that the Operation host and the Spec MCP server give the same task the same boundary. The
reasons are in [How Spec core works](design.md).

## Relationships

Spec core uses no Module. Everything else relies on it:

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
harness: Harness {
  workers: Workers
  checks: Check execution
}
operations: Operations
tasks: Tasks
issues: Issues
distribution: Distribution
harness.workers -> tooling.core
harness.checks -> tooling.core
operations -> tooling.core
tasks -> tooling.core
issues -> tooling.core
distribution -> tooling.core
```

Each consumer declares its own `uses` with the promises it relies on, and none of them is a
dependency of Spec core, so their changes never change what it promises.
