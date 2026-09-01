# Design Reference: Scripts

## Implementation Notes

The runtime path is `launcher → Python adapter → concorde.cli → operation module → repository files`.
`workspace.py` is the smaller adapter used by normal phase skills. The runtime is standard-library
Python 3.11+ and returns one structured result envelope for success, proposals, and findings.

Operations are split by behavior rather than by user command syntax:

- `initialize.py` produces digest-bound root proposals and applies only an explicitly accepted file set.
- `context.py` projects exactly one bounded architectural level.
- `validate.py` and `validation/` produce deterministic findings without source mutation.
- `feature_workspace.py` resolves nested durable and temporal paths.
- `delivery.py` atomically promotes an approved completed attempt.
- `reflections.py` parses and summarizes the durable project reflection log.

## Design Rationale

The runtime is subordinate to Skills and stateless outside the repository. Keeping file semantics in
Workspace Files prevents parsing code from becoming a second specification of what a file means.

## Alternatives Considered

- Name the module Runtime: rejected because the host coding agent is also a runtime; Scripts is the
  repository term users can locate directly.
- Split every CLI operation into a module: rejected because they share the same safety, result, and
  repository boundary.

## Decision Log

- Replaced the ambiguous Scripts label with Scripts.
- Made Workspace Files an explicit required boundary.

## Terminology

| Term | Meaning | Relationships |
|---|---|---|
| `Runtime operation` | One deterministic Scripts behavior selected by the CLI and implemented against repository files. | `returns` → `Structured result`; `operates on` → `Workspace Files` |
| `Workspace resolver` | The bounded operation that verifies a selected feature and derives its canonical durable and temporal paths. | `is a` → `Runtime operation`; `returns` → `Structured result` |
| `Structured result` | A versioned status envelope containing artifacts, findings, and operation-specific data. | `contains` → `Validation finding` |
| `Validation finding` | A deterministic rule result with severity, source, explanation, and remediation. | `returned in` → `Structured result` |
| `Mutation proposal` | A digest-bound description of an allowed file change that grants no authority until explicitly approved. | `applied by` → `Runtime operation`; `targets` → `Durable artifact` |
