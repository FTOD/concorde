# Spec Authoring execution and record contracts

These are the precise implementation agreements and executable Graph specifications owned by the
[Spec Authoring Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Blocker](../module.md#terminology) | Defined in Concorde Framework. |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework. |
| [Ready](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec context](../harness/context.md#terminology) | Defined in What information a worker receives. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Ownership](../spec/registry.md#terminology) | Defined in Registry. |
| [Graph](../module.md#terminology) | Defined in Concorde Framework. |
| [Internal operation](../development/module.md#terminology) | Defined in Development operation host. |
| [Skill](../module.md#terminology) | Defined in Concorde Framework. |

## Spec authoring operation {#authoring-spec-authoring-operation}

The [Development Module](../development/module.md) owns admission. Its [common invocation envelope](../development/interfaces.md#operation-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/execution-reference.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound operation in the [current adapter inventory](../development/execution-reference.md).
Only a declared in-process composition can call it; direct Skill/CLI invocation is rejected.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`specify` invokes the spec-author Operation in a fresh worker with no inherited stage artifacts or
implementation contents. Inputs are the complete owned/direct-reference contract, task and
constraints under the pinned Protocol. It returns full owned document replacements in
concorde-agent-stage-result@2, or attributed gaps with no replacements. The host validates identity,
metadata, allowed paths, context and configuration before applying accepted replacements; the author
never writes project files. The operation response retains references to accepted output.

A referencing author cannot replace a provider document. An owner may revise its own shared
document, but application requires affected-consumer compatibility checks in their separate
contexts. Ordinary authoring preserves document ID, owner, visibility and registered membership;
changes to those definitions require explicit topology reconciliation. An invalid, foreign or stale
replacement is rejected with existing bytes and blockers preserved. Successful assessment resolves
old authoring gaps only after the host accepts the output, not merely after a model says sufficient.

Repeated calls re-admit current inputs; accepted-authoring reuse and independent review selection
are the composing graph's decisions. This operation alone neither reviews its own output nor plans,
implements or marks a candidate ready. The [Topology Module](../topology/module.md)'s special candidate-author context is a distinct
existing mode, not an undeclared call to this ordinary specify adapter.

### Precise specifications {#authoring-precise-specifications}

The Spec Authoring Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary graph is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new graph requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
