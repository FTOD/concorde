# How Spec core works

This topic explains in more detail how Spec core loads, checks and answers, and why it is built
that way. The [entry](module.md) states what the Module promises and is enough to use it; the exact
calls and formats are in the [interface definitions](contracts.md).

## Loading

Loading reads `.concorde/config.json`, confirms the Protocol binding, reads the registry, and then
reads each Module's entry and every document the entry registers. A Markdown file that no entry
registers is not a document, and a link never adds one; this is what lets every set be enumerated
from declarations alone. A caller that wants to inspect a state it has not written yet can hand the
repository replacement bytes for the registry or for individual documents; after any Spec file
changes on disk, it builds a new repository.

One loader serves queries, grants and checks, so a query and a check cannot disagree about who owns
a document or what a relation selects. It keeps two kinds of failure apart. Opened for consumers,
it refuses a project whose structure cannot support a trustworthy boundary: an unreadable
configuration, registry or document, a mismatched Protocol binding, a broken entry, a document
owned twice or not at all, an unknown relation target or a composition cycle, because a partial
model would give a worker a wrong boundary. Opened by the validator, it collects the same problems
as findings and keeps going, so a developer repairs a Spec in one pass.

Loading checks the Protocol copy and nothing else about the installation. Whether the installed
package's built assets are fresh is Distribution's concern, checked by its own build and package
checks; Spec core never consults it, so it depends on nothing built above it.

## Boundary sets and impact indexes

For a Module M the five boundary sets are:

| Set | What it contains |
| --- | --- |
| Spec context | both members of every document M owns, and of every document selected by M's `contains`, `uses` and `includes` |
| External context | the readable files below M's external inclusions, with one digest per inclusion |
| Implementation context | the names of the files M's realizations bind |
| Spec scope | both members of every document M owns |
| Implementation scope | every file M's realizations cover, including pending entries not yet created |

Selection is one level deep. If Module A uses B and B uses C, A's context contains the B documents
it selects but none of C's. Implementation files are never read to load the Specs or to compute a
set; only their paths are listed.

The impact indexes answer the reverse question. `selected-by` tells which Modules read a document,
`referenced-by` which declarations name a node, `implemented-by` which Modules bind a file, the
binding Modules of a Module which other Modules share its files, and the changed-definition index
which documents and node definitions differ between two revisions. When several Modules bind one
file, the Protocol requires a task that writes it to be bound to every binding Module;
`implemented-by` names them. Which Modules a change may edit and which need a fresh review are
rules of the Operations built on these indexes, so Spec core holds no policy of theirs.

## Grants and context identity

The Protocol fixes, for each task type, the access level of every boundary set of the bound
Modules. Spec core serializes the levels as the grant does: `none` is omitted, `names` stays
`names`, `read` becomes `ro` and `write` becomes `rw`.

| Task type | Spec context | Implementation context | Implementation scope | Spec scope | External context |
| --- | --- | --- | --- | --- | --- |
| `understand` | `ro` | `names` | omitted | omitted | `ro` |
| `specify` | `ro` | `names` | omitted | `rw` | `ro` |
| `implement` | `ro` | `names` | `rw` | omitted | `ro` |
| `test` | `ro` | `names` | `ro` | omitted | `ro` |
| `review-spec` | `ro` | `names` | omitted | omitted | `ro` |
| `review-code` | `ro` | `names` | `ro` | omitted | `ro` |

A grant for several Modules is the union of their rows, and a path that falls into several sets,
of one Module or of several, receives the highest level any of them assigns. So a `specify` grant
for Modules A and B, where A uses B, makes B's documents `rw` even though A's Spec context sees
them only as `ro`. No other rule widens a grant: task material such as a brief or a diff is not a
source, and a file shared with an unbound Module adds nothing.

A grant lists what the worker may reach, never what it may not: a path absent from the list is
denied. Directory realization entries stay directory entries, so an `implement` grant on `src/a/`
also covers a file created below it later, and a pending entry is listed although its file does not
exist yet; the Operation host creates pending files before launch. Implementation context names are
the existing bound files and the pending exact entries, so an `understand` worker learns every file
name without reading any content. A name that a higher-level directory entry already covers is not
listed twice.

Writing a shared file is refused rather than silently narrowed. If an `implement` grant for A would
make writable a file that D also binds, and D is not among the grant's Modules, the computation
fails and names the file and D. The caller then binds the task to D as well, which also gives the
worker D's Spec context, or splits the work. Narrowing the grant instead would leave a worker
unable to write a file its own Module binds, with nothing to tell it why.

A grant is computed from the Specs of exactly one worktree: the root the caller names. The
Operation host names the task worktree, never the primary, so a Spec change made on the task branch
governs that task's workers and nothing else. The grant is a value with no lifetime of its own; it
is frozen when the host writes it into a worker's configuration at launch, and a worker never asks
for or changes its own grant.

The context identity follows the Protocol's Context chapter. For every bound Module it covers each
selected document member with its identity, owner, path, role, exact-byte digest and every relation
that selected it, and each external inclusion with its tree digest. It therefore changes on any
byte change to a selected member, on a change to a selecting declaration, including removing a
redundant inclusion, on an ownership transfer and on a change to pinned external material. It does
not cover implementation file contents: a worker's own writes do not make its context stale.

## Validation

The validator evaluates every Protocol check and Concorde's conventions over one loaded model and
returns one result with a digest of every input it assessed. It parses bound tests for verification
declarations and reads configured checks only to confirm that their inputs exist and are safe; it
runs nothing. Concerns other Modules own, such as the validity of Issue records or of Concorde's own
package, are configured checks of those Modules, run by Check execution outside `validate`, which
keeps `validate` a pure function of the Specs and the files they bind.

## Typed values and registration

Registration inverts a dependency that would otherwise point upward: a record's owner decides its
schema, and Spec core stays below every owner. The registration table, the closed checker, the
shared building blocks (strings, paths, digests, closed objects and arrays), the offline JSON Schema
subset that also checks every canonical contract in a Spec, strict JSON decoding, the safe
project-path rules and the small front-matter parser for instruction files live together because
they change together. A reference to another type by name is resolved at check time, so an owner
never imports the owner of a type it embeds.

## File transactions

The Transaction writer checks every expected digest before writing and again just before each
write, writes each file through a temporary file and an atomic rename, runs the optional final
check, and restores the original bytes if anything fails. Initialization, registry regeneration,
pending-entry confirmation and other Modules' deterministic steps use it, so none of them can leave
half an update behind. A pending entry records a file a task may create; once the file exists it
must leave `pending`, and confirmation rewrites only the affected metadata.

## Initialization

The initializer separates describing a new project from writing it: the proposal is the preview,
and application accepts only that exact proposal, named by its digest, while every destination is
absent and the project is still in the state the proposal was computed from. It proves its
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
Protocol binding pins the manifest. The bundle carries only the Protocol: Concorde's conventions,
such as the verification declarations, live in the Modules that own them. Keeping the text and its
distributed copy apart lets a project keep working under the rules it accepted while a newer
Protocol is being written.

## Open questions

The grant does not mark which of its entries are pending, so the Operation host learns which files
to create by checking what exists; whether the grant should carry that marker is not settled. The
command that exposes initialization to the developer is not settled either.
