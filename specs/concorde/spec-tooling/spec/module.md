# Spec core

## Purpose

Spec core is Concorde's implementation of the [Spec](../../glossary.json#concept.spec) Protocol and
the deterministic heart of Spec tooling. It loads a project's Specs, checks their structure, and
computes from the declarations alone what a task may read and write and whom a change concerns. It
uses no other [Module](../../glossary.json#concept.module) and never calls a model. It does not
judge whether a Spec explains enough or whether code keeps a promise, does not decide which
[task type](../../glossary.json#concept.task-type) a piece of work gets, and never enforces a grant.

## Core concepts

Spec core's words name what it loads, what it checks, what it computes and what it offers the
Modules above it.

### The loaded Specs

<a id="concept.registry"></a><a id="concept.protocol-binding"></a>

Every program that needs the Specs loads the same things: the configuration
`.concorde/config.json`, the [configured checks](../../glossary.json#concept.configured-check), one
file per Module under `.concorde/checks/`, the **[registry](../../glossary.json#concept.registry)**
`.concorde/specs.json`, the documents each entry registers and the project glossary the root entry
declares, which holds every concept with its owner and one-sentence definition. The registry is the
project-wide index of Modules, and it only mirrors each entry's `module` block: the entry is where
relations are declared. Nothing unregistered is a Spec, a link never adds a document, and a loaded
repository is an immutable snapshot.

The **[Protocol binding](../../glossary.json#concept.protocol-binding)** in the configuration is the
project's acceptance of one installed Protocol copy, by its version and manifest digest. Loading
refuses a binding that disagrees with the installed copy (`protocol_mismatch`), so new rules apply
only after the developer rebinds.

### Structural checks

<a id="concept.structural-check"></a><a id="concept.verification-declaration"></a>

A **[structural check](../../glossary.json#concept.structural-check)** is one decidable rule of the
Protocol or of Concorde's Spec conventions, named by a rule identity such as `CHK.registry.mirror`
and carrying the severity error or warning. `concorde spec-validation` reports every finding in one
run, each with its rule, severity, file and remediation; errors make the result `invalid`. Coverage
comes from **[verification declarations](../../glossary.json#concept.verification-declaration)** in
the tests' own source, which name the scenarios a test verifies and are parsed, never run
([syntax](contracts.md#verification-declarations)). Success is evidence about structure only; see
[What validation tells you](validation.md).

### Boundary sets and impact

<a id="concept.boundary-set"></a><a id="concept.impact-index"></a>

For the Modules a task is bound to, Spec core returns the six
**[boundary sets](../../glossary.json#concept.boundary-set)**: each Module's five, selected one
level deep, and the project-wide ProjectImplementation. A Module's
[Spec context](../../glossary.json#concept.spec-context) also holds its terms: the glossary entries
of the concepts it owns, of the concepts its selected documents link or relate to and of those its
`relies_on` names, closed over the terms those definitions link and their `narrows`, `supersedes`
and `relates` targets, so a reader knows every word its documents use without reading the owners'
documents. The **[impact indexes](../../glossary.json#concept.impact-index)** (`selected-by`,
`referenced-by`, `implemented-by`, `covered-by`, binding Modules, changed definitions) say whom a
change concerns and never widen a boundary. Which Modules a task may edit or must re-review is the
Operations' policy.

### Grants

<a id="concept.grant"></a><a id="concept.context-identity"></a>

A **[grant](../../glossary.json#concept.grant)** says, from one worktree's Specs, which paths a
worker of one task type bound to some Modules may change (`rw`), read (`ro`) or only know by name
(`names`); every other path is denied. A task type that reads code reads the whole project's code,
the Protocol's ProjectImplementation, but writes only within the bound Modules' scopes. The grant
carries the bound Modules' terms, whole glossary entries, and its
**[context identity](../../glossary.json#concept.context-identity)**, so a caller can tell later
whether a Spec source or pinned external material the worker could read has changed; it does not
cover implementation files. The [Operation](../../glossary.json#concept.operation) that launches a
worker freezes the grant into it at launch and the Spec MCP server returns the same computation;
Spec core neither stores nor enforces it.

### Typed values and file transactions

<a id="concept.typed-value"></a><a id="concept.file-transaction"></a>

Every structured value Modules exchange is a
**[typed value](../../glossary.json#concept.typed-value)** `{type_id, schema_version, data}` whose
owner registers its schema ([typed values](contracts.md#typed-values)). A
**[file transaction](../../glossary.json#concept.file-transaction)** writes a set of files
completely or, when a write or its final check fails, restores every file it wrote, each write bound
to the digest it replaces; an interrupted process or a refused restore can leave it partly applied,
and the latter is reported file by file.

## Overview

Spec core is a handful of deterministic parts around one loaded model. What each part reads and
produces:

```d2
model: Spec model
validator: Validator
grants: Grant computation
init: Project initializer
writer: Transaction writer
types: Typed values

registry: Registry
binding: Protocol binding
sets: Boundary set
impact: Impact index
check: Structural check
declaration: Verification declaration
grant: Grant
identity: Context identity
value: Typed value
transaction: File transaction

model -> registry: loads
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
init -> writer: writes through
init -> validator: validates the result with
```

How a change to the Specs reaches a worker: the task level changes a Module's declarations, the
validator reports the registry stale until its mirror is regenerated, and the grant of the next
worker is computed from the changed Specs. [A worked example](#a-worked-example) follows this
path with real output.

```d2 illustrative
direction: down
edit: "Task level: change a\nModule's module block"
validate: "Spec core: load one snapshot,\nrun every structural check"
stale: "Registry mirror\nstale?" {shape: diamond}
regenerate: "Task level:\nconcorde registry --write"
valid: "spec-validation: success"
grant: "Spec core: compute the grant\nfrom the changed Specs"
freeze: "Operation: freeze the grant\ninto its worker" {shape: page}

edit -> validate -> stale
stale -> regenerate: "yes, CHK.registry.mirror"
regenerate -> validate: validate again
stale -> valid: no
valid -> grant: an Operation launches\na worker
grant -> freeze
```

## Entry points

Spec core's entry points are three `concorde` commands, which in the Concorde checkout itself run
as `python3 scripts/concorde.py`, and one function:

- `concorde spec-validation` reports every structural finding of the worktree's Specs in one run.
- `concorde registry --write` regenerates a stale registry mirror (`CHK.registry.mirror`): a task
  may change its own `module` block but never the registry.
- `concorde grant --root <worktree> --modules <ids> --type <task type>` prints the grant the given
  task type receives for the given Modules from that worktree's Specs.
- `initialize(root, package, data)` first proposes the exact first files of a project and their
  digest, then applies exactly that proposal and keeps it only if the project validates; it refuses
  `already_initialized` and `not_installed`. Which command exposes it is Distribution's decision.

### A worked example

A shop project has two Modules under its root, Checkout and Inventory. Checkout's entry
`specs/checkout/module.md` binds the directory `src/checkout/` in its realization Checkout service,
owns the term Hold, which the project glossary `specs/project/glossary.json` defines as "Stock
withheld until an order is accepted or expires.", and relies on Inventory to reserve stock.
Inventory binds `src/inventory/`, and its entry links Hold too, since a reservation places one; a
term only its owner used would draw the warning `CHK.concept.local`. The root binds no files of its
own, and the example leaves out the installer's files. The developer declares Checkout's reliance as
a `uses` in the `module` block of Checkout's entry metadata:

```json
{
  "module": {
    "title": "Checkout",
    "owns": ["specs/checkout/module.md"],
    "contains": [],
    "uses": [{"target": "module.inventory", "meaning": "#uses-module-inventory"}],
    "includes": [],
    "participates": []
  },
  "defines": [
    {"id": "realization.checkout.service", "type": "realization", "title": "Checkout service",
     "meaning": "#realization.checkout.service", "entries": ["src/checkout/"]}
  ]
}
```

`concorde spec-validation` then reports one error, and its status is `invalid`, because the
registry still mirrors Checkout's old `module` block:

```json
{
  "rule_id": "CHK.registry.mirror",
  "severity": "error",
  "source": ".concorde/specs.json",
  "subject_id": "module.checkout",
  "message": "registry record module.checkout differs from its entry's module block in uses",
  "remediation": "Regenerate the registry's mirrored fields with `concorde.py registry --write`."
}
```

`concorde registry --write` regenerates that record (`"regenerated": ["module.checkout"]`), and the
next `spec-validation` is `success` with no finding. A worker is now to change Checkout's code, so
`concorde grant --root . --modules module.checkout --type implement` computes what it may touch and
prints it as its `result`:

```json
{
  "task_type": "implement",
  "modules": ["module.checkout"],
  "context_identity": "sha256:daa066e5aa817d139551eb0de41b1bbadcbbf51d8f798c864a798c38c76380d5",
  "entries": [
    {"path": "specs/checkout/module.md", "level": "ro"},
    {"path": "specs/checkout/module.md.json", "level": "ro"},
    {"path": "specs/inventory/module.md", "level": "ro"},
    {"path": "specs/inventory/module.md.json", "level": "ro"},
    {"path": "src/checkout/", "level": "rw"},
    {"path": "src/inventory/stock.py", "level": "ro"}
  ],
  "terms": [
    {"id": "concept.hold", "title": "Hold", "owner": "module.checkout",
     "definition": "Stock withheld until an order is accepted or expires.",
     "explanation": "specs/checkout/module.md#concept.hold"}
  ],
  "glossary": "specs/project/glossary.json"
}
```

Checkout's own entry and Inventory's entry, which the new `uses` selects, are its Spec context,
readable. Its realization's directory is writable, which covers `src/checkout/submit.py` without an
entry of its own. Inventory's code is readable because a task that implements reads the whole
project's code, and the root Module's entry is absent because nothing Checkout declares selects it.
The glossary is named but not writable, since this task type writes no Spec; the definition of Hold
travels in `terms` instead. Every other path, such as the registry, is denied. In a real project
the root also binds the installer's files, such as its skills and `CLAUDE.md`, which the grant
lists as `ro` with the rest of the project's code; the example leaves them out. The context identity
changes when either entry or the definition of Hold changes, never when `src/checkout/submit.py`
does.

## Parts

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
  transactions.
- <a id="realization.spec.typed-values"></a>**Typed values** hold the registration table, the offline
  checker that checks data as JSON Schema does, shared schema building blocks, strict JSON, safe
  paths and the front-matter parser.
- <a id="realization.spec.errors"></a>**Spec tooling errors** are Spec tooling's own error type:
  code, message, location, reason, remediation and causes, as the [error record](errors.md) defines.
  They depend on no other Module.
- <a id="realization.spec.protocol-text"></a><a id="realization.spec.protocol-assets"></a>**Protocol
  text** is the standard itself; **Protocol assets** are the bundle sources and tracked manifest
  from which Distribution renders the installed copy.
- <a id="realization.spec.tests"></a>**Spec tests** exercise all of this on small fixture projects.

## Why it is built this way

### Loading

One loader serves every query, grant and check, so they cannot disagree about who owns a document or
what a relation selects. A link never adds a document, which is what lets every set be enumerated
from declarations alone. Opened for consumers, the loader refuses a project whose structure cannot
support a trustworthy boundary, because a partial model would give a worker a wrong boundary; opened
by the validator, it collects the same problems as findings and keeps going, so a developer repairs a
Spec in one pass. It checks the [Protocol copy](../../glossary.json#concept.protocol-copy) and
nothing else about the installation: whether the package's built assets are fresh is Distribution's
concern, so Spec core depends on nothing built above it.

### Boundaries and grants

Selection is one level deep and never reads an implementation file, so a boundary is a function of
declarations. Spec core holds no policy of the Operations built on the impact indexes, such as which
Modules a change may edit or must re-review. The grant computation sits next to the boundary sets so
that an Operation and the Spec MCP server give the same task the same boundary. A grant is computed
from the Specs of the one worktree its caller names, which an Operation sets to the workspace it
runs in, so a [Spec change](../../glossary.json#concept.spec-change) on the task branch governs that
task's workers and nothing else.

A grant that writes Specs makes the glossary file writable, since a concept is declared there; that
its writes stay within the bound Modules' own entries is checked after the worker, by Workers'
[write audit](../../glossary.json#concept.write-audit). The computation refuses to make writable a
file that an unbound Module also binds, rather than silently narrowing the grant: narrowing would
leave a worker unable to write a file its own Module binds, with nothing to tell it why, while the
refusal names the file and the Module so the caller can bind the task to it too or split the work.
It never makes writable an installed file, one the installation record `.concorde/install.json` lists
as the installer's own: such a file is bound only by its exact path (`CHK.binds.installed`) and
granted at most `ro`, because the installer replaces it on every update and the agents working on
the project are configured by it.

The context identity covers no implementation contents, so a worker's writes to code never make its
context stale; a task that writes Specs changes its own context identity. Every path a grant lists
from a realization exists, since a realization binds only paths that exist: a new file outside the
bound directories is created and bound at the task level before the grant is computed, so the grant
needs no mark for files still to be created.

The computation runs in a fixed order ([definition](contracts.md#grants)), so that the refusal of a
shared file sees every level the task type assigns and an installed file is lowered only after it:

```d2 illustrative
direction: down
input: "Bound Modules, task type,\nSpecs of one worktree"
check: "Check the input"
levels: "Give each path of the boundary sets\nthe task type's level; a path keeps\nits highest (names < ro < rw)"
shared: "Does an rw entry cover a file\nan unbound Module also binds?" {shape: diamond}
installed: "Lower installed files\nfrom rw to ro"
drop: "Drop exact paths a directory entry\nof equal or higher level covers"
identity: "Compute the context identity over the\nSpec sources, terms and pinned\nexternal material"
grant: "Grant: sorted entries, terms,\nglossary path, context identity" {shape: page}
refused: "Refused, no grant:\ninvalid_input, invalid_task_type,\nunknown_module or shared_file" {shape: page}

input -> check -> levels -> shared
shared -> installed: no
installed -> drop -> identity -> grant
check -> refused: invalid input,\ntask type or Module
shared -> refused: yes
```

### Validation

The validator runs nothing: it parses verification declarations and reads configured checks only to
confirm their inputs exist and are safe. Concerns other Modules own, such as
[Issue](../../glossary.json#concept.issue) records or Concorde's own package, are their configured
checks, run by Check execution outside `spec-validation`, which keeps it a pure function of the
Specs and the files they bind.

### Typed values and file transactions

Registration inverts a dependency that would otherwise point upward: a record's owner decides its
schema, and Spec core stays below every owner. A reference to another type is resolved by name at
check time, so an owner never imports the owner of a type it embeds. The registration table, the
checker, the shared building blocks, strict JSON, the safe-path rules and the front-matter parser
live together because they change together. Initialization, registry regeneration and other
Modules' deterministic steps all write through file transactions, so a
failure they observe never leaves half an update behind, and a restore that fails is named instead
of hidden.

### Initialization

Describing a new project is separated from writing it: the proposal is the preview, and application
checks the proposal's shape, its digest and that the project is still in the state it was computed
from; the digest shows the proposal intact, not that propose made it. The written result is
validated inside the transaction, so a first Spec that does not validate is rolled back.
Initialization creates only what the project owns, its configuration, registry and first Spec;
everything that exists because Concorde is installed is the installer's. So that the project
validates at once, the root Module binds every file the project already has in one realization that
says only where the files are, and later Modules take files over from it. The first entry follows
the recommended reading order and invents nothing: after its Purpose, a section says what is not yet
specified, and its Parts section explains the realizations and, once a scaffold adds children, the
children.

Propose and apply are two calls, and apply refuses before it writes anything unless the proposal
is exactly what the project's current state would give ([definition](contracts.md#initialization)):

```d2 illustrative
direction: down
propose: Propose {
  ask: "Name, root Module,\ninterpreter"
  compute: "Compute the configuration,\nregistry, root entry and\nglossary from the project"
  proposal: "Proposal and its digest;\nnothing written" {shape: page}
  ask -> compute -> proposal
}
apply: Apply {
  checks: "Digest, shape, Protocol binding,\nnull before-digests, unchanged\nsource digest, allowed paths"
  write: "Write every file in\none file transaction"
  validate: "Validate the project\ninside the transaction"
  applied: "Applied" {shape: page}
  checks -> write -> validate -> applied: no error
}
refused: "Refused, nothing written:\ninvalid_input, already_initialized,\nnot_installed, invalid_proposal,\nstale_proposal or permission_denied" {shape: page}
rolled: "Every file rolled back" {shape: page}

propose.proposal -> apply.checks: the caller accepts it
propose.ask -> refused: invalid input, configuration\nexists or no Protocol copy
apply.checks -> refused: a check fails
apply.validate -> rolled: an error
```

### Protocol text and assets

The bundle carries only the Protocol; Concorde's conventions, such as verification declarations,
live in the Modules that own them. Keeping the text apart from its distributed copy, pinned by each
project's Protocol binding, lets a project keep working under the rules it accepted while a newer
Protocol is being written.

### Its place among the Modules

Spec core uses no Module, so nothing it relies on can make its own answers wrong; everything else
relies on it instead: Spec MCP server, Spec review, Views, Workers, Check execution, Operations,
Tasks, Issues, Distribution and nearly every other Module. Each consumer declares its own `uses`
with the promises it relies on, and none of them is a dependency of Spec core, so their changes
never change what it promises.
