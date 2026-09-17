# Preparing a specification before coding

Specification Flow routes a Spec-writing task, obtains owned revisions and independent review, then
stops before planning or implementation. Use it when the contract needs discussion before code work.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Normal progress

The developer supplies intended behavior and constraints. Routing selects the responsible Module;
a fresh author proposes its owned changes; the host checks them and obtains required owner/consumer
reviews. The result contains accepted Spec-stage artifacts or an explicit reason it could not finish.

For example, clarifying which failures allow a retry can be completed here without also writing the
retry mechanism. [Development Flow](../dev-loop/module.md) may later continue the same task and change using current accepted
Spec work, rather than starting a second unrelated authoring attempt.

## Limits and reuse

Completion means Spec preparation succeeded, not that code exists or a candidate is ready. A failed
or blocking review stops for a decision; this flow has no automatic Spec-repair loop. Disabling
authoring or review records that choice where permitted, but cannot cancel a previously required
review or supply missing meaning.

Reuse requires the same intent and unchanged relevant inputs. A standalone review of another task
cannot substitute for accepted authoring. Fresh invocations preserve independence even when the host
reuses current evidence. Exact state, reuse gates and executable transitions are in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#specify-loop-specification-flow).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
