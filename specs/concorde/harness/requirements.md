# Harness requirements

These precise specifications belong directly to the [Harness Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker profile](module.md#terminology) | Defined in Harness. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Snapshot](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec context](context.md#terminology) | Defined in What information a worker receives. |
| [Task context](context.md#terminology) | Defined in What information a worker receives. |
| [Capsule](module.md#terminology) | Defined in Harness. |
| [Tool gate](module.md#terminology) | Defined in Harness. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Entity](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Scenario](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Registry](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Harness

### req.harness.context-closure-nonempty — Non-empty frozen context closure

The frozen context closure SHALL never be empty even when one kind is empty for the phase.

### req.harness.context-focus-no-trim — Scenario focus never trims context

A scenario focus SHALL change only the question resolve_context answers, never the selected
Module's Spec context membership.

### req.harness.context-file-names-every-phase — File names visible to every phase

Every phase SHALL see the names, owning entity and pending status of the selected Module's
entity-bound files.

### req.harness.context-contents-code-phases-only — File contents limited to code phases

Only the implementation and code-review phases SHALL also receive the contents of the selected
Module's entity-bound files.

### req.harness.context-index-and-grant — Spec context is indexed and granted, never embedded

Every launch SHALL deliver the selected Module's Spec context and the Protocol rule bundle as an
index of the included files plus a read-only grant of exactly those files rather than as document
bodies in the invocation input.

The index is the frozen snapshot; the grant names project-relative paths, Spec documents where they
live and the installed Protocol copy under `.concorde/protocol/`, as byte-identical copies in a
capsule or the verified files in place in a project workspace. An agent opens what its task needs, starting from the reading
entry, and nothing outside the grant is readable. The Protocol fixes only which files are visible;
this index and grant is the Framework's chosen delivery. Task context stays inline: a review's
typed changes carry diffs of the reviewed Module's own files, which add no path to the grant and
replace no granted file. See [Spec context grant](contracts.md#context-spec-context-grant).

### req.harness.context-recheck — Recheck rejects reuse after changes

recheck_context and recheck_discovery_context SHALL reject reuse whenever any admitted input has
changed since resolution.

### req.harness.context-discovery-no-recurse — Discovery never expands via relationships

resolve_discovery_context SHALL NOT follow a dependency or hyperlink to add another Module's
documents to the discovery context.

### req.harness.profile-within-contract — A profile never exceeds its contract

A worker profile SHALL never grant a tool that its contract's effects and workspace kind do not
admit.

### req.harness.permission-no-widen — Effective permissions stay within both grants

Effective permissions SHALL be a subset of both the worker contract's declared effects and the
host's invocation grant.

### req.harness.permission-write-scope — Write authority limited to code-writing invocations

Only a code-writing invocation SHALL receive write authority, and only for the files the selected
Module's own entities list.

### req.harness.permission-no-spec-write — No write authority over Spec or registry

A code-writing invocation SHALL NOT gain authority to write Spec documents, entity declarations or
the registry.

### req.harness.permission-no-retry — No retry with a wider grant

No permission failure SHALL be retried with a wider grant.

### req.harness.check-project-read-only — Checks cannot mutate project files

The configured-check executor SHALL enforce project filesystem read-only access in the operating
system for the check and every descendant throughout execution.

### req.harness.check-fail-closed — Unavailable check isolation fails closed

The configured-check executor SHALL refuse execution when its read-only boundary cannot be enforced.

### req.harness.check-scratch — Checks receive independent external scratch space

Every configured check SHALL receive a fresh host-managed writable temporary directory outside the
project, removed after its process tree has terminated.

### req.harness.worker-gate — Every tool call is gated by the compiled grant

Every tool call of a worker and of its children SHALL be checked against the invocation's compiled
grant before it executes.

The gate is a policy boundary inside the Pi process, not an operating-system sandbox; see
[execution](execution-reference.md#execution-tool-gate).

### req.harness.worker-selection — Each worker runs on its own configured selection

Every worker launch SHALL use the model, thinking level and timeout resolved for that worker, and for
each of its children, from the project operation configuration.

### req.harness.capsule-closed — A capsule grants only its own snapshot

A capsule worker SHALL be granted read access only to its own snapshot and the copies that snapshot
indexes.

### req.harness.process-inputs-closed — Worker processes receive only closed inputs

A worker process SHALL receive only the allowlisted environment, its host-built Pi configuration,
its system prompt and its single typed context message.

### req.harness.execute-no-retry — No automatic retry after execution failure

No execution failure SHALL trigger an automatic retry with the same or wider permissions.

### req.harness.execute-exit-insufficient — Settling alone is not completion

A worker that settles without exactly one valid submitted result SHALL NOT be treated as completed.

### req.harness.delegation-one-level — Delegation stops at declared children

A worker SHALL delegate only to the children its own profile declares, never beyond one level.

### req.harness.worker-single-result — Only the submitted result leaves the worker

Only a worker's single submitted result SHALL leave its process as Concorde data.

### req.harness.typed-canonical — Canonical encoding digests identically

canonical(value) SHALL produce sorted-key, compact, ASCII-escaped JSON with no trailing newline,
so identical values always digest identically.
