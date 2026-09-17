# Fulfilling accepted tasks

Implementation changes code to satisfy an accepted plan and task list. It reports fulfillment of
those tasks; it does not decide that the whole candidate is ready or change the Spec to match its code.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Normal implementation

The workflow supplies current tasks for one Module. A fresh programmer receives its complete Spec
and the implementation files it may read or change. It implements and tests within that grant, then
returns the same task identities and acceptance conditions, marking only fulfilled tasks complete.
Missing tasks stop before work starts; omitted or incomplete results cannot establish full completion.

For example, a test may import a fixture outside the programmer's allowed files. That import does
not grant access. The programmer records why execution must be deferred to a host-level check and
continues independent work. Deferred execution is not a passing test, while an actual defect still
prevents task completion. Final host checks remain required.

## Failure and coordination

Code edits made before a failed or cancelled run can remain in the candidate. Inspect that progress
and restart with current inputs rather than assuming rollback. A change spanning several Modules
needs separate contracts and grants; the enclosing development workflow coordinates them and waits
for every writer before final checks. This prevents a partly changed shared file from producing
misleading consumer evidence.

Implementation is an internal provider used by declared workflows. Exact inputs, completion records
and coordination restrictions are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#implementation-implementation-capability).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
