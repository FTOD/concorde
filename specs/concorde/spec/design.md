# How Spec tooling works

This topic explains in more detail how Spec tooling loads, checks and answers, and why it is built
that way. The [entry](module.md) states what the Module promises and is enough to use it; the exact
calls and formats are in the [interface definitions](contracts.md).

## Loading

Loading reads `.concorde/config.json`, confirms the Protocol binding, reads the registry, and then
reads each Module's entry and every document the entry registers. A Markdown file that no entry
registers is not a document, and a link never adds one; this is what lets every set be enumerated
from declarations alone. A caller that wants to inspect a candidate state without writing it can
hand the repository replacement bytes for the registry or for individual documents; after any
Spec file changes on disk, it builds a new repository.

One loader serves queries and checks, so a query and a check cannot disagree about who owns a
document or what a relation selects. It keeps two kinds of failure apart. Opened for consumers, it
refuses a project whose structure cannot support a trustworthy boundary: an unreadable
configuration, registry or document, a mismatched Protocol binding, a broken entry, a document
owned twice or not at all, an unknown relation target or a composition cycle, because a partial
model would give a harness a wrong boundary. Opened by the validator, it collects the same problems
as findings and keeps going, so a developer repairs a Spec in one pass.

Loading checks the Protocol copy and nothing else about the installation. Whether the installed
package's built assets are fresh is Distribution's concern, checked by its own build and package
checks; Spec tooling never consults it, so it depends on nothing built above it.

## Boundary sets and impact indexes

For a Module M the five boundary sets are:

| Set | What it contains |
| --- | --- |
| Spec context | both members of every document M owns, and of every document selected by M's `contains`, `uses` and `includes` |
| External context | the readable files below M's external inclusions, with one digest per inclusion |
| Implementation context | the names of the files M's realizations bind |
| Spec scope | both members of every document M owns |
| Implementation scope | every file M's realizations cover, including pending entries not yet created |

Selection is one level deep. If Planning uses Review and Review uses Agents, Planning's context
contains the Review documents it selects but none of Agents'. Implementation files are never read
to load the Specs or to compute a set; only their paths are listed.

The impact indexes answer the reverse question. `selected-by` tells which Modules read a document,
`referenced-by` which declarations name a node, `implemented-by` which Modules bind a file, the
binding Modules of a Module which other Modules share its files, and the changed-definition index
which documents and node definitions differ between two revisions. When several Modules bind one
file, the Protocol requires a task that writes it to be bound to every binding Module;
`implemented-by` names them and the caller decides what the task receives. Which Modules a change
may edit, which need a fresh review and which a candidate edited are rules of Planning, Review and
Validation, built on these indexes, so Spec tooling holds no policy of theirs.

## Validation

The validator evaluates every Protocol check and Concorde's conventions over one loaded model and
returns one result with a digest of every input it assessed. It parses bound tests for verification
declarations and reads configured checks only to confirm that their inputs exist and are safe; it
runs nothing. Concerns other Modules own, such as the validity of Issue records or of Concorde's own
package, are configured checks of those Modules and reach a candidate's evidence through Check
execution, which keeps `validate` a pure function of the Specs and the files they bind.

## Typed values and registration

Registration inverts a dependency that would otherwise point upward: a record's owner decides its
schema, and Spec tooling stays below every owner. The registration table, the closed checker, the
shared building blocks (strings, paths, digests, closed objects and arrays), the offline JSON Schema
subset that also checks every canonical contract in a Spec, strict JSON decoding, the safe
project-path rules and the small front-matter parser for instruction files live together because
they change together. A reference to another type by name is resolved at check time, so an owner
never imports the owner of a type it embeds.

## File transactions

The Transaction writer checks every expected digest before writing and again just before each
write, writes each file through a temporary file and an atomic rename, runs the optional final
check, and restores the original bytes if anything fails. Initialization, registry regeneration,
pending-entry confirmation, configuration changes and several Host steps of other Modules use it,
so none of them can leave half an update behind. A pending entry records a file a task may create;
once the file exists it must leave `pending`, and confirmation rewrites only the affected metadata.

## Initialization

The initializer separates describing a new project from writing it: the proposal is the preview,
and application accepts only that exact proposal while every destination is absent. It proves its
result by running the validator on the written files inside the transaction, so a first Spec that
does not validate is rolled back. Initialization creates only what the project owns, its
configuration, registry and first Spec; the Protocol copy and everything else that exists because
Concorde is installed is the installer's output. The first Spec invents no concepts, requirements,
scenarios or relations. So that the project validates at once, the root Module binds every file the
project already has, tracked or untracked but not ignored, in one realization that says only where
the files are; later Modules take files over from it.

## Protocol text and assets

The Protocol text under `protocol/` holds the chapters, templates and the machine-readable
vocabulary `model.yaml`. The Protocol assets are the bundle sources and the tracked manifest.
Distribution's build renders the bundle and its installer copies it into each project, where the
Protocol binding pins the manifest. The bundle carries only the Protocol: Concorde's conventions
live in the Modules that own them, such as the verification declarations here and the Graph Spec
convention in Agent execution. Keeping the text and its distributed copy apart lets a project keep
working under the rules it accepted while a newer Protocol is being written.

## Transitional files

The catalog module and the capability-specific shapes among the typed values move to their owners,
which register them. The change-scope, review-impact and edited-Module policies in the impact code
move to Planning, Review and Validation. The configure service that shares the initializer's code
moves to Request admission, which owns `concorde-configure`.

## Open questions

The `concorde-init` declaration follows the Operation catalog's format, which Operations defines,
although Spec tooling uses no other Module; how an infrastructure Module declares a capability
without depending on the catalog is not settled. The worker configuration carried by an initial
proposal is a typed value whose type Request admission registers; Spec tooling stores it unchanged
without checking its schema itself.
