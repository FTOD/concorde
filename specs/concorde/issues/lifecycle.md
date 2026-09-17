# Solving a recorded problem

An explicit solve request selects one Issue and its current evidence. The solver uses the ordinary
specification, development and review capabilities rather than a separate repair system with wider
permissions.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| Disposition | An evidence-grounded recorded decision to resolve, mark duplicate, close as not actionable or reopen an Issue. |
| [Issue](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Host](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Spec](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Flow](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Normal progress

The solver first determines what the problem needs. Clear implementation intent can go to
[Development Flow](../dev-loop/module.md); a missing promise goes to
[Spec Authoring](../spec-authoring/module.md); a claim that already has a potential resolution goes to
Issue-specific verification through the [Review Module](../review/module.md). If an actual product or design choice is unsettled, it asks the developer
instead of inventing that choice. There is no mandatory triage ritual before every repair.

For example, a clearly specified incorrect result can be fixed and checked directly. If the expected
result is not specified, writing code first would conceal the gap rather than resolve it.

## What completion means

A proposed resolution receives fresh, independent Issue-specific review and the candidate's ordinary
required checks. The recorded disposition is included in final validation. Success leaves a ready
candidate, not a merge into primary. A supported disposition can be autonomous; unsettled intent
still requires a developer decision.

## Why closing is recoverable

A process can fail between recording closure and saving final completion. The host records enough
information to recognize its own pending write, invalidate old readiness and safely reassess on retry.
It does not overwrite a concurrent developer edit or guess that an already-closed record completed
this attempt. Failed work remains inspectable, and retries are bounded rather than endless.
Exact recovery records, limits and executable Flows are in the Module's execution reference.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#lifecycle-issue-solving-lifecycle).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
