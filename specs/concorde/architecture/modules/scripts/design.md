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
- `implementation_acceptance.py` atomically promotes an approved completed attempt.
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
