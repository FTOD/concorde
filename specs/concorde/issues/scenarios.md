# Issues scenarios

Concrete situations that show the [requirements](requirements.md) at work. Shapes and error codes
are defined in the [Issue interface](interface.md).

## Reporting

### scenario.issues.report-independent — Report without ending the task

- GIVEN a worker whose run has the `report_issue` tool
- WHEN it reports one or more problems and then submits its result
- THEN each report is saved and acknowledged while the worker keeps running
- AND the worker's task completes with its own outcome
- BUT the reports neither stop the worker nor start a repair

### scenario.issues.report-authority — Report only within the worker's context

- GIVEN a worker whose frozen context admits some Modules and files
- WHEN it reports a problem naming an admitted owner and admitted evidence
- THEN the Host saves the report with Host-supplied provenance
- AND the worker still has no write access to project files
- BUT a report naming an owner or evidence outside the context, forged provenance, or an append to an Issue not selected for the run is refused
- AND a policy preview that runs no worker creates no reporting service and no Issue

### scenario.issues.report-survives-failure — Keep reports from a failed run

- GIVEN a worker whose report the Host has acknowledged
- WHEN the worker later submits an invalid result, fails, times out or is cancelled
- THEN the report stays saved
- AND the failed run is still reported as failed, not as successful

### scenario.issues.reference — Reference only reported or admitted reports

- GIVEN a worker that reported some problems and may have received admitted Issue reports as input
- WHEN it submits Blockers or review Findings that reference Issue reports
- THEN each reference must name a report the worker made in this run or received as input
- AND a missing, foreign, fabricated or repeated reference fails the result
- BUT the reports already saved are kept

### scenario.issues.blocker-history — Track a Blocker independently of task wording

- GIVEN a candidate in which an Issue report blocks one Module's phase
- WHEN the work is replanned with different task wording and a fresh successful assessment of that phase releases the dependency
- THEN the Blocker stays in the candidate's history keyed by change, Module, phase and Issue
- AND the Issue itself stays open until a separate disposition closes it
- AND a worker bound to another Module does not see that Blocker

## Records

### scenario.issues.store-report — Save a report once

- GIVEN a Host-issued provenance and a classified report
- WHEN the Host saves it and then saves the identical report again
- THEN exactly one Issue with one report exists and both calls return the same receipt
- AND a later append with the current revision may classify the problem differently without changing the first report
- AND listing a project without an Issue directory returns nothing and creates nothing

### scenario.issues.store-concurrency — Serialize writes without coupling branches

- GIVEN concurrent reports in one worktree and a second worktree with its own copy of the records
- WHEN the Host accepts the reports and closes an Issue in one worktree
- THEN no accepted report is lost or duplicated
- AND the other worktree keeps its own status for that Issue until the branches are integrated

### scenario.issues.store-disposition — Close and reopen with evidence

- GIVEN an open Issue and its current revision
- WHEN an authorized Host call supplies a disposition with a note, evidence and actor
- THEN the Issue gets the disposition and keeps every report unchanged
- BUT a stale revision, empty evidence, a duplicate of itself, a closed duplicate target or an invalid transition is refused

### scenario.issues.store-boundary — Refuse malformed or unsafe records

- GIVEN a malformed report, an unsafe path, a corrupted report digest or a failed file publication
- WHEN the Host tries to accept or save it
- THEN it does not report success
- AND existing valid records stay readable and unchanged

## The capability

### scenario.issues.inspect — Inspect without starting work

- GIVEN an initialized project with or without Issues
- WHEN the user session calls `concorde-issues` with `list` or `show`
- THEN the current records are returned
- BUT no model runs, no candidate is created and no record changes

## Solving

### scenario.issues.solve-handoff — Carry an uncommitted Issue into the candidate

- GIVEN an open Issue whose report is not yet committed in the primary worktree
- WHEN the user session requests `solve` from the primary worktree
- THEN the Host copies exactly the selected Issue's bytes into the new candidate before relaying the request there
- AND other local edits and the primary worktree's index are left alone

### scenario.issues.solve-spec-repair — Hand needed changes back

- GIVEN a solve whose solver decides `develop` or `spec-repair`
- WHEN the Host admits the decision
- THEN the solve stops with outcome `unsupported`, naming the Module, the intended change and the reason
- AND the Issue stays open and the decision is kept in the solve history
- BUT no worker writes code or Specs and nothing is changed
- AND after the user session makes the change, a new solve can verify it on the current inputs

### scenario.issues.solve-decision — Ask only when a choice is genuinely open

- GIVEN a selected Issue whose fix needs a product or design choice that its context does not settle
- WHEN the solver decides `needs-decision`
- THEN the solve stops with the precise question and the Issue stays open
- AND a later solve with a `note` carrying the developer's answer starts a fresh bounded attempt

### scenario.issues.solve-ready — Close, validate and stop at ready

- GIVEN a selected open Issue that the user session has already fixed
- WHEN fresh Issue-specific and ordinary reviews pass and the solver decides `resolved`
- THEN the Host writes the disposition and final validation checks the candidate including it
- AND the result is a ready candidate
- BUT nothing is delivered or merged, and repeating solve does not run the workflow again

### scenario.issues.solve-stale — Refuse changed inputs

- GIVEN a solve in progress
- WHEN the selected Issue's bytes, the offered duplicate, or the Module's Specs or implementation files change before a dependent step
- THEN that step is refused as stale and earlier work is kept
- AND a failed final validation leaves the Issue open, not closed

### scenario.issues.native-solve — Only Host steps close an Issue

- GIVEN one selected Issue in its candidate and the native solve workflow
- WHEN the workflow runs solver and reviewer calls between its Host steps
- THEN each solver attempt is saved before the model starts, and only results correlated with an actual finished native child are admitted
- AND `develop`, `spec-repair` and `needs-decision` return to the user session without changes
- AND `resolved`, `duplicate` and `not-actionable` close the Issue only through the journal and final validation
- AND failed validation restores the Issue, and a stopped, failed, stale or duplicated step cannot close it
- AND a verification with many reviewers runs them all in the same workflow without extra Host permissions

## Recovery

### scenario.issues.disposition-recovery — Recover an interrupted close

- GIVEN a solve that saved its closing journal
- WHEN the process fails before the disposition is written, after it is written, or before completion is saved
- THEN the next solve in the same candidate first invalidates any earlier ready result
- AND restores exactly the journal's open bytes, or does nothing if they are already on disk
- AND continues with a fresh solve and fresh validation
- BUT a failure before the journal was saved leaves the Issue open with nothing to restore
- AND nothing is delivered automatically

### scenario.issues.disposition-recovery-stale — Refuse recovery that cannot be proven

- GIVEN an interrupted solver close
- WHEN the next solve finds Issue bytes that match neither journal image, a corrupt journal, or a solver close without any journal
- THEN it refuses to recover and does not overwrite the record
- AND no solver is launched
