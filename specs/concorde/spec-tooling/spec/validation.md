# What validation tells you

Validation answers one question: are the project's [Spec](../../glossary.json#concept.spec)
declarations well formed and consistent with each other? This topic explains:

- What the checks look at.
- How to read a finding.
- What Concorde checks in addition to the Protocol.
- What it deliberately leaves to the parts that own other files.
- What a successful run does and does not mean.

The precise obligations are in the [requirements](requirements.md) and
[scenarios](scenarios.md). The result format is in the
[interface definitions](contracts.md#validation-result).

## Check families

The Protocol's Checks chapter (`protocol/checks.md`) lists every check with an identity and a
strictness. Validation evaluates all of them. They fall into seven families:

| Family | What it catches | Example |
| --- | --- | --- |
| Nodes | Bad identities, missing or unresolved explanations, concept definitions, requirement statements, scenario steps and contract fences | a requirement whose first sentence contains `SHALL` twice |
| Documents | Unpaired or misplaced documents, wrong metadata schema, a Module without exactly one entry; never how an entry is organized, since the Protocol requires no section | a Module that owns two `module`-role `module.md` documents |
| Glossary and terms | A malformed or doubly declared glossary, a definition of more than one sentence, two terms with one title, a term link to no entry, a term used without a link (warning) | a link to `#concept.x` that addresses a Module document |
| Relations | Relations at the wrong site, unresolved targets, composition cycles, registry drift, bad bindings, unbound files, name collisions, contract participation | a [Module](../../glossary.json#concept.module) that uses itself, or a file no Module binds |
| Views | Mermaid blocks, checked D2 diagrams outside `module` reading or outside the semantic subset, and checked diagrams whose shapes, nesting or edges assert something undeclared | a Module drawn inside another that does not contain it |
| Reconciliation | A declaration that requires a definition the Module's context does not contain | a `relates` to another Module's realization whose document the Module never selects |
| Style | A sentence of a document's reading with more than 35 words, a concept definition with more than 50 words, a semicolon in prose or a sentence with more than one requirement keyword, in a document's reading or a concept definition (warnings) | a requirement that joins three conditions with semicolons |

The style checks measure the Protocol's *Sentence style* (`protocol/style.md`) in the prose of
every document and in every concept definition. They see the prose as a reader sees it. They leave
out:

- Fences are left out.
- Headings are left out.
- Tables are left out.
- Front matter is left out.
- HTML anchors are left out.

A link counts as its text. An inline code span counts as one word. Each paragraph and each list
item is split into sentences by the sentence-break rule that `CHK.concept.definition` uses.

Most families look at one document at a time. A relation's target, a registry record or a context
selection lives elsewhere. Therefore, Relations and Reconciliation look across the whole project.
The registry mirror covers every field of a Module's `module` block, its title included.

## Reading a finding

A finding names:

- The rule that failed, for example `CHK.context.reconciled`.
- Its strictness.
- The file it concerns.
- Where known, a line.
- Where known, the node identity involved.
- Where known, a remediation.

An error means the Specs are not structurally conformant. With an error, the result status is
`invalid`.
A warning is reported and does not change the status. The Protocol's warnings are `CHK.contains.root`,
`CHK.node.explained`, `CHK.term.unlinked`, `CHK.concept.local`, `CHK.includes.redundant` and the
three style checks. Concorde adds one, the coverage warning `CONCORDE-COVERAGE-001`.

Validation reports every finding it can establish in one run. When a document cannot be read at all,
for example because its metadata is not valid JSON:

- The checks that need it are skipped.
- The unreadable document is itself reported.
- The rest of the project is still checked.

When one test file cannot be parsed, it is reported and the remaining test files are still scanned.
Only in these cases does the run end early, with a single `CONCORDE-SOURCE-008` error:

- A configuration cannot be read at all.
- A registry cannot be read at all.
- A [Protocol binding](../../glossary.json#concept.protocol-binding) cannot be read at all.

Without them nothing else can be located.

## What Concorde checks beyond the Protocol

**Scenario coverage.** Validation parses the Python and TypeScript tests that Modules bind.
It reads their [verification declarations](../../glossary.json#concept.verification-declaration)
without importing, compiling or running the tests. A declaration that names an unknown
scenario fails `CHK.verifies.resolves`. Unless its Module binds no files at all, Concorde warns with
`CONCORDE-COVERAGE-001` when a scenario has no declaring test. A Module that binds no files has no
tests of its own. Tests and scenarios are many-to-many: one test may verify scenarios of several
Modules. Since the file's owner only decides who may change it, a declaration counts wherever its
test file is bound. When a test file cannot be parsed or a declaration is malformed, its coverage
cannot be known. This is a `CONCORDE-COVERAGE-003` error for that file.

**What counts as an unbound file.** `CHK.binds.unbound` looks at every file under version control.
It exempts:

- Document members.
- Everything under `.concorde/` (the registry, the configuration and other control records).
- Generated outputs: everything under `generated/`.
- Generated outputs: build output directories.
- Generated outputs: every output that
  [`generated/build-manifest.json`](../../distribution/contracts.md#contract.distribution.build-manifest)
  lists.
- External material declared with `includes` of kind `external`, including the vendored material
  under `references/`.

**Links to definitions.** The Protocol requires a link fragment that names a stable identity to
name a definition in the linked document. The Protocol lists no check for it. When a link's
fragment begins with `realization.`, `req.`, `scenario.` or `contract.` and names no definition or
a definition in another document, Concorde reports a `CONCORDE-LINK-001` error.

A link whose fragment begins with `concept.` is a term link. The Protocol's `CHK.term.link` checks
it against the glossary, so it never draws `CONCORDE-LINK-001`.

**Realization entries.** Every entry must exist (`CHK.binds.exists`): a realization records what
exists, never an intent. A realization record that still carries Protocol 15's `pending` field
fails `CHK.document.schema`, with no migration of its own. The Protocol's migration notes say how
to remove it.

## What validation leaves to other parts

Some questions about a project are not questions about its Spec declarations. Validation does not
answer them:

- Whether every [Issue](../../glossary.json#concept.issue) record is readable is the issues part's
  own check.
- Whether every [configured check](../../glossary.json#concept.configured-check) is well formed
  and its inputs exist is Check execution's check, in the execution part.
- Whether Concorde's own package is consistent and whether tests pass are configured checks. The
  Module concerned owns them, and Check execution runs them.

Their results enter a task's evidence next to the validation result, not inside it.
Therefore, `spec-validation` stays a pure function of the Specs and the files they bind.

The spec part reads no file format of another part except two of Distribution's.
Distribution is the installation host present in every installation. The spec part reads each
file only when it is present. For the installation record `.concorde/install.json`, a Module binds
its installed files by their exact paths (`CHK.binds.installed`). The spec part reads the
[build manifest](../../glossary.json#concept.build-manifest) `generated/build-manifest.json` in the
shape of its [contract](../../distribution/contracts.md#contract.distribution.build-manifest).
Its listed outputs are exempt from `CHK.binds.unbound`.

Without an installation record no file counts as installed. Without a build manifest only the
other generated outputs are exempt. Neither absence is a finding.

## What success means

A successful run means that these checks passed for the files assessed at the time of the run.
So that a caller can tell later whether any changed since the run, the result carries a digest of:

- The configuration.
- The registry.
- The Spec documents.
- The glossary.
- The Protocol binding.

The digest does not cover everything the checks read. These inputs are outside it:

- The files that Modules bind.
- The list of version-controlled files.
- The tests scanned for verification declarations.

Therefore, findings about bindings, unbound files and scenario coverage can change while the
digest stays the same. A caller that needs those findings current runs validation again.
A success does not mean:

- That a Spec explains enough for its reader.
- That a scenario is worth having.
- That the code keeps any promise.

The result states this explicitly. No Concorde step treats structural success as review or test
evidence.
