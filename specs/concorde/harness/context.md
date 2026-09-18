# What information a worker receives

Context resolution makes a task's information boundary explicit before a worker starts. It gives
each phase enough admitted information for its job without silently inheriting everything a previous
worker, provider or developer session knew.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Spec context | The selected Module's complete owned and directly referenced specification units, including explanation, precise specifications and metadata. |
| Implementation context | The Module's bound implementation files; names are visible generally, but contents require a code-phase grant. |
| Resource context | The admitted operation/tool agreements and declared external reference material available to the phase. |
| Task context | The explicit task, constraints, admitted stage results and relevant lifecycle state for this invocation. |
| [Context](../module.md#terminology) | Defined in Concorde Framework. |
| [Worker](../module.md#terminology) | Defined in Concorde Framework. |
| [Module](../module.md#terminology) | Defined in Concorde Framework. |
| [Spec](../module.md#terminology) | Defined in Concorde Framework. |
| [Scenario](../module.md#terminology) | Defined in Concorde Framework. |
| [Host](../module.md#terminology) | Defined in Concorde Framework. |
| [Grant](../module.md#terminology) | Defined in Concorde Framework. |
| [Snapshot](../module.md#terminology) | Defined in Concorde Framework. |
| [Reference](../spec/registry.md#terminology) | Defined in Registry. |
| [Document role](../spec/values.md#terminology) | Defined in Identities and versions. |
| [Implementation Specs](../module.md#terminology) | Defined in Concorde Framework. |

## Context kinds

Each kind answers a different question: what the software promises, where it is realized, which
outside agreements or tools may be used, and what this job is trying to accomplish. Some kinds may
be empty for a phase. Instructions tell a worker how to behave; they are not another source of
project business facts.

For example, a planner sees the complete selected Spec and the names of implementation files, but
not their contents. A programmer later receives accepted tasks and its separately allowed code.
Selecting one scenario changes the question, not the rest of its owner's Spec context.

## Gap rule for bounded tasks

If the admitted context does not specify a necessary promise, report what is missing and which step
needs it. Do not fill the gap by following an undeclared link or reading implementation. Independent
work can continue, but the dependent judgment needs an explicit repair or selection decision.

## Design

The host records current sources and makes them available whole. It rechecks those inputs before
accepting a result, because a task planned against one revision may no longer be valid after an edit.
A provider reference supplies knowledge, not ownership or permission to alter its code. One-level
reference expansion keeps that boundary finite and understandable.

### Implementation status

Both document roles remain in complete Spec context; Implementation Specs never become code-file
grants. The runtime delivers an index plus readable files rather than embedding every document in
the request. Its exact snapshot fields, delivery rules and phase-specific subsets are specified in
[context interfaces](contracts.md#context-context-snapshot-resolution).

## Precise specifications

See the Module-owned [context-kind contract](contracts.md#context-kinds),
[requirements](requirements.md) and [scenarios](scenarios.md) for exact obligations and verification cases.
