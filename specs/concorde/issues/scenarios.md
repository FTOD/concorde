# Issues scenarios

These precise specifications belong directly to the [Issues Module](module.md).
Subject headings organize the Module's obligations; they do not create separate owners or contexts.

## Terminology

| Term | Meaning / definition |
| --- | --- |
| [Issue](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Blocker](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Candidate](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |
| [Evidence](../concepts.md#terminology) | Defined in Concepts for reading Concorde. |

## Issue interface

### scenario.issues.inspect — Inspect without starting work

- GIVEN an initialized project, with or without Issue records
- WHEN list or show is requested
- THEN the current records are returned without a model invocation, candidate creation or issue mutation

### scenario.issues.reference — Admit only observed or granted Issue references

- GIVEN a bounded worker with reporting authority and optional admitted repair feedback
- WHEN it submits task blockers or review judgments
- THEN every reference resolves to an observation it reported or was explicitly granted
- AND missing, foreign and fabricated references fail admission without removing saved reports

### scenario.issues.blocker-history — Track dependencies without task-text identity

- GIVEN a candidate with an Issue blocking a Module phase
- WHEN the same work is replanned and a fresh successful assessment releases that dependency
- THEN its stable Issue relation remains in history without depending on old task wording
- AND the Issue itself remains open unless separately disposed with evidence
- AND another Module's blocker is absent from the worker's bounded workspace context

### scenario.issues.archive — Preserve legacy history explicitly

- GIVEN legacy Reflection data and no archive destination
- WHEN the developer explicitly requests archival
- THEN the complete directory is moved without altering its records or relative evidence links
- AND no active Issue is created or marked resolved
- AND conflicting destinations and symlinks are refused without discarding data

## Issue solving lifecycle

### scenario.issues.solve-ready — Resolve and verify the candidate

- GIVEN an explicitly selected open Issue with current evidence
- WHEN bounded development and Issue-specific verification succeed
- THEN the authorized solver can resolve the Issue and final checks bind the disposition bytes
- AND the result is a ready candidate without automatic delivery or primary merge

### scenario.issues.solve-spec-repair — Route contract repair to the ordinary author

- GIVEN an admitted solver decision with action spec-repair
- WHEN the flow selects the next operation
- THEN it enters the declared repair_spec node and invokes the owner-only Spec author
- AND the author receives intended behavior without the solver's selection or prior transcript
- AND accepted repair can continue to development or, for a code-free Module, Spec-only verification

### scenario.issues.solve-decision — Ask only for genuinely unsettled decisions

- GIVEN a selected Issue whose required product or design choice cannot be determined from its context
- WHEN the solver returns needs-decision
- THEN the Issue remains open and the precise question is returned without inventing a fix
- AND an explicit solve note supplies developer clarification and permits a fresh bounded attempt

### scenario.issues.solve-stale — Refuse changed selections and retain failed work

- GIVEN selected Issue bytes or verification inputs that change during solving
- WHEN a dependent solve or disposition step is attempted
- THEN stale evidence is rejected and unrelated work is preserved
- AND failed final candidate verification cannot leave the runtime's unchanged disposition presented as completed

### scenario.issues.disposition-recovery — Recover an interrupted closing transaction

- GIVEN a selected Issue whose disposition is about to be published
- WHEN execution or persistence fails before publication, after publication or before the completed checkpoint
- THEN a journal is durable before any closing write and an unjournaled failed preparation leaves the Issue open
- AND retry first invalidates old readiness and restores only the exact journaled write before fresh solving and validation
- AND a rollback whose acknowledgement is lost can be retried without another restoration write
- AND the original selected request can resume across its own journaled revision without automatic delivery

### scenario.issues.disposition-recovery-stale — Refuse unprovable restoration

- GIVEN an interrupted solver disposition
- WHEN a retry finds changed Issue bytes, a corrupt journal or a legacy unfinished close without a journal
- THEN it rejects recovery without overwriting the record or treating it as an ordinary completed close
- AND no solver worker is launched before those checks succeed

### scenario.issues.solve-handoff — Carry an uncommitted selected report

- GIVEN an open report not yet present in the committed base
- WHEN the host prepares a candidate for its explicit solve request
- THEN that record's exact selected bytes are copied to the candidate before the session handoff
- AND unrelated local edits and the source worktree's index are preserved

## Issue records and reporting

### scenario.issues.report-authority — Bind reporting without granting arbitrary writes

- GIVEN a worker with a frozen context and host reporting service
- WHEN it reports an admitted observation or attempts foreign evidence, ownership or provenance
- THEN the host saves the admitted observation without granting the worker project writes
- AND foreign evidence, forged provenance and appends to unselected issues are rejected
- AND policy preview launches no reporting service and creates no issue

### scenario.issues.report-independent — Report without ending the task

- GIVEN a worker or question-answering invocation with reporting authority
- WHEN it reports issues and then completes its own task
- THEN the reports remain available and the task can complete successfully
- AND the reporting tool itself neither terminates the worker nor starts a repair

### scenario.issues.report-survives-failure — Retain observations from interrupted work

- GIVEN a worker whose issue report was acknowledged by the host
- WHEN its final result is invalid or its execution is interrupted
- THEN the issue observation remains persisted independently of the failed stage
- AND the failed or incomplete stage is not represented as successful

### scenario.issues.store-report — Persist and reference classified observations

- GIVEN a host-issued reporting context and a classified issue report
- WHEN the host records it and retries the identical report
- THEN one branch-local issue and one immutable observation exist with the same returned receipt
- AND appending current evidence can revise the classification without changing the original report
- AND querying an absent collection creates no record or directory

### scenario.issues.store-concurrency — Serialize writes without coupling branches

- GIVEN concurrent reports in one worktree and an independent branch copy
- WHEN the host accepts reports and disposes a record in one branch
- THEN accepted observations are not lost or duplicated by identical retries
- AND another branch's copy retains its own disposition until explicit integration

### scenario.issues.store-disposition — Retain evidence-bound disposition history

- GIVEN an open issue with its current byte revision
- WHEN an authorized host supplies a valid disposition with rationale and evidence
- THEN the record is retained with the requested disposition and unchanged original observations
- AND stale revisions, empty evidence, self-duplicates and invalid transitions are rejected

### scenario.issues.store-boundary — Reject malformed and unsafe persistence

- GIVEN a malformed report, unsafe path, corrupted observation or failed publication
- WHEN the host attempts to admit or persist it
- THEN it does not acknowledge successful recording of that invalid operation
- AND existing valid observations remain available without widening file authority
