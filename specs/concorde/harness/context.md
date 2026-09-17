# Context resolution

This document defines the four kinds of context a Harness freezes for one invocation and the
host-internal interface that resolves them. The Spec Protocol defines Spec context and
implementation context; this Module realizes those definitions and adds the two Framework kinds.

### Context kinds

| Kind | Content | Required for |
| --- | --- | --- |
| Spec context | The selected Module's complete resolved document-unit context (reading plus metadata), exactly the Protocol's `Context(M)`; a scenario focus changes the question, not the membership. The Protocol fixes only this visible set; the Framework delivers it as a context index and grant: the snapshot lists every document with identity, owner, digest, inclusion reasons and the reading entry, and the documents are granted read-only at their project-relative paths, byte-identical copies in a capsule. No document body is embedded. | Every Module-bound invocation. |
| Implementation context | The Protocol's `ImplementationContext(M)`: the listing entries the selected Module's own entities declare, exact files and directory prefixes alike, and the files those entries currently bind. Every phase can see the declared entries and bound file names with their owning entity and pending status; only code-writing and code-review phases receive file contents, in their declared subsets. | Entries and file names: every phase. File contents: code-writing and code-review phases only. |
| Capability context | The contracts of the Capabilities and Tools the invocation may use, as admitted by its Harness and constraints, together with the Module's Protocol-defined external references: the vendored documentation and source it declares with `references` of kind `external`, one tree digest per entry. Descriptions given to the model and bindings accepted by the executor resolve to the same contracts. | Reference entries and digests: every phase. Reference contents, read-only: the modes that declare the `references` effect (plan, tasks, implementation, code-review). Capability and Tool contracts: none admitted by any current Agent. |
| Task context | The task and constraints, the stage artifacts admitted for this phase, such as a plan, implementation tasks, a review result or an Issue selection, and the frozen workspace lifecycle metadata. Task context travels inline in the invocation input, including the review host's typed changes. | Every invocation; stage artifacts are optional. |

A kind may be empty for a phase, but the frozen closure is never empty. Agent instructions, the
Protocol rule bundle and installed Skills are not context: instructions belong to the Agent
definition and are injected beside the context, and a Skill is the developer-facing projection of
a public Capability. The snapshot identity covers every admitted byte of every kind.

### Gap rule for bounded tasks

All task roles use the same necessary-contract gap rule. Explanation, planning, tasks and
implementation pause only dependent judgments when a required contract is missing or ambiguous;
independent reasoning may continue. Development gaps retain target, task, phase and Spec revision
until repair and a successful fresh assessment of that step. An explicit worker report may create an Issue without granting Spec/code write authority; context resolution itself remains read-only.

## Design

### Implementation status

Snapshots and discovery retain their independently versioned wire agreements, described in the
[context interfaces](contracts.md#context-context-snapshot-resolution). They freeze spec_resolution
and original source pools, preserve owner and inclusion provenance, and reject old membership
partitions. Both Protocol-8 document roles enter that same complete context; Implementation Specs
never become implementation-file grants. Native capsules and grants keep
referenced sources read-only; only owned entity listings grant implementation access. Rechecks
compare declarations and exact bytes, including reference changes with unchanged path sets.

## Precise specifications

The Harness Module owns the exact obligations and interface details in [contracts](contracts.md).
These companions are part of the same complete Module specification, not separate topic owners.
