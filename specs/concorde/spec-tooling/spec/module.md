# Spec core

## Purpose

Spec core is Concorde's implementation of the [Spec](../../glossary.json#concept.spec) Protocol and
the deterministic heart of Spec tooling. It loads a project's Specs, checks their structure, and
computes from the declarations alone what a task may read and write and whom a change concerns. It
uses no other [Module](../../glossary.json#concept.module) and never calls a model. It does not
judge whether a Spec explains enough or whether code keeps a promise, does not decide which
[task type](../../glossary.json#concept.task-type) a piece of work gets, and never enforces a grant.

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

The commands named below are `concorde` commands; in the Concorde checkout itself they run as
`python3 scripts/concorde.py`.

<a id="concept.registry"></a><a id="concept.document"></a><a id="concept.protocol-binding"></a>

**Loading.** Every program that needs the Specs loads the configuration `.concorde/config.json`, the
[Protocol binding](../../glossary.json#concept.protocol-binding), the registry
`.concorde/specs.json`, the documents each entry registers and the project glossary the root
entry declares, which holds every concept with its owner and one-sentence definition. The registry
only mirrors each entry's `module` block; the entry is where relations are declared. Nothing
unregistered is a Spec, a link never adds a document, and a loaded repository is an immutable
snapshot. Loading refuses a
binding that disagrees with the installed copy (`protocol_mismatch`), so new rules apply only after
the developer rebinds.

<a id="concept.structural-check"></a><a id="concept.verification-declaration"></a>

**Validation.** `concorde spec-validation` reports every structural finding in one run, each with
its rule, severity, file and remediation; errors make the result `invalid`. Coverage comes from
[verification declarations](../../glossary.json#concept.verification-declaration) in the tests' own
source, parsed and never run ([syntax](contracts.md#verification-declarations)). A task may change
its own `module` block but never the registry, so `concorde registry --write` regenerates a stale
mirror (`CHK.registry.mirror`). Success is evidence about structure only; see
[What validation tells you](validation.md).

<a id="concept.boundary-set"></a><a id="concept.impact-index"></a>

**Boundaries and impact.** For the Modules a task is bound to, Spec core returns the six boundary
sets: each Module's five, selected one level deep, and the project-wide ProjectImplementation. A
Module's [Spec context](../../glossary.json#concept.spec-context) also holds its terms: the glossary
entries of the concepts it owns, of the concepts its selected documents link or relate to and of
those its `relies_on` names, closed over the terms those definitions link and their `narrows`,
`supersedes` and `relates` targets, so a reader knows every word its documents use without reading
the owners' documents. The impact indexes (`selected-by`, `referenced-by`, `implemented-by`,
`covered-by`, binding Modules, changed definitions) say whom a change concerns and never widen a
boundary. Which Modules a task may edit or must re-review is the Operations' policy.

<a id="concept.grant"></a><a id="concept.context-identity"></a>

**Grants.** `concorde grant --root <worktree> --modules <ids> --type <task type>` computes, from one
worktree's Specs, which paths a worker may change (`rw`), read (`ro`) or only know by name
(`names`); every other path is denied. A task type that reads code reads the whole project's code,
the Protocol's ProjectImplementation, but writes only within the bound Modules' scopes. The grant
carries the bound Modules' terms, whole glossary entries, and its
[context identity](../../glossary.json#concept.context-identity), so a caller can tell later
whether anything the worker could read has changed. A grant that writes Specs makes the
glossary file writable, since a concept is declared there; that its writes stay within the bound
Modules' own entries is checked after the worker, by Workers'
[write audit](../../glossary.json#concept.write-audit). It refuses to make writable a file that an
unbound Module also binds, and it never makes writable an installed file, one the installation
record `.concorde/install.json` lists as the installer's own: such a file is bound only by its exact
path (`CHK.binds.installed`) and granted at most `ro`, because the installer replaces it on every
update and the agents working on the project are configured by it. The
[Operation](../../glossary.json#concept.operation) that launches a worker freezes the grant into it
at launch and the Spec MCP server returns the same computation; Spec core neither stores nor
enforces it.

<a id="concept.typed-value"></a><a id="concept.file-transaction"></a><a id="concept.initial-proposal"></a>

**Shared services.** Every structured value Modules exchange is a
[typed value](../../glossary.json#concept.typed-value) `{type_id, schema_version, data}` whose owner
registers its schema ([typed values](contracts.md#typed-values)). A
[file transaction](../../glossary.json#concept.file-transaction) writes a set of files completely or
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
  reads verification declarations and
  [configured-check](../../glossary.json#concept.configured-check) inputs without running anything,
  and regenerates the registry mirror.
- <a id="realization.spec.grants"></a>**[Grant](../../glossary.json#concept.grant) computation**
  applies a task type to the bound Modules'
  [boundary sets](../../glossary.json#concept.boundary-set), computes the context identity and
  refuses unbound shared writes.
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

**Loading.** One loader serves every query, grant and check, so they cannot disagree about who owns
a document or what a relation selects. A link never adds a document, which is what lets every set be
enumerated from declarations alone. Opened for consumers, the loader refuses a project whose
structure cannot support a trustworthy boundary, because a partial model would give a worker a wrong
boundary; opened by the validator, it collects the same problems as findings and keeps going, so a
developer repairs a Spec in one pass. It checks the
[Protocol copy](../../glossary.json#concept.protocol-copy) and nothing else about the installation:
whether the package's built assets are fresh is Distribution's concern, so Spec core depends on
nothing built above it.

**Boundaries and grants.** Selection is one level deep and never reads an implementation file, so a
boundary is a function of declarations. Spec core holds no policy of the Operations built on the
impact indexes, such as which Modules a change may edit or must re-review. The grant computation
sits next to the boundary sets so that an Operation and the Spec MCP server give the same task the
same boundary. A grant is computed from the Specs of the one worktree its caller names, which an
Operation sets to the workspace it runs in, so a
[Spec change](../../glossary.json#concept.spec-change) on the task branch governs that task's
workers and nothing else. A write to a file an unbound Module also binds is refused rather than
silently narrowed: narrowing would leave a worker unable to write a file its own Module binds, with
nothing to tell it why, while the refusal names the file and the Module so the caller can bind the
task to it too or split the work. The context identity covers no implementation contents, so a
worker's writes to code never make its context stale; a task that writes Specs changes its own
context identity. The grant does not yet mark which of its entries are pending, so the Operation
learns which files to create by checking what exists; whether it should is not settled.

**Validation.** The validator runs nothing: it parses verification declarations and reads configured
checks only to confirm their inputs exist and are safe. Concerns other Modules own, such as
[Issue](../../glossary.json#concept.issue) records or Concorde's own package, are their configured
checks, run by Check execution outside `spec-validation`, which keeps it a pure function of the
Specs and the files they bind.

**Shared services.** Registration inverts a dependency that would otherwise point upward: a
record's owner decides its schema, and Spec core stays below every owner. A reference to another
type is resolved by name at check time, so an owner never imports the owner of a type it embeds.
The registration table, the checker, the shared building blocks, strict JSON, the safe-path rules
and the front-matter parser live together because they change together. Initialization, registry
regeneration, pending-entry confirmation and other Modules' deterministic steps all write through
file transactions, so none of them can leave half an update behind.

**Initialization.** Describing a new project is separated from writing it: the proposal is the
preview, and application accepts only that exact proposal while the project is still in the state
it was computed from. The written result is validated inside the transaction, so a first Spec that
does not validate is rolled back. Initialization creates only what the project owns, its
configuration, registry and first Spec; everything that exists because Concorde is installed is
the installer's. So that the project validates at once, the root Module binds every file the
project already has in one realization that says only where the files are, and later Modules take
files over from it.

**Protocol text and assets.** The bundle carries only the Protocol; Concorde's conventions, such as
verification declarations, live in the Modules that own them. Keeping the text apart from its
distributed copy, pinned by each project's Protocol binding, lets a project keep working under the
rules it accepted while a newer Protocol is being written.

**Its place among the Modules.** Spec core uses no Module, so nothing it relies on can make its own
answers wrong; everything else relies on it instead: Spec MCP server, Spec review, Views,
Workers, Check execution, Operations, Tasks, Issues, Distribution and nearly every other Module.

Each consumer declares its own `uses` with the promises it relies on, and none of them is a
dependency of Spec core, so their changes never change what it promises.
