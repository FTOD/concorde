```concorde-document
{
  "id": "document.reflections.lifecycle",
  "targets": [
    "module.reflections"
  ],
  "main_visible": true
}
```

# Reflection investigation, implementation and disposition

A Reflection retains a problem, its observed effects, evidence, investigation and developer
comments. Investigation runs as read-only implementation with selected record bytes and HEAD; it
receives the selected Module's Spec context and the exact files its entities list, and no write
permission for those files. Code-writing tasks separately receive write permission for the same
entity-listed files. The independent Spec Protocol standard is outside the registered Module
ownership available to a reflection investigation; a result that requires changing that standard
cannot be applied through this Module-bound investigation.

## Investigation

### scenario.reflections.investigate-reproduces — Investigation binds evidence and writes a plan

- GIVEN an existing Reflection report and the project's current HEAD
- WHEN investigate is invoked for that report
- THEN the host binds the exact selected record bytes and HEAD before reading them
- AND it preserves the original report and human comments
- AND it writes findings, a reproduction verdict, a route, an effort estimate and an evidence-bound resolution as a plan under the configured `plans_dir`
- AND the record moves into the bucket matching its completed triage sections in one deterministic action

- req.reflections.bucket-triage-agreement: A record whose triage sections contradict its bucket, or that lies outside every bucket, SHALL be rejected.
- req.reflections.non-reproduced-disposition: A non-reproduced investigation outcome SHALL recommend dismissal and require human intervention.
- req.reflections.fast-loop-effort: A fast-loop route SHALL only be recommended together with small effort.
- req.reflections.no-heading-injection: An investigation section value SHALL NOT inject a document-level Markdown heading.
- req.reflections.investigation-file-boundary: Investigation SHALL read only the files listed by the selected Module's own entities.

### scenario.reflections.investigate-stale-evidence — Stale evidence blocks investigation

- GIVEN a report whose selected record bytes or HEAD have changed since selection
- WHEN investigate is invoked
- THEN the call is rejected as stale
- AND the report and its existing progress remain available for a later attempt

A Module with no entity file listings is an unsupported code-investigation target. If a Module's
ownership of the needed code is unclear, a separately bound context-solving task can identify the
missing facts before investigation is retried.

## Implementation

### scenario.reflections.implement-approved-plan — Implementation composes a fresh development task

- GIVEN a reproduced investigation, no outstanding human intervention and an approved route or plan
- WHEN implement is invoked
- THEN the host composes a fresh concorde-dev-loop using only the approved intended behavior
- AND investigation text, code and logs are excluded from its Spec-stage inputs
- AND a successful result marks the plan implemented while leaving the report's human disposition independent

### scenario.reflections.implement-requires-current-approval — A changed resolution needs fresh approval

- GIVEN configuration requires approval and the resolution is new or has changed since it was last approved
- WHEN implement is invoked without a fresh approval
- THEN the call is rejected
- AND the previous approval is not reused for the changed resolution

## Disposition and merge

### scenario.reflections.close-sets-disposition — An explicit human decision resolves or dismisses a report

- GIVEN a report with investigation findings recorded
- WHEN a developer invokes close with an explicit disposition and a `resolution_note`
- THEN the record's status becomes resolved or dismissed as decided
- AND the original observation and user comments remain preserved

### scenario.reflections.close-rejects-mere-nonreproduction — Non-reproduction alone does not close a report

- GIVEN an investigation that reports a problem as not reproduced
- WHEN no explicit human disposition has been given
- THEN the report remains open

### scenario.reflections.merge-after-checks — Merge removes disposed records after existing Git checks

- GIVEN resolved or dismissed records with a `resolution_note`
- AND the existing Git merge checks for the change pass
- WHEN merge is invoked
- THEN the deterministic removal deletes the records from their bucket
- AND Git history continues to preserve their content
- BUT the action performs no Git merge itself

Reflection record selection, status, investigation coordination, approval and disposition remain on
`module.reflections`; this Module has no separately registered child Module. When an approved
resolution becomes ordinary product work, its typed route selects the responsible target named by
the Reflection.
