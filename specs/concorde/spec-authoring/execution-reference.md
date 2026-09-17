# Spec Authoring execution and record contracts

These are the precise implementation agreements and executable Flow specifications owned by the
[Spec Authoring Module](module.md). Explanatory topics introduce their purposes; exact identities, limits
and transitions are retained here as the single detailed contract.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Contract](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Spec authoring capability {#authoring-spec-authoring-capability}

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/execution-reference.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound capability in the [current adapter inventory](../development/execution-reference.md).
Only a declared in-process composition can call it; direct Skill/CLI invocation is rejected.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`specify` uses a fresh spec-engineer specify invocation with no inherited stage artifacts or
implementation contents. Inputs are the complete owned/direct-reference contract, task and
constraints under the pinned Protocol. It returns full owned document replacements in
concorde-agent-stage-result@2, or attributed gaps with no replacements. The host validates identity,
metadata, allowed paths, context and configuration before applying accepted replacements; the author
never writes project files. The capability response retains references to accepted output.

A referencing author cannot replace a provider document. An owner may revise its own shared
document, but application requires affected-consumer compatibility checks in their separate
contexts. Ordinary authoring preserves document ID, owner, visibility and registered membership;
changes to those definitions require explicit topology reconciliation. An invalid, foreign or stale
replacement is rejected with existing bytes and blockers preserved. Successful assessment resolves
old authoring gaps only after the host accepts the output, not merely after a model says sufficient.

Repeated calls re-admit current inputs; accepted-authoring reuse and independent review selection
are the composing flow's decisions. This capability alone neither reviews its own output nor plans,
implements or marks a candidate ready. Topology's special candidate-author context is a distinct
existing mode, not an undeclared call to this ordinary specify adapter.

### Precise specifications {#authoring-precise-specifications}

The Spec Authoring Module owns the exact obligations and interface details in [scenarios](scenarios.md).
These companions are part of the same complete Module specification, not separate topic owners.

## Realization and reuse limits

This Module and its consumers are siblings under Concorde Framework. Declared files explicitly
share the existing adapter realization with Development; no new runtime package, public Skill,
Agent grant or configurable arbitrary flow is created by this Spec boundary. Host admission,
phase artifacts and permissions remain mandatory. A new flow requires declared composition and
an implementation of its sequencing, artifact admission, recovery and completion policies before
it can execute. The existing host package still realizes common dispatch and provider internals.
