# Recording and following problems

Use an Issue to retain a concrete problem beyond the current conversation. The record contains what
was observed, why it matters, its evidence and the responsible Module when known. Reporting a problem
does not itself stop a task, change code or authorize a repair.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Issue](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Disposition](lifecycle.md#terminology) | Defined in Solving a recorded problem. |
| [Module](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Reporting and reading

A developer can report a problem explicitly; a worker can report observations within its allowed
scope while continuing useful work. An Issue can describe a defect, a missing or conflicting promise,
or a limitation of otherwise consistent behavior. New observations can refine the classification
without erasing the original report.

For example, discovering that a retry policy is unspecified is a contract gap. Discovering an
unrelated usability limitation need not block the current change. The task's blocker decision is
separate from retaining either observation.

## Appending rather than rewriting history

Follow-up evidence is appended to the current record. Repeating the same acknowledged report does
not create another observation, while changed input must not overwrite the first one. Concurrent
updates are checked against the latest record so one reporter cannot silently discard another's work.
Accepted reports survive a later worker failure.

## Closing and reopening

Closing requires a reason supported by current evidence, such as a verified resolution, a genuine
duplicate or a contract-grounded non-actionable judgment. A workaround or one failed reproduction is
not automatically a fix. Closed records remain readable with their observations; reopening records
why the problem needs attention again.

Issues are versioned with their branch. Closing one in a candidate does not mean the primary branch
has changed. The [solving lifecycle](lifecycle.md) explains verification and final completion. Exact
storage, reporting-tool, concurrency and disposition interfaces remain in Implementation Specs.

## Precise specifications

See the Module-owned [execution and record contracts](execution-reference.md#issues-issue-records-and-reporting).
The exact obligations remain in Implementation Specs; this topic explains their purpose and use.
