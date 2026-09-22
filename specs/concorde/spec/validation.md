# What validation tells you

Validation answers one question: are the project's Spec declarations well formed and consistent
with each other? This topic explains what the checks look at, how to read a finding, what Concorde
checks in addition to the Protocol, and what a successful run does and does not mean. The precise
obligations are in the [requirements](requirements.md) and [scenarios](scenarios.md).

## Check families

The Protocol's Checks chapter (`protocol/checks.md`) lists every check with an identity and
a severity. Validation evaluates all of them. They fall into five families:

| Family | What it catches | Example |
| --- | --- | --- |
| Nodes | Bad identities, missing or unresolved explanations, concept definitions, requirement statements, scenario steps and contract fences | a requirement whose first sentence contains `SHALL` twice |
| Documents | Unpaired or misplaced documents, wrong metadata schema, missing entry sections, malformed Terminology tables | an entry whose `Design` heading comes before `Usage` |
| Relations | Relations at the wrong site, unresolved targets, composition cycles, registry drift, bad bindings, unbound files, name collisions, contract participation | a Module that uses itself, or a file no Module binds |
| Views | Mermaid blocks in reading that are neither checked flowcharts nor marked illustrative, and checked flowcharts that assert something undeclared | an edge drawn from a realization to a Module without a matching `relates` |
| Reconciliation | A declaration that requires a definition the Module's context does not contain | an import row for a concept whose defining document the Module never selects |

Most families look at one document at a time. Relations and Reconciliation look across the whole
project, because a relation's target, a registry record or a context selection lives elsewhere.

## Reading a finding

A finding names the check that failed, for example `CHK.context.reconciled`, its severity, the file
it concerns and, where known, a line, the node identity involved and a remediation. An error means
the Specs are not structurally conformant; the result status is `invalid`. A warning is reported
and does not change the status. `CHK.contains.root`, `CHK.node.explained`, `CHK.imports.owner` and
`CHK.includes.redundant` are the Protocol's warnings.

Validation reports every finding it can establish in one run. When a document cannot be read at
all, for example because its metadata is not valid JSON, the checks that need it are skipped and
the unreadable document is itself reported, so the rest of the project is still checked. Only a
configuration, registry or Protocol binding that cannot be read at all ends the run early, with a
single `CONCORDE-SOURCE-008` error.

## What Concorde checks beyond the Protocol

**Scenario coverage.** Validation parses the Python and TypeScript tests that Modules bind and reads
their verification declarations, without importing, compiling or running them. A declaration that
names an unknown scenario fails `CHK.verifies.resolves`. In addition, Concorde warns with
`CONCORDE-COVERAGE-001` when a scenario has no declaring test, unless its Module binds no files at
all, since such a Module has no tests of its own. It warns with `CONCORDE-COVERAGE-002` when the
declaring test is not bound by the scenario's owner, because the owner's code tasks would not see
that test. A test file that cannot be parsed, or a malformed declaration, is a
`CONCORDE-COVERAGE-003` error, because its coverage cannot be known. The syntax is defined in the
[interface definitions](contracts.md#verification-declarations).

**What counts as an unbound file.** `CHK.binds.unbound` looks at every file under version control.
It exempts document members, everything under `.concorde/` (the registry, the configuration and
other control records), generated outputs (everything under `generated/`, build output directories, and every output
that `generated/build-manifest.json` lists, such as the files under `.pi/agents/` and
`.pi/extensions/`), and external
material declared with `includes` of kind `external`, including the vendored submodules under
`reference/`.

**Links to definitions.** The Protocol requires a link fragment that names a stable identity to
name a definition in the linked document, but lists no check for it. Concorde checks it: a link
whose fragment begins with `concept.`, `realization.`, `req.`, `scenario.` or `contract.` and that
names no definition, or a definition in another document, is a `CONCORDE-LINK-001` error.

**Configured check inputs.** Every input path a configured check declares must exist as a regular
file or directory without symbolic links; a missing or unsafe input is a `CONCORDE-CHECK-001` error
naming the check. Validation reads no input's content and runs no check.

**Pending entries.** A pending entry whose file now exists fails `CHK.binds.pending-subset`. When
the Validation Module validates a candidate, it first removes such entries from `pending` through
a file transaction, so a task that created a declared file is not blocked by its own progress.

**Issue records.** Validation reads every Issue record through the Issue store and reports a record
it cannot read as `CONCORDE-ISSUE-001`.

**Concorde's own package.** In Concorde's source checkout, recognized by its `concorde.json`
package manifest, validation also runs the package checks of the Distribution Module and reports
their findings.

## What success means

A successful run means that these checks passed for the exact files assessed. The result carries a
digest of those inputs, so a caller can tell later whether anything has changed since. It does not
mean that a Spec explains enough for its reader, that a scenario is worth having, or that the code
keeps any promise. The result states this explicitly, and no Concorde step treats structural
success as review or test evidence.
