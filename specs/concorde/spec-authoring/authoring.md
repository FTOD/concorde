# Revising the intended contract

Spec authoring changes the description of intended behavior and design, not the implementation.
A composing workflow supplies one owning Module and a task; the author proposes changes that the
host checks before writing project files.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Contract](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## A normal revision

The author reads the complete allowed specification, identifies what the requested change means,
and returns complete replacements for the affected owned documents. It explains normal use and
important guarantees in Module Specs, defines exact obligations in Implementation Specs, and keeps
Terminology definitions canonical. Unknown intended behavior is reported as a gap rather than inferred
from source code.

For example, a consumer can rely on a provider's documented reservation result, but cannot replace
the provider's contract while editing its own Spec. A shared contract change is authored by its owner
and checked against affected consumers in their separate contexts.

## Why proposal and application are separate

The model can propose meaning without receiving a general filesystem write grant. The host checks
ownership, source freshness and the complete replacement set before applying it. Invalid or stale
output preserves prior bytes. Ordinary revisions keep document identity and ownership; structural
changes use Topology so registrations and references change together.

The author does not independently approve its own work. The calling flow chooses review and any
later planning. Exact proposal and acceptance rules are in the execution reference.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#authoring-spec-authoring-capability).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
