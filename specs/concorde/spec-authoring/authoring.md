```concorde-document
{
  "id": "document.spec-authoring.authoring",
  "owner": "module.spec-authoring",
  "main_visible": true
}
```

# Spec authoring capability

## Usage & Contract

The [common invocation envelope](../development/interfaces.md#capability-execution-boundary),
[typed handoffs](../development/interfaces.md#stage-handoffs) and
[gap rules](../development/review-and-gaps.md) apply. Artifact references are host-issued paths
and exact digests; a valid shape alone does not establish currentness or authority.
This is a private, bound capability in the [current adapter inventory](../development/capabilities.md).
Only a declared in-process composition can call it; direct Skill/CLI invocation is rejected.
A caller supplies the selected Module, task, constraints, focus and current candidate identity
where required. It cannot reselect context or forge saved artifacts. Spec context is complete,
file names are visible and implementation contents remain excluded from non-code phases.

`specify` uses a fresh spec-engineer specify invocation with no inherited stage artifacts or
implementation contents. Inputs are the complete owned/direct-reference contract, task and
constraints under the pinned Protocol. It returns full owned document replacements in
concorde-agent-stage-result@1, or attributed gaps with no replacements. The host validates identity,
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

### Scenarios

#### scenario.spec-authoring.gap — Missing meaning prevents replacements

- GIVEN the selected Module's complete Spec lacks meaning necessary for the authoring task
- WHEN the fresh author cannot complete its owned replacements without inventing that meaning
- THEN it returns attributed gaps with no document replacements
- AND existing document bytes and unresolved blockers remain available for explicit repair

#### scenario.spec-authoring.foreign-output — A consumer cannot replace its provider's document

- GIVEN a selected Module references a document owned by another Module
- WHEN its author proposes a replacement for that foreign document
- THEN the host rejects the replacement rather than treating reference inclusion as ownership
- AND project document bytes and prior blockers remain unchanged

#### scenario.spec-authoring.stale-output — Changed inputs reject author output

- GIVEN an author prepared owned replacements from a frozen current context
- AND admitted source bytes, context or configuration change before acceptance
- WHEN the host rechecks those replacements
- THEN it rejects the stale or incompatible output without applying replacements
- AND previous document bytes and blockers remain available for a fresh authoring invocation

#### scenario.spec-authoring.invalid-output — Invalid metadata prevents application

- GIVEN a selected Module and its currently registered document identities and metadata
- WHEN ordinary authoring returns replacements with invalid identity or metadata
- THEN the host rejects the replacements without applying them
- AND successful assessment alone does not clear the previous authoring blockers
