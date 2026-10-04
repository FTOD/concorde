# Spec core

## Purpose

Spec core is Concorde's implementation of the [Spec](../../glossary.json#concept.spec) Protocol and
the deterministic heart of Spec tooling. Spec core does the following:

- It loads a project's Specs.
- It checks their structure.
- From the declarations alone, it computes the following:
  - What a task may read.
  - What a task may write.
  - Whom a change concerns.

Spec core has these limits:

- It uses no other [Module](../../glossary.json#concept.module).
- It depends on no other part.
- It never calls a model.
- It does not judge whether a Spec explains enough or whether code keeps a promise.
- It does not decide which [task type](../../glossary.json#concept.task-type) a piece of work gets.
- It never enforces a grant.

## Core concepts

Spec core's words name the following:

- What it loads.
- What it checks.
- What it computes.
- What it offers the Modules above it.

### The loaded Specs

<a id="concept.registry"></a><a id="concept.protocol-binding"></a>

Every program that needs the Specs loads the same things:

- The configuration `.concorde/config.json`.
- The **[registry](../../glossary.json#concept.registry)** `.concorde/specs.json`.
- The documents each entry registers.
- The project glossary the root entry declares.

The glossary holds every concept with its owner and one-sentence definition. The registry is the
project-wide index of Modules. The registry only mirrors each entry's `module` block. The entry is
where relations are declared. Nothing unregistered is a Spec. A link never adds a document. A loaded
repository is an immutable snapshot.

The **[Protocol binding](../../glossary.json#concept.protocol-binding)** in the configuration is the
project's acceptance of one installed Protocol copy, by its version and manifest digest.
When a binding disagrees with the installed copy, loading refuses it (`protocol_mismatch`).
Only after the developer rebinds do new rules apply.

### Structural checks

<a id="concept.structural-check"></a><a id="concept.verification-declaration"></a>

A **[structural check](../../glossary.json#concept.structural-check)** is one decidable rule of the
Protocol or of Concorde's Spec conventions. A rule identity such as `CHK.registry.mirror` names it.
The check carries the strictness error or warning. `concorde spec-validation` reports every finding
in one run. Each finding carries its rule, strictness, file and remediation. Errors make the result
`invalid`. Coverage comes from
**[verification declarations](../../glossary.json#concept.verification-declaration)** in the tests'
own source. They name the scenarios a test verifies and are parsed, never run
([syntax](contracts.md#verification-declarations)). Success is evidence about structure only. See
[What validation tells you](validation.md).

### Boundary sets and impact

<a id="concept.boundary-set"></a><a id="concept.impact-index"></a>

For the Modules a task is bound to, Spec core returns the seven
**[boundary sets](../../glossary.json#concept.boundary-set)**:

- Each Module's five, selected one level deep.
- The project-wide ProjectImplementation, every file any Module binds.
- The project-wide ProjectSpecification, every Module's documents with the glossary.

A Module's [Spec context](../../glossary.json#concept.spec-context) also holds its terms. These are
the glossary entries of the following concepts:

- The concepts it owns.
- The concepts its selected documents link or relate to.
- The concepts its `relies_on` names.

These entries are closed over the terms those definitions link and their `narrows`, `supersedes`
and `relates` targets. Thus, a reader knows every word its documents use without reading the owners'
documents. The **[impact indexes](../../glossary.json#concept.impact-index)** say whom a change
concerns. The indexes are `selected-by`, `referenced-by`, `implemented-by`, `covered-by`, binding
Modules and changed definitions.

The impact indexes never widen a boundary. Which Modules a task may edit
or must re-review is the Operations' policy.

### Grants

<a id="concept.grant"></a><a id="concept.context-identity"></a>

From one worktree's Specs, a **[grant](../../glossary.json#concept.grant)** specifies path access for a
worker of one task type bound to some Modules:

- Paths it may change (`rw`).
- Paths it may read (`ro`).
- Paths it may only know by name (`names`).

Every other path is denied. A task type that reads code reads the whole project's code,
the Protocol's ProjectImplementation. Such a task type writes only within the bound Modules' scopes.

`review-architecture` reads every Module's Specs, the Protocol's ProjectSpecification.
`review-architecture` knows the project's code only by name. The grant carries the bound Modules'
terms as whole glossary entries. The grant also carries its
**[context identity](../../glossary.json#concept.context-identity)**.
The identity lets a caller detect later changes to a Spec source or pinned external material the
worker could read. The context identity does not cover implementation files. The
[Operation](../../glossary.json#concept.operation) that launches a worker freezes the grant into it
at launch. The Spec MCP server returns the same computation. Spec core does not store it.
Spec core does not enforce it.

### Its own data utilities

The records Spec core reads and writes are [typed values](../../glossary.json#concept.typed-value)
`{type_id, schema_version, data}`. Every write it makes, such as initialization or a registry
regeneration, is a [file transaction](../../glossary.json#concept.file-transaction). Both formats are
the Kernel's ([typed values](../../kernel/contracts.md#typed-values),
[file transactions](../../kernel/contracts.md#file-transactions)). Spec core does not use the
Kernel's code. Spec core keeps its own copy of these utilities, schema checking and digests.

Spec core uses its own error types with the copy ([its interface](contracts.md#typed-values)). This lets the spec
part install and work with no other part. The Spec MCP server and Views use the same copy.

## Overview

Spec core is a handful of deterministic parts around one loaded model. What each part reads and
produces:

```d2
model: Spec model
validator: Validator
grants: Grant computation
init: Project initializer
writer: Transaction writer

registry: Registry
binding: Protocol binding
sets: Boundary set
impact: Impact index
check: Structural check
declaration: Verification declaration
grant: Grant
identity: Context identity

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
init -> writer: writes through
init -> validator: validates the result with
```

How a change to the Specs reaches a worker:

- The task level changes a Module's declarations.
- Until its mirror is regenerated, the validator reports the registry stale.
- The grant of the next worker is computed from the changed Specs.

[A worked example](#a-worked-example) follows this path with real output.

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

Spec core's entry points are three `concorde` commands and one function.
In the Concorde checkout itself, the commands run as `python3 scripts/concorde.py`.
The entry points are:

- `concorde spec-validation` reports every structural finding of the worktree's Specs in one run.
- `concorde registry --write` regenerates a stale registry mirror (`CHK.registry.mirror`). A task
  may change its own `module` block but never the registry.
- `concorde grant --root <worktree> --modules <ids> --type <task type>` prints the grant the given
  task type receives for the given Modules from that worktree's Specs.
- `initialize(root, package, data)` first proposes the exact first files of a project and their
  digest. The function then applies exactly that proposal. Only if the project validates does the
  function keep it. The function refuses `already_initialized` and `not_installed`.
  The spec part registers `concorde init`, which exposes the function. Installing the spec part never
  runs it. The developer runs `init --propose` and then `init --apply`
  ([Distribution](../../distribution/module.md#after-installing)).

### A worked example

A shop project has two Modules under its root, Checkout and Inventory. Checkout's entry
`specs/checkout/module.md` declares the following:

- It binds the directory `src/checkout/` in its realization Checkout service.
- It owns the term Hold.
- It relies on Inventory to reserve stock.

The project glossary `specs/project/glossary.json` defines Hold as "Stock withheld until an order
is accepted or expires." Inventory binds `src/inventory/`. Since a reservation places a Hold,
Inventory's entry links Hold too. If only its owner used a term, the term would draw the warning
`CHK.concept.local`. The root binds no files of its own. The example leaves out the installer's
files. The developer declares Checkout's reliance as a `uses` in the `module` block of Checkout's
entry metadata:

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

Because the registry still mirrors Checkout's old `module` block, `concorde spec-validation`
then reports one error in a result with status `invalid`:

```json
{
  "rule_id": "CHK.registry.mirror",
  "strictness": "error",
  "source": ".concorde/specs.json",
  "subject_id": "module.checkout",
  "message": "registry record module.checkout differs from its entry's module block in uses",
  "remediation": "Regenerate the registry's mirrored fields with `concorde.py registry --write`."
}
```

`concorde registry --write` regenerates that record (`"regenerated": ["module.checkout"]`). The
next `spec-validation` is `success` with no finding. A worker is now to change Checkout's code.
`concorde grant --root . --modules module.checkout --type implement` computes what it may touch.
The command prints this as its `result`:

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

The new `uses` selects Inventory's entry. Checkout's own entry and Inventory's entry are its
readable Spec context. Its realization's directory is writable. This covers
`src/checkout/submit.py` without an entry of its own. Because a task that implements reads the
whole project's code, Inventory's code is readable. Because nothing Checkout declares selects
the root Module's entry, that entry is absent. Since this task type writes no Spec, the glossary
is named but not writable. The definition of Hold travels in `terms` instead.

Every other path, such as the registry, is denied. In a real project, the root also binds the
installer's files, such as its skills and `CLAUDE.md`. The grant lists those files as `ro` with the
rest of the project's code.

The example leaves them out. When either entry or the definition of Hold changes, the context
identity changes. When `src/checkout/submit.py` changes, the context identity never changes.

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

- <a id="realization.spec.model"></a>**Spec model** loads the registry and documents.
  It computes every set and index from declarations alone, never reading implementation contents.
- <a id="realization.spec.validator"></a>**Validator** does the following:
  - It evaluates every check over one loaded model.
  - It reads verification declarations without running anything.
  - It regenerates the registry mirror.
- <a id="realization.spec.grants"></a>**[Grant](../../glossary.json#concept.grant) computation**
  does the following:
  - It applies a task type to the bound Modules'
    [boundary sets](../../glossary.json#concept.boundary-set).
  - It computes the context identity.
  - It refuses unbound shared writes.
- <a id="realization.spec.initializer"></a>**Project initializer** does the following:
  - It proposes the first Spec of a project.
  - It applies that first Spec.
  - It keeps an installed project's files bound.

  The spec part's commands and install services that call it also call Views and the Spec MCP server.
  For that reason, they are its parent's [part entries](../module.md#realization.spec-tooling.part).
- <a id="realization.spec.transactions"></a>**Transaction writer** is Spec core's own copy of
  digest-bound file transactions.
- <a id="realization.spec.typed-values"></a>**Typed values** are Spec core's own copy of the
  registration table and the offline checker. The offline checker checks data as JSON Schema does.
  The copy includes shared schema building blocks, strict JSON, safe paths and the front-matter
  parser.
- <a id="realization.spec.errors"></a>**Spec tooling errors** are Spec tooling's own error type:
  code, message, location, reason, remediation and causes, as the [error record](errors.md) defines.
  They depend on no other Module.
- <a id="realization.spec.protocol-text"></a><a id="realization.spec.protocol-assets"></a>**Protocol
  text** is the standard itself. **Protocol assets** are the bundle sources and tracked manifest
  from which Distribution renders the installed copy.
- <a id="realization.spec.tests"></a>**Spec tests** exercise all of this on small fixture projects.

## Why it is built this way

### Loading

One loader serves every query, grant and check. Thus, they cannot disagree about who owns a
document or what a relation selects. A link never adds a document. This lets every set be
enumerated from declarations alone. When opened for consumers, the loader refuses a project
whose structure cannot support a trustworthy boundary. A partial model would give a worker a
wrong boundary. When opened by the validator, the loader collects the same problems as findings
and keeps going.

Thus, a developer repairs a Spec in one pass. The loader checks the
[Protocol copy](../../glossary.json#concept.protocol-copy) and nothing else about the installation.
Whether the package's built assets are fresh is Distribution's concern. Thus, Spec core depends
on nothing built above it.

### Boundaries and grants

Selection is one level deep. Selection never reads an implementation file. Thus, a boundary is a
function of declarations. Spec core holds no policy of the Operations built on the impact indexes,
such as which Modules a change may edit or must re-review. The grant computation sits next to the
boundary sets. This lets an Operation and the Spec MCP server give the same task the same boundary.
A grant is computed from the Specs of the one worktree its caller names. An Operation sets that
worktree to the workspace it runs in. Thus, a [Spec change](../../glossary.json#concept.spec-change)
on the task branch governs that task's workers and nothing else.

Since a concept is declared in the glossary file, a grant that writes Specs makes that file
writable. After each round, the glossary ownership audit of the Method step that launched the
worker checks that the grant's writes stay within the bound Modules' own entries.
The audit runs beside the worker harness's [write audit](../../glossary.json#concept.write-audit).

When an unbound Module also binds a file, the computation refuses to make that file writable
instead of silently narrowing the grant.
Narrowing would leave a worker unable to write a file its own Module binds, with nothing to tell
it why. The refusal names the file and the Module. This lets the caller bind the task to that
Module too or split the work. An installed file is one the installation record
`.concorde/install.json` lists as the installer's own. For an installed file:

- The computation never makes it writable.
- The file is bound only by its exact path (`CHK.binds.installed`).
- The file is granted at most `ro`.
- The installer replaces it on every update.
- The file configures the agents working on the project.

The replacement and configuration explain the access restriction.

The context identity covers no implementation contents. Thus, a worker's writes to code never
make its context stale. A task that writes Specs changes its own context identity.
Since a `review-architecture` worker judges every Module's Specs, its grant's identity also covers
every file of ProjectSpecification. Thus, a change to any of them makes its judgment stale.
Since a realization binds only paths that exist, every path a grant lists from a realization exists.
For a new file outside the bound directories, creation and binding occur at the task level before
the grant is computed. Thus, the grant needs no mark for files still to be created.

The computation runs in a fixed order ([definition](contracts.md#grants)). This lets the refusal
of a shared file see every level the task type assigns. An installed file is lowered only after
that refusal.

```d2 illustrative
direction: down
input: "Bound Modules, task type,\nSpecs of one worktree"
check: "Check the input"
levels: "Give each path of the boundary sets\nthe task type's level; a path keeps\nits highest (names < ro < rw)"
shared: "Does an rw entry cover a file\nan unbound Module also binds?" {shape: diamond}
installed: "Lower installed files\nfrom rw to ro"
drop: "Drop exact paths a directory entry\nof equal or higher level covers"
identity: "Compute the context identity over the\nSpec sources, terms and pinned\nexternal material (and every\nModule's Specs for review-architecture)"
grant: "Grant: sorted entries, terms,\nglossary path, context identity" {shape: page}
refused: "Refused, no grant:\ninvalid_input, invalid_task_type,\nunknown_module or shared_file" {shape: page}

input -> check -> levels -> shared
shared -> installed: no
installed -> drop -> identity -> grant
check -> refused: invalid input,\ntask type or Module
shared -> refused: yes
```

### Validation

<a id="uses-distribution"></a>

The validator runs nothing. The validator parses verification declarations. The validator reads
nothing a check would run. Outside `spec-validation`, the owning parts check concerns other Modules
own, such as:

- [Issue](../../glossary.json#concept.issue) records.
- [configured checks](../../glossary.json#concept.configured-check) and their inputs.
- Concorde's own package.

This keeps `spec-validation` a pure function of the Specs and the files they bind. The spec part
stays free of every other part's file formats except two of Distribution's formats.
When present, Spec core reads those Distribution records
([What validation leaves to other parts](validation.md#what-validation-leaves-to-other-parts)).

### A private copy of the data utilities

<a id="uses-kernel"></a>

Typed values and file transactions are the Kernel's formats. The other parts share them through
the Kernel's code. Because the spec part must install and work with nothing else, Spec core keeps
a copy of its own instead. A Spec tooling that imported the Kernel could not be used alone.
The few hundred lines Spec core duplicates change rarely. The copy follows the Kernel's formats
exactly. Thus, a value or a transaction means the same on both sides. The copy raises Spec tooling's
own errors. Registration lets each record's owner decide its schema. The checker stays below
every owner. At check time, a reference to another type is resolved by name. Initialization and
registry regeneration write through file transactions. Thus, a failure they observe never leaves
half an update behind. When a restore fails, it is named instead of hidden.

### Initialization

Describing a new project is separated from writing it. The proposal is the preview. Application
performs these checks:

- It checks the proposal's shape.
- It checks the proposal's digest.
- It checks that the project is still in the state from which the proposal was computed.

The digest shows the proposal intact, not that propose made it. The written result is validated
inside the transaction. If a first Spec does not validate, it is rolled back.
Initialization creates only what the project owns: its configuration, registry and first Spec.

Everything that exists because Concorde is installed is the installer's. So that the project
validates at once, the root Module binds every file the project already has in one realization.
That realization says only where the files are. Later Modules take files over from the root Module.
The first entry follows the recommended reading order. The entry invents nothing. After its
`Purpose`, a section says what is not yet specified. Its `Parts` section explains the realizations.
Once a scaffold adds children, that section also explains the children.

Propose and apply are two calls. Unless the proposal is exactly what the project's current state
would give, apply refuses before it writes anything ([definition](contracts.md#initialization)):

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

The bundle carries only the Protocol. Concorde's conventions, such as verification declarations,
live in the Modules that own them. Each project's Protocol binding pins the distributed copy.
While a newer Protocol is written, keeping the text apart from that copy lets a project keep
working under the rules it accepted.

### Its place among the Modules

Spec core imports no other Module's code. It needs no other part installed. Thus, no other part's
code can make Spec core's answers wrong. Its two `uses` are reliances on formats alone: the Kernel's
[typed values](../../glossary.json#concept.typed-value) and
[file transactions](../../glossary.json#concept.file-transaction), and the two records of Distribution.
Spec core's own copy follows the Kernel's formats.
When the records are present, Spec core reads the two records of Distribution.

Every Module that reads Specs relies on Spec core instead:

- The Spec MCP server and Views in its own part.
- Method, whose Operations and commands compute their grants and readiness through Spec core.
- The [optional integrations](../../glossary.json#concept.optional-integration) of Coordination
  and Issues. Only where the spec part is installed do they check a Module identity against the
  registry.

Each consumer declares its own `uses` with the promises it relies on. None of them is a dependency
of Spec core. Thus, their changes never change what it promises. Spec core's install contribution
is the Protocol copy, the Protocol binding and `concorde init`.
The contribution reaches a project through the spec part's registration with Distribution.
