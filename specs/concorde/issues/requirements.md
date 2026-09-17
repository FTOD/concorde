# Issues requirements

These precise specifications belong directly to the [Issues Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Issue](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Issues

### req.issues.report-control — Reporting does not control execution

Accepting an Issue report SHALL NOT itself stop a worker, start repair or change task completion.

### req.issues.scope — Issue routing preserves authority

Selecting or reporting an Issue SHALL NOT widen the selected worker's Spec, implementation or command grant.

### req.issues.retention — Closing preserves observations

Issue disposition SHALL preserve the record and every original observation.

### req.issues.ready-boundary — Solving stops before delivery

A successful solving flow SHALL stop at ready without delivery or primary merge.
