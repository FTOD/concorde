# What validation tells you

Validation answers one question: are the project's [Spec](../../glossary.json#concept.spec)
declarations well formed and consistent with each other? This topic explains what the checks look
at, how to read a finding, what Concorde checks in addition to the Protocol, what it deliberately
leaves to [configured checks](../../glossary.json#concept.configured-check), and what a successful
run does and does not mean. The precise obligations are in the [requirements](requirements.md) and
[scenarios](scenarios.md); the result format is in the
[interface definitions](contracts.md#validation-result).

## Check families

The Protocol's Checks chapter (`protocol/checks.md`) lists every check with an identity and a
severity. Validation evaluates all of them. They fall into five families:

| Family | What it catches | Example |
| --- | --- | --- |
| Nodes | Bad identities, missing or unresolved explanations, concept definitions, requirement statements, scenario steps and contract fences | a requirement whose first sentence contains `SHALL` twice |
| Documents | Unpaired or misplaced documents, wrong metadata schema, missing or repeated entry sections | an entry with two `Design` sections |
| Glossary and terms | A malformed or doubly declared glossary, a definition of more than one sentence, two terms with one title, a term link to no entry, a term used without a link (warning) | a link to `#concept.x` that addresses a Module document |
| Relations | Relations at the wrong site, unresolved targets, composition cycles, registry drift, bad bindings, unbound files, name collisions, contract participation | a [Module](../../glossary.json#concept.module) that uses itself, or a file no Module binds |
| Views | Mermaid blocks, checked D2 diagrams outside `module` reading or outside the semantic subset, and checked diagrams whose shapes, nesting or edges assert something undeclared | a Module drawn inside another that does not contain it |
| Reconciliation | A declaration that requires a definition the Module's context does not contain | a `relates` to another Module's realization whose document the Module never selects |

Most families look at one document at a time. Relations and Reconciliation look across the whole
project, because a relation's target, a registry record or a context selection lives elsewhere. The
registry mirror covers every field of a Module's `module` block, its title included.

## Reading a finding

A finding names the rule that failed, for example `CHK.context.reconciled`, its severity, the file
it concerns and, where known, a line, the node identity involved and a remediation. An error means
the Specs are not structurally conformant; the result status is `invalid`. A warning is reported
and does not change the status. `CHK.contains.root`, `CHK.node.explained`, `CHK.term.unlinked` and
`CHK.includes.redundant` are the Protocol's warnings; Concorde adds one, the coverage warning
`CONCORDE-COVERAGE-001`.

Validation reports every finding it can establish in one run. When a document cannot be read at all,
for example because its metadata is not valid JSON, the checks that need it are skipped and the
unreadable document is itself reported, so the rest of the project is still checked. When one test
file cannot be parsed, it is reported and the remaining test files are still scanned. Only a
configuration, registry or [Protocol binding](../../glossary.json#concept.protocol-binding) that
cannot be read at all ends the run early, with a single `CONCORDE-SOURCE-008` error, because without
them nothing else can be located.

## What Concorde checks beyond the Protocol

**Scenario coverage.** Validation parses the Python and TypeScript tests that Modules bind and reads
their [verification declarations](../../glossary.json#concept.verification-declaration), without
importing, compiling or running them. A declaration that names an unknown scenario fails
`CHK.verifies.resolves`. Concorde warns with `CONCORDE-COVERAGE-001` when a scenario has no
declaring test, unless its Module binds no files at all, since such a Module has no tests of its
own. Tests and scenarios are many-to-many: one test may verify scenarios of several Modules, and a
declaration counts wherever its test file is bound, since the file's owner only decides who may
change it. A test file that cannot be parsed,
or a malformed declaration, is a `CONCORDE-COVERAGE-003` error for that file, because its coverage
cannot be known.

**What counts as an unbound file.** `CHK.binds.unbound` looks at every file under version control.
It exempts document members, everything under `.concorde/` (the registry, the configuration and
other control records), generated outputs (everything under `generated/`, build output directories,
and every output that `generated/build-manifest.json` lists), and external material declared with
`includes` of kind `external`, including the vendored material under `references/`.

**Links to definitions.** The Protocol requires a link fragment that names a stable identity to
name a definition in the linked document, but lists no check for it. Concorde checks it: a link
whose fragment begins with `realization.`, `req.`, `scenario.` or `contract.` and that names no
definition, or a definition in another document, is a `CONCORDE-LINK-001` error. A link whose
fragment begins with `concept.` is a term link, which the Protocol's `CHK.term.link` checks
against the glossary, so it never draws `CONCORDE-LINK-001`.

**Configured check inputs.** Every input path a configured check declares must exist as a regular
file or directory reached without symbolic links; a missing or unsafe input is a
`CONCORDE-CHECK-001` error naming the check. Validation reads no input's content and runs no check.

**Pending entries.** A pending entry whose file now exists fails `CHK.binds.pending-subset`. A
caller that decides readiness, such as the
[execution command](../../glossary.json#concept.execution-command) `task-validation`, validates the
Specs as they read with such entries confirmed, without writing them, and lists them as
confirmations; the execution command `delivery`, which may change the Specs, then clears exactly
those markers through a [file transaction](../../glossary.json#concept.file-transaction), so a task
that created a declared file is not blocked by its own progress.

## What validation leaves to configured checks

Some questions about a project are not questions about its Spec declarations, and validation does
not answer them. Whether every [Issue](../../glossary.json#concept.issue) record is readable,
whether Concorde's own package is consistent and whether tests pass are each answered by a
configured check owned by the Module concerned and run by Check execution. Their results enter a
task's evidence next to the validation result, not inside it, so `spec-validation` stays a pure
function of the Specs and the files they bind.

## What success means

A successful run means that these checks passed for the files assessed at the time of the run. The
result carries a digest of the configuration, the registry, the Spec documents, the glossary, the
Protocol binding and the configured-check inputs, so a caller can tell later whether any of those
has changed since. The digest does not cover everything the checks read: the files that Modules
bind, the list of version-controlled files and the tests scanned for verification declarations are
outside it, so findings about bindings, unbound files and scenario coverage can change while the
digest stays the same. A caller that needs those findings current runs validation again. A success
does not mean that a Spec explains enough for its reader, that a scenario is worth having, or that
the code keeps any promise. The result states this explicitly, and no Concorde step treats
structural success as review or test evidence.
