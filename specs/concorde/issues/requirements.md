# Issues requirements

These precise specifications belong directly to the [Issues Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Issue](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Worker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Grant](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Disposition](lifecycle.md#terminology) | Defined in Solving a recorded problem. |
| [Ready](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Delivery](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Graph](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Issues

### req.issues.report-control — Reporting does not control execution

Accepting an Issue report SHALL NOT itself stop a worker, start repair or change task completion.

### req.issues.scope — Issue routing preserves authority

Selecting or reporting an Issue SHALL NOT widen the selected worker's Spec, implementation or command grant.

### req.issues.retention — Closing preserves observations

Issue disposition SHALL preserve the record and every original observation.

### req.issues.ready-boundary — Solving stops before delivery

A successful solving graph SHALL stop at ready without delivery or primary merge.
