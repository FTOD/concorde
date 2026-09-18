# How the host coordinates a request

The Development host checks a request, selects its operation and workspace, then lets the chosen
provider or workflow do its job. It records accepted results so later work can distinguish completion
from a blocked or failed attempt.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Operation](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Normal request path

A public request enters one common boundary. The host checks its operation and configuration,
establishes the current workspace, and selects or restores the responsible Module. It then dispatches
the admitted operation and records its result. Invalid requests stop before workers run.

For example, a request to review code and a request to develop a change share admission checks, but
have different completion conditions. Review returns findings; it does not create a development
candidate merely because both operations use the same host.

## Coordinating several Modules

A shared change can require work from several owners. Each receives its own contract and permissions.
The host waits for all writers before final checks, because checking one consumer while another is
still changing shared code would give misleading evidence. A later repair may invalidate an earlier
consumer's result, so readiness waits for a stable, consistently checked revision.

## Reading the diagrams

The exact operation, dispatch, target, project, coordination and stabilization Graphs are maintained
once in the Module's execution reference. They are checked against the compiled runtime and are the
source for Studio inspection. This page explains their purpose; it does not define a second execution
graph. Domain workflows still own their own sequencing and stopping policies.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#graphs-development-host-graphs).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
