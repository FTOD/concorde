# Finding the responsibility behind a request

Query and Routing connects a developer's question or intended change to the Module whose contract
can answer it. Hints help selection; they are not permission to read arbitrary documents or code.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Context](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Asking a question

Discovery starts from explicitly selected complete Module Specs. It can request another Module when
needed, and the host checks that selection before making its documents available. The answerer uses
the admitted originals rather than summaries made by earlier readers. Missing meaning is reported
with its owner when known; discovery does not inspect implementation to invent a promise.

For example, a checkout question may require Inventory's reservation contract. The selection must
include that knowledge explicitly. Inventory's own unrelated references do not recursively enter
the reader's context merely because Inventory was selected.

## Routing a change

Routing returns an owning Module while preserving the original task and constraints. The consuming
workflow then gives a fresh worker that Module's bounded job. A route is not implementation
completion or a grant to change the provider's files. A saved candidate with a bound owner resumes
that identity rather than silently rerouting to another Module.

## Why discovery is bounded

Repeated expansion might still fail to find a required promise. Explicit limits make that an honest
stopping result, not an invitation to keep reading indefinitely. The exact discovery and query Flows
are maintained once in the Module's execution reference.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#query-and-routing-query-and-routing-agent-flow).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
