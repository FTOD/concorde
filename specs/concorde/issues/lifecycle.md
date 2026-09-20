# Solving a recorded problem

An explicit solve request selects one Issue and its current evidence. The solver returns needed implementation or Spec edits to the calling agent and uses independent
review for verification; it never gains wider repair permissions.

## Terminology

| Term                                  | Meaning / definition                                                                                           |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Disposition                           | An evidence-grounded recorded decision to resolve, mark duplicate, close as not actionable or reopen an Issue. |
| [Issue](../module.md#terminology)     | Defined in Concorde Framework.                                                                                 |
| [Candidate](../module.md#terminology) | Defined in Concorde Framework.                                                                                 |
| [Ready](../module.md#terminology)     | Defined in Concorde Framework.                                                                                 |
| [Evidence](../module.md#terminology)  | Defined in Concorde Framework.                                                                                 |
| [Host](../module.md#terminology)      | Defined in Concorde Framework.                                                                                 |
| [Spec](../module.md#terminology)      | Defined in Concorde Framework.                                                                                 |
| [Graph](../module.md#terminology)     | Defined in Concorde Framework.                                                                                 |

## Normal progress

The solver first determines what the problem needs. Clear implementation intent or a missing promise
returns to the calling agent with its selected target, intended behavior and rationale. The caller
edits Specs, paired metadata and registry directly or selects the retained planning/implementation
Operations explicitly. A claim with a potential resolution goes to Issue-specific verification
through the [Review Module](../review/module.md). An unsettled product or design choice returns to
the developer instead of being invented. There is no mandatory triage ritual before every repair.

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
Exact recovery records, limits and executable Graphs are in the Module's execution reference.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#lifecycle-issue-solving-lifecycle).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
